"""Campus Customs API — the file you run with Uvicorn.

Run (from hw4/backend):
    uvicorn main:app --reload --port 8000

- Problem 3: catalogue, per-size stock, and product images (read-only).
- Problem 4: create account / log in (auth.py), which writes to users.
- Problem 5: POST /api/chat runs the PydanticAI shop agent (agent.py) and returns its
  reply plus product cards; logged-in chats are saved to chat_messages.

All reads and writes use the working copy data/campus_customs_new.db (db.py);
the original data/campus_customs.db is never touched.
"""

import json
import logging
import sqlite3

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded

from agent import run_chat
from auth import current_user
from auth import router as auth_router
from db import DATA_DIR, check_data_pack, connect
from models import ChatHistoryResponse, ChatRequest, ChatResponse, ChatTurn, CustomerContext, PageResults, ShopDeps
from tools import cards_for, product_names, size_stock_map, viewing_context

log = logging.getLogger("campus_customs")

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

app = FastAPI(title="Campus Customs API", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)  # /api/auth/* (Problem 4)

# Product images: catalogue.image_file_path is "products/<file>.jpg",
# relative to data/, so it is served at /media/products/<file>.jpg.
# Only data/products is mounted, so the .db file is never downloadable.
check_data_pack()  # clear error if hw4/data/ is missing the data pack
app.mount("/media/products", StaticFiles(directory=DATA_DIR / "products"), name="media")


def get_db() -> sqlite3.Connection:
    # Read-only connection to the working copy; only auth.py opens a writable one.
    return connect()


def image_url(image_file_path: str) -> str:
    return "/media/" + image_file_path


def product_from_row(row: sqlite3.Row) -> dict:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_file_path": row["image_file_path"],
        "image_url": image_url(row["image_file_path"]),
        "price": row["price"],
    }


def inventory_for(conn: sqlite3.Connection, product_id: str) -> list[dict]:
    rows = conn.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)
    ).fetchall()
    stock = [{"size": r["size"], "quantity": r["quantity"]} for r in rows]
    stock.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)
    return stock


@app.get("/api/health")
def health() -> dict:
    with get_db() as conn:
        n = conn.execute("SELECT COUNT(*) FROM catalogue").fetchone()[0]
    return {"status": "ok", "products": n}


@app.get("/api/products")
def list_products(q: str | None = None) -> list[dict]:
    """All products with total stock. Optional ?q= filters on name, type, tags, description."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
            FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
            GROUP BY c.product_id
            ORDER BY c.name
            """
        ).fetchall()
    sizes = size_stock_map()
    products = []
    for row in rows:
        p = product_from_row(row)
        p["total_stock"] = row["total_stock"]
        p["size_stock"] = sizes.get(row["product_id"], {})  # Problem 9: size strip on cards
        products.append(p)
    if q:
        needle = q.lower()
        products = [
            p for p in products
            if needle in " ".join(
                [p["name"], p["garment_type"], p["description"], *p["search_tags"], *p["colors"]]
            ).lower()
        ]
    return products


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict:
    """One product with its per-size stock."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        product = product_from_row(row)
        product["inventory"] = inventory_for(conn, product_id)
    product["total_stock"] = sum(s["quantity"] for s in product["inventory"])
    return product


# ---------- chat (Problem 5) ----------

HISTORY_LIMIT = 10
PAGE_RESULTS_LIMIT = 60

FILTERED_REPLY = (
    "Sorry, I can't help with that. I'm here for Campus Customs shopping: "
    "products, sizes, colors, and what's in stock. What can I help you find?"
)
UNAVAILABLE_REPLY = "Sorry, our shopping assistant is having trouble right now. Please try again in a moment."


def load_history(user_id: int) -> list[ChatTurn]:
    """The logged-in customer's last HISTORY_LIMIT saved messages, replayed to the agent.
    Assistant turns get a note of the product cards they showed, so "that one" still works later."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, HISTORY_LIMIT),
        ).fetchall()
    turns = []
    for r in reversed(rows):
        content = r["content"]
        if r["role"] == "assistant" and r["products_json"]:
            ids = [p["product_id"] for p in json.loads(r["products_json"]) if "product_id" in p]
            names = product_names(ids)
            if names:
                content += "\n[Product cards shown: " + "; ".join(f"{names[i]} ({i})" for i in ids if i in names) + "]"
        turns.append(ChatTurn(role=r["role"], content=content))
    return turns


def customer_context(user: dict | None) -> CustomerContext | None:
    """Who is chatting, from the users row behind the session cookie (never from the request body)."""
    if not user:
        return None
    with connect() as conn:
        created = conn.execute("SELECT created_at FROM users WHERE id = ?", (user["id"],)).fetchone()
    return CustomerContext(first_name=user["first_name"], last_name=user["last_name"], name=user["name"],
                           email=user["email"], member_since=(created["created_at"] or "")[:10])


def save_turn(user_id: int, message: str, response: ChatResponse) -> None:
    products_json = json.dumps([c.model_dump() for c in response.products]) if response.products else None
    with connect(write=True) as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, message)
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, response.reply, products_json),
        )


def clean_suggestions(items: list[str]) -> list[str]:
    """Problem 9: at most 3 short, distinct quick replies."""
    out: list[str] = []
    for text in items:
        text = " ".join(text.split())[:60]
        if text and text.lower() not in {o.lower() for o in out}:
            out.append(text)
    return out[:3]


def page_results(show: bool, title: str | None, deps: ShopDeps) -> PageResults | None:
    """Problem 7: turn the agent's latest search into the product grid the website shows on the page.

    The product list comes from what search_products actually matched (deps.last_search_ids),
    rebuilt from the database, so the page never shows an invented product or price.
    """
    if not show or not deps.last_search_ids:
        return None
    cards = cards_for(deps.last_search_ids, limit=PAGE_RESULTS_LIMIT)
    return PageResults(title=title or deps.last_search_label, query=deps.last_search_label,
                       total=len(deps.last_search_ids), products=cards)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request) -> ChatResponse:
    """Website chat panel -> shop agent -> reply + product cards.

    Logged in: history comes from (and the turn is saved to) chat_messages for that user only,
    and the agent is told the customer's name and email (CustomerContext).
    Not logged in: the browser sends recent history; nothing is saved.
    Both: req.page (current path) becomes ViewingContext, so "this" means the product on screen.
    """
    user = current_user(request)
    history = load_history(user["id"]) if user else req.history[-HISTORY_LIMIT:]
    page = req.page
    deps = ShopDeps(customer=customer_context(user),
                    page=viewing_context(page.path, page.results_title) if page else None)
    try:
        output = await run_chat(req.message, history, deps)
        response = ChatResponse(reply=output.reply, products=cards_for(output.product_ids),
                                page=page_results(output.show_on_page, output.page_title, deps),
                                suggestions=clean_suggestions(output.suggestions))
    except ModelHTTPError as e:
        if "content_filter" in str(e.body):
            # Azure's content filter blocked the message (e.g. a jailbreak attempt).
            response = ChatResponse(reply=FILTERED_REPLY)
        else:
            log.exception("model error")
            raise HTTPException(502, UNAVAILABLE_REPLY)
    except UsageLimitExceeded:
        response = ChatResponse(reply="Sorry, that one took me too long to look up. Could you ask it a simpler way?")
    except UnexpectedModelBehavior:
        # e.g. the reply kept stating a price/quantity the database didn't return (output guard).
        log.warning("agent output rejected after retries", exc_info=True)
        response = ChatResponse(reply="Sorry, I couldn't confirm that from our live catalogue just now. "
                                      "Please check the product page for the current price and sizes.")
    if user:
        save_turn(user["id"], req.message, response)
    return response


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
def chat_history(request: Request) -> ChatHistoryResponse:
    """The logged-in shopper's recent chat (only their own), so the panel can restore it."""
    user = current_user(request)
    if not user:
        return ChatHistoryResponse(messages=[])
    with connect() as conn:
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT 20",
            (user["id"],),
        ).fetchall()
    return ChatHistoryResponse(messages=[
        {"role": r["role"], "content": r["content"],
         "products": json.loads(r["products_json"]) if r["role"] == "assistant" and r["products_json"] else []}
        for r in reversed(rows)
    ])
