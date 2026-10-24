"""Problem 9 evidence: does find_alternatives make sold-out answers faster/cheaper?

Runs the same sold-out-size questions through two agents built from the same code:
  WITH    = the live agent (has find_alternatives + the prompt rule to use it)
  WITHOUT = same model/prompt, but find_alternatives removed and the old rule
            ("suggest similar in-stock items from search_products") restored.
Records model requests, tokens, latency and tool calls. Read-only on the DB.

Run from hw4/:  python3 scripts/benchmark_alternatives.py   -> output/p9_alternatives_benchmark.md
"""

import asyncio
import sys
import time
from pathlib import Path

HW4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HW4 / "backend"))

from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.messages import ModelResponse, ToolCallPart  # noqa: E402

import agent as shop_agent  # noqa: E402
from model import ChatReply, ShopDeps, ViewingContext  # noqa: E402
from tools import SHOP_TOOLS, find_alternatives, viewing_context  # noqa: E402

QUESTIONS = [
    ("/products/fencing-left-chest-hoodie", "Do you have this in a large? If not, what else could I get in L?"),
    ("/products/davenport-college-crewneck", "I need a small in this. Anything similar if it's gone?"),
    ("/products/champion-reverse-weave-hoodie-1", "Is this available in XL? Otherwise show me something like it."),
]

NEW_RULE_START = "- **When the size they want is sold out**"
OLD_RULE = "- If **every** size is sold out, say the product is sold out and suggest similar in-stock items from `search_products`."


def build_without() -> Agent:
    prompt = shop_agent.PROMPT_FILE.read_text(encoding="utf-8")
    lines = [OLD_RULE if l.startswith(NEW_RULE_START) else l for l in prompt.splitlines()
             if "`find_alternatives`" not in l or l.startswith(NEW_RULE_START)]
    a = Agent(shop_agent._model(), instructions="\n".join(lines), deps_type=ShopDeps, output_type=ChatReply,
              tools=[t for t in SHOP_TOOLS if t is not find_alternatives], retries=2)
    a.instructions(lambda ctx: shop_agent.customer_instructions(ctx.deps) + "\n\n" + shop_agent.page_instructions(ctx.deps))
    return a


async def run(agent: Agent, path: str, q: str) -> dict:
    deps = ShopDeps(page=viewing_context(path), user_message=q)
    t0 = time.perf_counter()
    r = await agent.run(q, deps=deps, model_settings={"max_tokens": 1200, "openai_reasoning_effort": "none"})
    dt = time.perf_counter() - t0
    calls = [p.tool_name for m in r.new_messages() if isinstance(m, ModelResponse)
             for p in m.parts if isinstance(p, ToolCallPart) and p.tool_name != "final_result"]
    u = r.usage
    return {"secs": dt, "requests": u.requests, "tokens": (u.input_tokens or 0) + (u.output_tokens or 0),
            "calls": calls, "reply": r.output.reply, "cards": len(r.output.product_ids)}


async def main() -> None:
    agents = {"WITH find_alternatives": shop_agent.get_agent(), "WITHOUT (search + get_stock)": build_without()}
    results = {name: [] for name in agents}
    for path, q in QUESTIONS:
        for name, a in agents.items():
            res = await run(a, path, q)
            results[name].append(res)
            print(f"{name:30} {res['requests']} req {res['tokens']:6} tok {res['secs']:5.1f}s {res['calls']}")
    lines = ["# Problem 9 — find_alternatives benchmark", "",
             "Same model (gpt-6-luna via Portkey), same prompt except the sold-out rule, same 3 questions.", "",
             "| Question | Agent | Model requests | Tokens | Seconds | Tool calls | Cards |", "|---|---|---|---|---|---|---|"]
    for i, (path, q) in enumerate(QUESTIONS):
        for name in agents:
            r = results[name][i]
            lines.append(f"| {q} ({path.split('/')[-1]}) | {name} | {r['requests']} | {r['tokens']} | {r['secs']:.1f} | "
                         f"{', '.join(r['calls'])} | {r['cards']} |")
    lines += ["", "**Totals**", "", "| Agent | Model requests | Tokens | Seconds |", "|---|---|---|---|"]
    for name in agents:
        rs = results[name]
        lines.append(f"| {name} | {sum(r['requests'] for r in rs)} | {sum(r['tokens'] for r in rs)} | {sum(r['secs'] for r in rs):.1f} |")
    lines += ["", "**Replies**", ""]
    for i, (path, q) in enumerate(QUESTIONS):
        for name in agents:
            lines.append(f"- *{name}* — {q}: {results[name][i]['reply']}")
    (HW4 / "output" / "p9_alternatives_benchmark.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
