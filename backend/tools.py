"""Tools the shop agent can call (Problems 5-6).

All tools are READ-ONLY on the working copy (data/campus_customs_new.db, a copy of the
given campus_customs.db) and only touch catalogue + inventory. No tool can see users,
password hashes, or chats.

Every price and quantity a tool returns is also recorded in ctx.deps.seen_prices /
seen_quantities, which the output guard in agent.py checks the reply against.
"""

import json
import re
import sqlite3

from pydantic_ai import RunContext

from db import connect
from model import (
    Alternative,
    AlternativesResult,
    CategorySummary,
    CustomerContext,
    ProductCard,
    ProductDescription,
    ProductNotFound,
    ProductPrice,
    ProductRef,
    ProductStock,
    SearchResults,
    ShopDeps,
    SizeStock,
    ViewingContext,
)

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
CATEGORIES = ["Hoodies", "Crewnecks", "T-shirts & tees", "Quarter-zips", "Jackets & full-zips"]
MAX_RESULTS = 12
LOW_STOCK = 5  # 1-5 units = "only N left"

# How shoppers say sizes -> the size codes stored in inventory.size.
SIZE_ALIASES = {
    "xs": "XS", "x-small": "XS", "xsmall": "XS", "extra small": "XS", "extra-small": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "x-large": "XL", "xlarge": "XL", "extra large": "XL", "extra-large": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "xxlarge": "XXL", "2x": "XXL",
    "extra extra large": "XXL", "double xl": "XXL",
}


def category(garment_type: str) -> str:
    """Fold the ~22 messy garment_type spellings into 5 shopper categories (same as frontend api.ts)."""
    t = garment_type.lower()
    if "quarter-zip" in t:
        return "Quarter-zips"
    if "jacket" in t or "full-zip" in t:
        return "Jackets & full-zips"
    if "hood" in t:
        return "Hoodies"
    if "crewneck sweatshirt" in t or t == "crewneck" or "mockneck" in t:
        return "Crewnecks"
    if "t-shirt" in t or "shirt" in t:
        return "T-shirts & tees"
    return "Other"


def normalize_size(size: str) -> str | None:
    key = re.sub(r"\s+", " ", size.strip().lower())
    return SIZE_ALIASES.get(key) or (key.upper() if key.upper() in SIZE_ORDER else None)


def size_stock_map() -> dict[str, dict[str, int]]:
    """{product_id: {"XS": n, ..., "XXL": n}} for every product, in size order (Problem 9)."""
    out: dict[str, dict[str, int]] = {}
    with connect() as conn:
        for r in conn.execute("SELECT product_id, size, quantity FROM inventory"):
            out.setdefault(r["product_id"], {})[r["size"]] = r["quantity"]
    return {pid: {s: sizes.get(s, 0) for s in SIZE_ORDER} for pid, sizes in out.items()}


def _rows() -> list[sqlite3.Row]:
    with connect() as conn:
        return conn.execute(
            """
            SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
            FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
            GROUP BY c.product_id ORDER BY c.name
            """
        ).fetchall()


def _ref(row: sqlite3.Row) -> ProductRef:
    return ProductRef(product_id=row["product_id"], name=row["name"], url=f"/products/{row['product_id']}")


def _card(row: sqlite3.Row, sizes: dict[str, dict[str, int]] | None = None) -> ProductCard:
    sizes = sizes if sizes is not None else size_stock_map()
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        category=category(row["garment_type"]),
        garment_type=row["garment_type"],
        price=row["price"],
        colors=json.loads(row["colors"]),
        total_stock=row["total_stock"],
        image_url="/media/" + row["image_file_path"],
        url=f"/products/{row['product_id']}",
        short_description=_short(row["description"]),
        size_stock=sizes.get(row["product_id"], {}),
    )


def _short(text: str, limit: int = 90) -> str:
    return text if len(text) <= limit else text[: text.rfind(" ", 0, limit)] + "…"


def _color_key(text: str) -> str:
    # "Grey" and "gray" are the same color to a shopper; the catalogue spells it "gray".
    return text.lower().replace("grey", "gray")


def _search_label(query, category_name, color, max_price, size_in_stock) -> str:
    parts = [f"“{query}”" if query else None, category_name, f"color {color}" if color else None,
             f"under ${max_price:g}" if max_price is not None else None,
             f"size {size_in_stock} in stock" if size_in_stock else None]
    return ", ".join(p for p in parts if p) or "all products"


def _stem(word: str) -> str:
    # "hoodies" -> "hoodie", "shirts" -> "shirt", but keep short words like "xs".
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def _words(text: str) -> list[str]:
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())]


def _score(row: sqlite3.Row, q_words: list[str]) -> int:
    """Keyword score: 3 per query word in the name, 1 per word found elsewhere."""
    name_words = set(_words(row["name"]))
    hay = set(_words(" ".join([row["name"], row["garment_type"], row["description"],
                                row["colors"], row["search_tags"]])))
    return sum(3 if w in name_words else 1 for w in q_words if w in hay)


def _covers(row: sqlite3.Row, q_words: list[str]) -> bool:
    hay = set(_words(" ".join([row["name"], row["garment_type"], row["description"],
                                row["colors"], row["search_tags"]])))
    return all(w in hay for w in q_words)


def _sizes_in_stock(product_ids: list[str], size: str) -> set[str]:
    with connect() as conn:
        rows = conn.execute(
            f"SELECT product_id FROM inventory WHERE size = ? AND quantity > 0 AND product_id IN ({','.join('?' * len(product_ids))})",
            (size, *product_ids),
        ).fetchall()
    return {r["product_id"] for r in rows}


def _resolve(product: str) -> sqlite3.Row | ProductNotFound:
    """Find exactly one product from a product_id or a name. Never guesses between close matches."""
    rows = _rows()
    text = product.strip()
    for row in rows:  # exact product_id, then exact name
        if row["product_id"] == text.lower() or row["name"].lower() == text.lower():
            return row
    q_words = _words(text)
    scored = sorted(((_score(r, q_words), r) for r in rows), key=lambda s: -s[0])
    scored = [(s, r) for s, r in scored if s > 0]
    if scored and (len(scored) == 1 or scored[0][0] > scored[1][0]):
        return scored[0][1]
    return ProductNotFound(
        query=product,
        message=("Several products match; ask the shopper which one, or call again with the exact product_id."
                 if scored else "No product matches. Use search_products to find it."),
        did_you_mean=[_ref(r) for _, r in scored[:5]],
    )


def _size_stock(size: str, quantity: int) -> SizeStock:
    if quantity == 0:
        status, label = "sold_out", "Sold out"
    elif quantity <= LOW_STOCK:
        status, label = "low_stock", f"Only {quantity} left"
    else:
        status, label = "in_stock", f"In stock ({quantity})"
    return SizeStock(size=size, quantity=quantity, status=status, label=label)


def _remember(ctx: RunContext[ShopDeps], prices=(), quantities=()) -> None:
    ctx.deps.seen_prices.update(float(p) for p in prices)
    ctx.deps.seen_quantities.update(int(q) for q in quantities)


# ---------- tools ----------

def search_products(
    ctx: RunContext[ShopDeps],
    query: str | None = None,
    category_name: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size_in_stock: str | None = None,
    limit: int = 8,
) -> SearchResults:
    """Search the Campus Customs catalogue to FIND products. All filters are optional and combined with AND.
    Returns the top `limit` matches plus total_matches. When you set show_on_page, the website shows
    ALL matches of your most recent search on the page.

    query: keywords matched against name, description, garment type, colors and tags
        (e.g. "Davenport", "hockey", "bulldog hoodie", "law school"). Best matches first.
    category_name: one of "Hoodies", "Crewnecks", "T-shirts & tees", "Quarter-zips", "Jackets & full-zips".
    color: a color word that must appear in the product's colors (e.g. "gray", "navy", "white").
    max_price: highest price in USD.
    size_in_stock: only products with this size in stock (XS, S, M, L, XL, XXL, or "small", "large"...).
        If none of the matches have that size in stock, the matches are returned anyway with a note.
    limit: max results (default 8, max 12).
    """
    q_words = _words(query or "")
    scored: list[tuple[int, sqlite3.Row]] = []
    for row in _rows():
        if category_name and category(row["garment_type"]).lower() != category_name.lower():
            continue
        if color and _color_key(color) not in _color_key(" ".join(json.loads(row["colors"]))):
            continue
        if max_price is not None and row["price"] > max_price:
            continue
        score = _score(row, q_words) if q_words else 0
        if q_words and score == 0:
            continue
        scored.append((score, row))
    if q_words:
        # Prefer products that match EVERY query word ("quarter zip" shouldn't list full-zip
        # jackets); fall back to partial matches only if nothing matches fully ("Davenport stuff").
        full = [(sc, r) for sc, r in scored if _covers(r, q_words)]
        scored = full or scored
    scored.sort(key=lambda s: (-s[0], s[1]["name"]))
    rows = [r for _, r in scored]
    note = None
    if size_in_stock and rows:
        size = normalize_size(size_in_stock) or size_in_stock.upper()
        keep = _sizes_in_stock([r["product_id"] for r in rows], size)
        if keep:
            rows = [r for r in rows if r["product_id"] in keep]
        else:
            note = (f"None of these matches has size {size} in stock (sold out). They are shown anyway as the "
                    f"closest alternatives: tell the shopper {size} is sold out and call get_stock "
                    "to say which sizes are available.")
    if not rows:
        note = "No products match. Try fewer filters or different keywords."
    sizes = size_stock_map()
    cards = [_card(r, sizes) for r in rows[: max(1, min(limit, MAX_RESULTS))]]
    _remember(ctx, prices=[c.price for c in cards],
              quantities=[c.total_stock for c in cards] + [len(rows)] + [q for c in cards for q in c.size_stock.values()])
    # The page gets ALL matches of the latest search (main.py), not just the cards the model sees.
    ctx.deps.last_search_ids = [r["product_id"] for r in rows]
    ctx.deps.last_search_label = _search_label(query, category_name, color, max_price, size_in_stock)
    return SearchResults(products=cards, total_matches=len(rows), note=note)


def get_product_description(ctx: RunContext[ShopDeps], product: str) -> ProductDescription | ProductNotFound:
    """What a product is: full description, garment type, colors and tags. Use for "tell me about…",
    material/fit/graphic questions. Has NO price or stock — use get_product_price / get_stock for those.

    product: the product_id (best, from search results) or the product's name.
    """
    row = _resolve(product)
    if isinstance(row, ProductNotFound):
        return row
    return ProductDescription(
        product=_ref(row),
        category=category(row["garment_type"]),
        garment_type=row["garment_type"],
        description=row["description"],
        colors=json.loads(row["colors"]),
        search_tags=json.loads(row["search_tags"]),
    )


def get_product_price(ctx: RunContext[ShopDeps], product: str) -> ProductPrice | ProductNotFound:
    """The exact current price of one product. ALWAYS call this before stating a price.

    product: the product_id (best, from search results) or the product's name.
    """
    row = _resolve(product)
    if isinstance(row, ProductNotFound):
        return row
    _remember(ctx, prices=[row["price"]])
    return ProductPrice(product=_ref(row), price=row["price"], price_display=f"${row['price']:.2f}")


def get_stock(ctx: RunContext[ShopDeps], product: str, size: str | None = None) -> ProductStock | ProductNotFound:
    """Live stock for one product: units on hand in every size (XS-XXL). ALWAYS call this before saying
    whether something is available, how many are left, or which sizes are sold out.

    product: the product_id (best, from search results) or the product's name.
    size: the size the shopper asked about, if any (XS, S, M, L, XL, XXL, or words like "small", "2XL").
    """
    row = _resolve(product)
    if isinstance(row, ProductNotFound):
        return row
    with connect() as conn:
        found = {r["size"]: r["quantity"] for r in conn.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ?", (row["product_id"],))}
    sizes = [_size_stock(s, found.get(s, 0)) for s in SIZE_ORDER]
    total = sum(s.quantity for s in sizes)
    requested_size, requested, note = None, None, None
    if size:
        requested_size = normalize_size(size)
        if requested_size is None:
            note = f"{size!r} isn't one of our sizes. We stock XS, S, M, L, XL and XXL."
        else:
            requested = next(s for s in sizes if s.size == requested_size)
            if requested.status == "sold_out":
                note = f"Size {requested_size} is SOLD OUT. Say so clearly and offer the available sizes."
    _remember(ctx, quantities=[s.quantity for s in sizes] + [total])
    return ProductStock(
        product=_ref(row),
        requested_size=requested_size,
        requested=requested,
        sizes=sizes,
        available_sizes=[s.size for s in sizes if s.quantity > 0],
        sold_out_sizes=[s.size for s in sizes if s.quantity == 0],
        total_quantity=total,
        note=note,
    )


def list_categories(ctx: RunContext[ShopDeps]) -> list[CategorySummary]:
    """The shop's product categories with how many products each has and their price range."""
    groups: dict[str, list[float]] = {}
    for row in _rows():
        groups.setdefault(category(row["garment_type"]), []).append(row["price"])
    summary = [
        CategorySummary(category=c, product_count=len(p), min_price=min(p), max_price=max(p))
        for c in CATEGORIES + sorted(set(groups) - set(CATEGORIES))
        if (p := groups.get(c))
    ]
    _remember(ctx, prices=[x for c in summary for x in (c.min_price, c.max_price)],
              quantities=[c.product_count for c in summary])
    return summary


def find_alternatives(
    ctx: RunContext[ShopDeps], product: str, size: str | None = None, max_price: float | None = None, limit: int = 4
) -> AlternativesResult | ProductNotFound:
    """Similar products that ARE in stock, for when a product or the shopper's size is sold out.
    One call replaces a search plus several get_stock calls.

    product: product_id (best) or name of the product they wanted.
    size: the size they need (XS-XXL or words like "medium"); alternatives must have it in stock.
    max_price: optional budget in USD.
    limit: how many alternatives (default 4, max 6).
    Ranked by: same category, shared tags/keywords (college, sport, school, style, color), then closest price.
    """
    row = _resolve(product)
    if isinstance(row, ProductNotFound):
        return row
    want = normalize_size(size) if size else None
    sizes = size_stock_map()
    target_tags = {t.lower() for t in json.loads(row["search_tags"])} | set(json.loads(row["colors"]))
    target_words = set(_words(row["name"])) - {"yale", "t", "shirt", "1", "4"}
    target_cat = category(row["garment_type"])
    scored = []
    for r in _rows():
        if r["product_id"] == row["product_id"]:
            continue
        qty = sizes.get(r["product_id"], {}).get(want, 0) if want else r["total_stock"]
        if qty <= 0 or (max_price is not None and r["price"] > max_price):
            continue
        tags = {t.lower() for t in json.loads(r["search_tags"])} | set(json.loads(r["colors"]))
        shared = sorted((tags & target_tags) - {"yale", "campus customs", "college apparel", "yale merch"})
        shared_words = sorted((set(_words(r["name"])) & target_words))
        same_cat = category(r["garment_type"]) == target_cat
        score = (10 if same_cat else 0) + 2 * len(shared_words) + len(shared)
        if score == 0:
            continue
        why = ", ".join(filter(None, ["same category" if same_cat else category(r["garment_type"]),
                                      ("shares: " + ", ".join(list(dict.fromkeys(shared_words + shared))[:3])) if shared_words or shared else ""]))
        scored.append((score, -abs(r["price"] - row["price"]), r, qty, why))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]["name"]))
    picked = scored[: max(1, min(limit, 6))]
    alts = [
        Alternative(product=_card(r, sizes), size_quantity=qty if want else None,
                    size_label=_size_stock(want, qty).label if want else None, why=why)
        for _, _, r, qty, why in picked
    ]
    original_qty = sizes.get(row["product_id"], {}).get(want) if want else None
    note = None
    if size and want is None:
        note = f"{size!r} isn't one of our sizes (XS-XXL); showing in-stock alternatives in any size."
    elif not alts:
        note = "No similar in-stock products found. Try without max_price, or search_products more broadly."
    _remember(ctx, prices=[a.product.price for a in alts] + [row["price"]],
              quantities=[a.size_quantity for a in alts if a.size_quantity is not None]
              + [a.product.total_stock for a in alts] + ([original_qty] if original_qty is not None else []))
    if alts:
        # Let the website show them as page cards too if the agent sets show_on_page.
        ctx.deps.last_search_ids = [a.product.product_id for a in alts]
        ctx.deps.last_search_label = f"alternatives to {row['name']}" + (f" in size {want}" if want else "")
    return AlternativesResult(original=_ref(row), size=want, original_size_quantity=original_qty,
                              alternatives=alts, note=note)


def get_customer_profile(ctx: RunContext[ShopDeps]) -> CustomerContext | str:
    """The logged-in shopper's own account details: name, email, member since.
    Use when they ask about their account ("what email is my account under?").
    Only ever returns the person who is chatting; there is no way to look up anyone else.
    """
    if ctx.deps.customer is None:
        return "The shopper is not logged in (guest). They can log in or create an account from the top bar."
    return ctx.deps.customer


def get_current_page(ctx: RunContext[ShopDeps]) -> ViewingContext | str:
    """Which page the shopper is looking at right now, including the product if they are on a
    product page. Use it to resolve "this", "it", "this one" when they haven't named a product.
    """
    return ctx.deps.page or "Unknown page (the browser didn't send page context)."


SHOP_TOOLS = [search_products, get_product_description, get_product_price, get_stock, find_alternatives,
              list_categories, get_customer_profile, get_current_page]


# ---------- helpers for main.py (not agent tools) ----------

PAGE_KINDS = {"/": "home", "/products": "products", "/about": "about", "/login": "login", "/signup": "signup"}


def viewing_context(path: str, results_title: str | None = None) -> ViewingContext:
    """Turn the browser's path into page context. A /products/<id> path is checked against the
    catalogue, so the agent only ever hears about a product that really exists."""
    path = path.split("?")[0].rstrip("/") or "/"
    product = None
    if path.startswith("/products/"):
        row = next((r for r in _rows() if r["product_id"] == path.removeprefix("/products/")), None)
        product = _ref(row) if row else None
        kind = "product" if product else "other"
    else:
        kind = PAGE_KINDS.get(path, "other")
    return ViewingContext(page=kind, path=path, product=product,
                          results_title=results_title if kind != "product" else None)


def product_names(product_ids: list[str]) -> dict[str, str]:
    return {r["product_id"]: r["name"] for r in _rows() if r["product_id"] in set(product_ids)}


def cards_for(product_ids: list[str], limit: int = 6) -> list[ProductCard]:
    """Turn the agent's product_ids into cards using live DB data. Unknown ids are dropped,
    so the website never shows a product (or price) the model invented."""
    by_id = {r["product_id"]: r for r in _rows()}
    sizes = size_stock_map()
    seen, cards = set(), []
    for pid in product_ids:
        if pid in by_id and pid not in seen:
            seen.add(pid)
            cards.append(_card(by_id[pid], sizes))
    return cards[:limit]
