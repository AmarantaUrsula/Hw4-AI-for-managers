"""Append-only audit trail of the agent loop (Problem 12).

File: hw4/output/audit_trail.json, a JSON array of events, oldest first.

Rules
- APPEND-ONLY: entries are only ever added. Nothing in the app truncates, rewrites, or
  deletes old entries, and it survives server restarts and reset_db.sh (which only touches data/).
- Each agent run buffers its events and appends them in one locked write when the run ends
  (also when it fails), so concurrent chats can't interleave or clobber each other.
- If the file is ever unreadable, it is moved aside to audit_trail.corrupt-<time>.json
  (kept, never deleted) and a fresh array is started with a note pointing to it.
- Privacy: no emails, passwords, cookies, or keys. Shoppers are "guest" or "customer #<id>",
  and long text is cut to a short preview.

Event fields: time (UTC ISO), run_id, seq, event, plus tool / args / result / stop_reason / usage
as relevant. Events: run_start, model_request, tool_call, tool_result, guard_retry,
final_answer, run_end.
"""

import fcntl
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic_ai.messages import (
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
)

AUDIT_PATH = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
LOCK_PATH = AUDIT_PATH.with_suffix(".lock")
PREVIEW = 200  # max characters for any message / args / result preview

_thread_lock = threading.Lock()


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def short(value: Any, limit: int = PREVIEW) -> str:
    if isinstance(value, BaseModel):
        text = value.model_dump_json(exclude_none=True)
    elif isinstance(value, (dict, list)):
        text = json.dumps(value, default=str)
    else:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def summarize_result(content: Any) -> str:
    """Human-readable one-liner for the common tool results; JSON preview for the rest."""
    name = type(content).__name__
    try:
        if name == "SearchResults":
            names = ", ".join(p.name for p in content.products[:4])
            return short(f"{content.total_matches} matches: {names}" + (f" | note: {content.note}" if content.note else ""))
        if name == "ProductPrice":
            return f"{content.product.name}: {content.price_display}"
        if name == "ProductStock":
            sizes = " ".join(f"{s.size}={s.quantity}" for s in content.sizes)
            req = f" | asked {content.requested_size}={content.requested.quantity}" if content.requested else ""
            return short(f"{content.product.name}: {sizes}{req}")
        if name == "ProductDescription":
            return short(f"{content.product.name}: {content.description}")
        if name == "AlternativesResult":
            alts = ", ".join(f"{a.product.name} ({a.size_label or a.product.total_stock})" for a in content.alternatives)
            return short(f"for {content.original.name} size {content.size}: {alts or 'none'}")
        if name == "ProductNotFound":
            return short(f"NOT FOUND '{content.query}': {content.message}")
        if name == "CustomerContext":
            return f"customer profile: {content.first_name} (email withheld from audit)"
    except Exception:  # never let auditing break a chat
        pass
    return short(content)


def append_entries(entries: list[dict]) -> None:
    """Append events to the audit file (process + thread safe). Never removes anything."""
    if not entries:
        return
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _thread_lock, open(LOCK_PATH, "w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        existing: list = []
        if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size > 0:
            try:
                existing = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    raise ValueError("audit trail is not a JSON array")
            except ValueError:
                aside = AUDIT_PATH.with_name(f"audit_trail.corrupt-{datetime.now():%Y%m%d-%H%M%S}.json")
                os.replace(AUDIT_PATH, aside)  # keep the old file; never delete it
                existing = [{"time": now(), "event": "audit_note",
                             "result": f"previous file was unreadable and was kept as {aside.name}"}]
        existing.extend(entries)
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(existing, indent=1, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, AUDIT_PATH)  # atomic: readers see the old or the new file, never half


class RunAudit:
    """Collects the events of one agent run, then appends them all at the end."""

    def __init__(self, shopper: str, page: str | None, message: str, model: str) -> None:
        self.run_id = uuid.uuid4().hex[:10]
        self.events: list[dict] = []
        self.started = datetime.now(timezone.utc)
        self.add("run_start", shopper=shopper, page=page, model=model, message=short(message))

    def add(self, event: str, **fields: Any) -> None:
        self.events.append({"time": now(), "run_id": self.run_id, "seq": len(self.events) + 1,
                            "event": event, **{k: v for k, v in fields.items() if v is not None}})

    def on_model_request(self, request: ModelRequest, step: int) -> None:
        """A model call is about to happen; record what it is being sent back (tool results, retries)."""
        for part in request.parts:
            if isinstance(part, ToolReturnPart) and part.tool_name != "final_result":
                self.add("tool_result", tool=part.tool_name, result=summarize_result(part.content))
            elif isinstance(part, RetryPromptPart):
                # Output guards (invented numbers, show_on_page without a search) or bad tool args.
                self.add("guard_retry", tool=part.tool_name, result=short(part.content))
        self.add("model_request", step=step)

    def on_model_response(self, response: ModelResponse) -> None:
        for part in response.parts:
            if isinstance(part, ToolCallPart):
                if part.tool_name == "final_result":
                    args = part.args_as_dict()
                    self.add("final_answer", reply=short(args.get("reply", ""), 160),
                             cards=len(args.get("product_ids", [])), show_on_page=args.get("show_on_page") or None,
                             suggestions=len(args.get("suggestions", [])) or None)
                else:
                    self.add("tool_call", tool=part.tool_name, args=short(part.args_as_dict(), 160))
            elif isinstance(part, TextPart) and part.content.strip():
                self.add("model_text", result=short(part.content, 120))

    def end(self, stop_reason: str, usage: Any = None, error: str | None = None) -> None:
        secs = (datetime.now(timezone.utc) - self.started).total_seconds()
        u = None
        if usage is not None:
            u = {"requests": usage.requests, "input_tokens": usage.input_tokens, "output_tokens": usage.output_tokens}
        self.add("run_end", stop_reason=stop_reason, seconds=round(secs, 2), usage=u, error=short(error) if error else None)

    def flush(self) -> None:
        try:
            append_entries(self.events)
        except Exception:  # auditing must never break the shopper's chat
            import logging
            logging.getLogger("campus_customs").exception("audit write failed")
