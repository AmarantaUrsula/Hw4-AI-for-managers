"""Shop chatbot agent: entry point and wiring (Problem 5).

How the agent is loaded
- System prompt: read from prompts/prompt.md (edit that file to change voice/safety).
- Model: PORTKEY_MODEL (gpt-6-luna) through Portkey, using PORTKEY_API_KEY. Both are read
  from hw4/.env (copy .env.example), then backend/.env, then the parent folder's .env.
  There is no fallback model.
- Tools: tools.SHOP_TOOLS (read-only catalogue + inventory).
- Output: models.ChatReply, checked by three output guards before it is sent:
  page_needs_search (show_on_page needs a search), no_private_data (safety rules 6-8),
  and no_invented_numbers (every $ price / stock count must come from a tool this message).
  A failing guard sends the model a ModelRetry; after OUTPUT_RETRIES it stops.
- Every run is recorded step by step in the append-only output/audit_trail.json (audit.py).
"""

import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext, UsageLimits
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from audit import RunAudit
from models import ChatReply, ChatTurn, ShopDeps
from tools import SHOP_TOOLS

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_FILE = BACKEND_DIR / "prompts" / "prompt.md"

# Settings come from .env files (never committed; see .env.example). First found wins per variable:
load_dotenv(BACKEND_DIR.parent / ".env")         # hw4/.env  (copy of .env.example: key + model)
load_dotenv(BACKEND_DIR / ".env")                # backend/.env (optional local overrides)
load_dotenv(BACKEND_DIR.parent.parent / ".env")  # course folder .env (the author's local setup)

MAX_HISTORY_TURNS = 10      # previous messages replayed to the model
MAX_REQUESTS_PER_MESSAGE = 8  # model calls (incl. tool rounds) allowed per shopper message
MAX_OUTPUT_TOKENS = 1200      # per model call
OUTPUT_RETRIES = 2            # how many times a rejected reply (output guards) may be redone


# "$68", "$68.00", "$ 1,200.50"
PRICE_RE = re.compile(r"\$\s?(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?)")
# "5 left", "12 in stock", "only 3", "25 available", "8 units", "in stock (25)"
QTY_RE = re.compile(
    r"\b(\d+)\s+(?:left|in stock|available|units?|remaining|pieces?|on hand)\b"
    r"|\bonly\s+(\d+)\b"
    r"|\bin stock\s*\((\d+)\)",
    re.IGNORECASE,
)
NUM_RE = re.compile(r"\d+(?:\.\d+)?")

# ---- Safety guard (Problem 12): things a reply must never contain ----
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
CARD_LIKE_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")  # card / account number shapes
INTERNAL_MARKERS = ("pbkdf2", "password_hash", "password hash", "portkey", "api key", "api_key",
                    "campus_customs.db", "campus_customs_new.db", ".session_secret")
KEY_LIKE_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{8,}")  # API-key shaped strings (not "risk-free")


def private_data_problems(reply: str, deps: ShopDeps) -> list[str]:
    """Safety rules 6-8 enforced in code: no other people's emails, no internals, no card numbers."""
    problems = []
    own = deps.customer.email.lower() if deps.customer else None
    others = [e for e in EMAIL_RE.findall(reply) if e.lower() != own]
    if others:
        problems.append("an email address that isn't the logged-in customer's own")
    low = reply.lower()
    hits = [m for m in INTERNAL_MARKERS if m in low]
    if KEY_LIKE_RE.search(reply):
        hits.append("an API-key-like string")
    if hits:
        problems.append(f"internal system details ({', '.join(hits)})")
    if CARD_LIKE_RE.search(reply):
        problems.append("a long number that looks like a card or account number")
    return problems


def invented_numbers(reply: str, deps: ShopDeps) -> tuple[list[str], list[str]]:
    """Prices / quantities in the reply that no tool returned this message (and the shopper didn't say)."""
    said = {float(n) for n in NUM_RE.findall(deps.user_message.replace(",", ""))}
    bad_prices = [m for m in PRICE_RE.findall(reply)
                  if (v := float(m.replace(",", ""))) not in deps.seen_prices and v not in said]
    bad_qty = [q for groups in QTY_RE.findall(reply) for q in groups
               if q and int(q) not in deps.seen_quantities and float(q) not in said]
    return bad_prices, bad_qty


def _model() -> OpenAIChatModel:
    api_key = os.environ.get("PORTKEY_API_KEY")
    model_name = os.environ.get("PORTKEY_MODEL")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY not found. Copy .env.example to .env in hw4/ and add your key.")
    if not model_name:
        raise RuntimeError("PORTKEY_MODEL not set. Add it to hw4/.env (see .env.example).")
    client = AsyncOpenAI(api_key=api_key, base_url=os.environ.get("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"))
    return OpenAIChatModel(model_name, provider=OpenAIProvider(openai_client=client))


@lru_cache(maxsize=1)
def get_agent() -> Agent[ShopDeps, ChatReply]:
    agent = Agent(
        _model(),
        name="campus_customs_shop",
        instructions=PROMPT_FILE.read_text(encoding="utf-8"),
        deps_type=ShopDeps,
        output_type=ChatReply,
        tools=SHOP_TOOLS,
        retries=OUTPUT_RETRIES,
    )

    @agent.instructions
    def shopper_context(ctx: RunContext[ShopDeps]) -> str:
        """Code in the agent context (Problem 8): who is chatting and what page they're on,
        rebuilt for every message from ShopDeps."""
        return customer_instructions(ctx.deps) + "\n\n" + page_instructions(ctx.deps)

    @agent.output_validator
    def page_needs_search(ctx: RunContext[ShopDeps], output: ChatReply) -> ChatReply:
        # show_on_page displays the latest search_products results, so there must be one.
        if output.show_on_page and not ctx.deps.last_search_ids:
            raise ModelRetry("You set show_on_page but haven't called search_products in this message. "
                             "Call search_products for what the shopper is browsing, then answer.")
        return output

    @agent.output_validator
    def no_private_data(ctx: RunContext[ShopDeps], output: ChatReply) -> ChatReply:
        problems = private_data_problems(output.reply + " " + " ".join(output.suggestions), ctx.deps)
        if problems:
            raise ModelRetry(
                "Safety rules 6-8: your reply contains " + "; ".join(problems) + ". Rewrite it without that: "
                "never share other people's details, system internals, or sensitive numbers."
            )
        return output

    @agent.output_validator
    def no_invented_numbers(ctx: RunContext[ShopDeps], output: ChatReply) -> ChatReply:
        bad_prices, bad_qty = invented_numbers(output.reply, ctx.deps)
        if bad_prices or bad_qty:
            problems = [f"price ${p}" for p in bad_prices] + [f"quantity {q}" for q in bad_qty]
            raise ModelRetry(
                f"Your reply states {', '.join(problems)}, but no tool returned that during this message. "
                "Prices and stock must come from the database: call get_product_price / get_stock for the "
                "product, then answer using exactly the returned values (or leave the number out)."
            )
        return output

    return agent


def customer_instructions(deps: ShopDeps) -> str:
    c = deps.customer
    if c is None:
        return ("## Who is chatting\nA guest (not logged in). You don't know their name or email; don't ask for "
                "their email or password. Their chat is not saved after they leave.")
    return (
        "## Who is chatting\n"
        f"Logged-in customer: **{c.name}** (first name {c.first_name}), email **{c.email}**, "
        f"customer since {c.member_since}.\n"
        "Greet them by first name now and then. You may tell them their own name or email if they ask "
        "(e.g. \"which email is my account?\"). Never reveal it to anyone else, and never mention passwords. "
        "Earlier messages in this conversation are their saved chat history, so you can refer back to it "
        "(\"the hoodie you asked about earlier\")."
    )


def page_instructions(deps: ShopDeps) -> str:
    v = deps.page
    if v is None:
        return "## Where the shopper is\nUnknown page."
    if v.product:
        return (
            "## Where the shopper is\n"
            f"They are on the product page for **{v.product.name}** (product_id `{v.product.product_id}`).\n"
            "If they say \"this\", \"it\", \"this one\", or ask about colors, sizes, price, or stock without naming "
            f"a product, they mean {v.product.name}: call the lookup tools with product_id "
            f"`{v.product.product_id}` (no search needed). If they name a different product, use that one."
        )
    where = {"home": "the Home page", "products": "the Products page", "about": "the About us page",
             "login": "the Log in page", "signup": "the Create account page"}.get(v.page, f"the page {v.path}")
    text = f"## Where the shopper is\nThey are on {where}."
    if v.results_title:
        text += (f" The page is currently showing your earlier chat search results: \"{v.results_title}\". "
                 "\"These\" / \"those\" probably refers to them.")
    return text + " They are not on a single product's page, so if they say \"this\" without context, ask which product."


def to_message_history(turns: list[ChatTurn]) -> list[ModelMessage]:
    history: list[ModelMessage] = []
    for t in turns[-MAX_HISTORY_TURNS:]:
        if t.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=t.content)]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=t.content)]))
    return history


def stop_reason(exc: BaseException) -> str:
    if isinstance(exc, UsageLimitExceeded):
        return "request_limit"            # hit MAX_REQUESTS_PER_MESSAGE
    if isinstance(exc, ModelHTTPError):
        return "content_filter" if "content_filter" in str(exc.body) else "model_error"
    if isinstance(exc, UnexpectedModelBehavior):
        return "output_rejected"          # output guards kept failing after retries
    return "error"


async def run_chat(message: str, history: list[ChatTurn], deps: ShopDeps, shopper: str = "guest") -> ChatReply:
    """Run the agent loop for one shopper message, node by node, recording every step in the
    append-only audit trail (audit.py). Exceptions are recorded with a stop reason, then re-raised."""
    # Numbers the shopper typed (e.g. "under $60") may be repeated back without a tool.
    deps.user_message = " ".join([t.content for t in history if t.role == "user"] + [message])
    audit = RunAudit(shopper=shopper, page=deps.page.path if deps.page else None, message=message,
                     model=os.environ.get("PORTKEY_MODEL", "?"))
    run = None
    try:
        async with get_agent().iter(
            message,
            deps=deps,
            message_history=to_message_history(history),
            # Portkey's Azure gpt-6-luna only allows function tools with reasoning_effort='none'.
            model_settings={"max_tokens": MAX_OUTPUT_TOKENS, "openai_reasoning_effort": "none"},
            usage_limits=UsageLimits(request_limit=MAX_REQUESTS_PER_MESSAGE),
        ) as run:
            step = 0
            async for node in run:
                if Agent.is_model_request_node(node):
                    step += 1
                    audit.on_model_request(node.request, step)
                elif Agent.is_call_tools_node(node):
                    audit.on_model_response(node.model_response)
        result = run.result
        audit.end("final_result", usage=result.usage)
        return result.output
    except BaseException as exc:
        audit.end(stop_reason(exc), usage=run.usage if run is not None else None, error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        audit.flush()
