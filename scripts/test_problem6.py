"""Problem 6 evidence: ask the real agent price / stock / description questions, record which
tools it called, and check every price and stock count in each reply against the database.

Run from hw4/:  python3 scripts/test_problem6.py
Writes output/p6_tool_tests.md. Read-only on the DB (no chats are saved).
"""

import asyncio
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HW4 = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HW4 / "backend"))

from pydantic_ai.messages import ModelResponse, ToolCallPart  # noqa: E402

from agent import PRICE_RE, QTY_RE, get_agent  # noqa: E402
from models import ChatTurn, ShopDeps  # noqa: E402

DB = HW4 / "data" / "campus_customs_new.db"

# (conversation, what a correct answer must contain)
CASES = [
    (["How much is the Basic Hoodie Big Yale?"], "price $68.00"),
    (["Do you have the Davenport College Crewneck in a small?"], "S sold out, other sizes offered"),
    (["How many Basic Hoodie Big Yale are left in XL?"], "XL: only 2 left"),
    (["What sizes does the Fencing Left Chest Hoodie come in?"], "XS, L, XXL sold out; S, M, XL available"),
    (["Tell me about the Boola Boola T-shirt."], "description from DB"),
    (["I want the Yale Mom Crewneck in XXXL"], "we stock XS–XXL"),
    (["Is the Champion Reverse Weave Hoodie on sale? Can I get it for $50?"], "exact price, no invented discount"),
    (["What hockey stuff do you have?", "How much is the hoodie and is there a large?"], "follow-up: re-looks up price + L stock"),
]


def db_facts() -> tuple[set[float], set[int]]:
    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    prices = {r[0] for r in conn.execute("SELECT price FROM catalogue")}
    qtys = {r[0] for r in conn.execute("SELECT quantity FROM inventory")}
    qtys |= {r[0] for r in conn.execute("SELECT SUM(quantity) FROM inventory GROUP BY product_id")}
    return prices, qtys


def tool_calls(messages) -> list[str]:
    calls = []
    for m in messages:
        if isinstance(m, ModelResponse):
            for p in m.parts:
                if isinstance(p, ToolCallPart) and p.tool_name != "final_result":
                    args = p.args_as_dict()
                    calls.append(f"{p.tool_name}({', '.join(f'{k}={v!r}' for k, v in args.items())})")
    return calls


async def main() -> None:
    agent = get_agent()
    db_prices, db_qtys = db_facts()
    lines = [
        "# Problem 6 — tool lookup tests",
        "",
        f"Run {datetime.now():%Y-%m-%d %H:%M} against `data/campus_customs_new.db` with the live agent "
        "(gpt-6-luna via Portkey). For each reply, every `$` price and stock count was checked against the database.",
        "",
    ]
    all_ok = True
    for i, (turns, expected) in enumerate(CASES, 1):
        history: list[ChatTurn] = []
        for t, msg in enumerate(turns):
            deps = ShopDeps(user_message=" ".join([h.content for h in history if h.role == "user"] + [msg]))
            result = await agent.run(
                msg, deps=deps,
                message_history=None if not history else [m for m in last_messages],  # noqa: F821
                model_settings={"max_tokens": 1200, "openai_reasoning_effort": "none"},
            )
            last_messages = result.all_messages()
            history += [ChatTurn(role="user", content=msg), ChatTurn(role="assistant", content=result.output.reply)]
        reply = result.output.reply
        prices = [float(p.replace(",", "")) for p in PRICE_RE.findall(reply)]
        qtys = [int(q) for g in QTY_RE.findall(reply) for q in g if q]
        said = {float(n) for n in re.findall(r"\d+(?:\.\d+)?", " ".join(turns))}
        bad = [f"${p}" for p in prices if p not in db_prices and p not in said] + \
              [str(q) for q in qtys if q not in db_qtys]
        ok = not bad
        all_ok &= ok
        calls = tool_calls(result.new_messages())
        lines += [
            f"## {i}. {' → '.join(turns)}",
            "",
            f"- **Expected:** {expected}",
            f"- **Tools called (last turn):** {', '.join(f'`{c}`' for c in calls) or '_none_'}",
            f"- **Reply:** {reply}",
            f"- **Cards:** {', '.join(result.output.product_ids) or '_none_'}",
            f"- **Numbers in reply:** prices {prices or '—'}, quantities {qtys or '—'} → "
            + ("✅ all found in the database" if ok else f"❌ not in database: {bad}"),
            "",
        ]
        print(f"[{i}] {'OK ' if ok else 'BAD'} tools={calls}\n    {reply}\n")
    lines.append(f"**Result: {'all replies used only database prices and quantities' if all_ok else 'SOME REPLIES FAILED'}.**")
    (HW4 / "output" / "p6_tool_tests.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
