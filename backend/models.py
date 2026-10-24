"""Pydantic / PydanticAI structured types for the shop chatbot (Problems 5-6)."""

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field


# ---------- agent run context ----------

class CustomerContext(BaseModel):
    """Who is chatting (Problem 8). Built server-side from the users row of the logged-in
    session cookie. These are the ONLY customer fields the agent sees: never the password
    hash, user id, or anyone else's data."""

    first_name: str
    last_name: str
    name: str
    email: str
    member_since: str = Field(description="Date the account was created (YYYY-MM-DD)")


PageKind = Literal["home", "products", "product", "about", "login", "signup", "other"]


class ViewingContext(BaseModel):
    """Where the shopper is on the site when they send the message (Problem 8).
    Built server-side from the browser's path; the product is looked up in the DB."""

    page: PageKind
    path: str
    product: "ProductRef | None" = Field(None, description="The product whose page they are on, if any")
    results_title: str | None = Field(None, description="Chat search results currently shown on the page, if any")


@dataclass
class ShopDeps:
    """Per-message context passed to every tool and to the dynamic instructions in agent.py.

    customer: who is chatting (None = guest). page: what they are looking at.
    The seen_* sets record every price and quantity a tool returned during this message, so the
    output guard in agent.py can reject a reply that states a number no tool returned.
    """

    customer: CustomerContext | None = None
    page: ViewingContext | None = None
    user_message: str = ""
    seen_prices: set[float] = field(default_factory=set)
    seen_quantities: set[int] = field(default_factory=set)
    # Problem 7: every product_id the most recent search_products call matched (not just the
    # few shown to the model), so main.py can put the full result set on the page.
    last_search_ids: list[str] = field(default_factory=list)
    last_search_label: str = ""

    @property
    def first_name(self) -> str | None:
        return self.customer.first_name if self.customer else None


# ---------- what tools return to the agent ----------

StockStatus = Literal["in_stock", "low_stock", "sold_out"]


class ProductRef(BaseModel):
    """Which product a lookup is about, so the agent can name it and link it as a card."""

    product_id: str
    name: str
    url: str


class ProductCard(BaseModel):
    """Compact product info: what search returns to the agent and what the chat widget renders."""

    product_id: str
    name: str
    category: str
    garment_type: str
    price: float
    colors: list[str]
    total_stock: int
    image_url: str
    url: str = Field(description="Website path of the product page")
    short_description: str = Field(description="First ~90 characters of the description, for card text")
    size_stock: dict[str, int] = Field(default_factory=dict, description='Units per size, e.g. {"XS": 0, "S": 12, ...}')


class SearchResults(BaseModel):
    """search_products output: the top matches plus how many matched in total."""

    products: list[ProductCard] = Field(description="Top matches (up to `limit`)")
    total_matches: int = Field(description="How many products matched; all of them go on the page if show_on_page")
    note: str | None = None


class ProductDescription(BaseModel):
    """get_product_description: what the product is. Deliberately has no price or stock."""

    product: ProductRef
    category: str
    garment_type: str
    description: str
    colors: list[str] = Field(description="Colors on the garment (one colorway), not options to choose from")
    search_tags: list[str]


class ProductPrice(BaseModel):
    """get_product_price: the exact catalogue price."""

    product: ProductRef
    price: float = Field(description="Exact price in USD from catalogue.price")
    price_display: str = Field(description='Ready-to-say price, e.g. "$68.00"')
    currency: Literal["USD"] = "USD"


class SizeStock(BaseModel):
    size: str
    quantity: int = Field(description="Units on hand from inventory.quantity")
    status: StockStatus = Field(description="sold_out = 0, low_stock = 1-5, in_stock = 6+")
    label: str = Field(description='Ready-to-say status, e.g. "Sold out", "Only 2 left", "In stock (25)"')


class ProductStock(BaseModel):
    """get_stock: live per-size stock, plus the one size the shopper asked about (if any)."""

    product: ProductRef
    requested_size: str | None = Field(None, description="Normalized size the shopper asked about (XS-XXL)")
    requested: SizeStock | None = Field(None, description="Stock for requested_size; None if no size was asked")
    sizes: list[SizeStock] = Field(description="All six sizes, XS to XXL")
    available_sizes: list[str]
    sold_out_sizes: list[str]
    total_quantity: int
    note: str | None = None


class ProductNotFound(BaseModel):
    """Returned instead of a lookup result when the product can't be identified for sure."""

    found: Literal[False] = False
    query: str
    message: str
    did_you_mean: list[ProductRef] = Field(default_factory=list)


class Alternative(BaseModel):
    product: ProductCard
    size_quantity: int | None = Field(None, description="Live units of the requested size (None if no size was given)")
    size_label: str | None = Field(None, description='e.g. "In stock (12)", "Only 3 left"')
    why: str = Field(description='Why it is similar, e.g. "same category; shares: hockey, navy"')


class AlternativesResult(BaseModel):
    """find_alternatives (Problem 9): in-stock substitutes for a sold-out product or size."""

    original: ProductRef
    size: str | None
    original_size_quantity: int | None = Field(None, description="Units of that size for the original product")
    alternatives: list[Alternative]
    note: str | None = None


class CategorySummary(BaseModel):
    category: str
    product_count: int
    min_price: float
    max_price: float


# ---------- agent output ----------

class ChatReply(BaseModel):
    """Structured output the agent must return for every message."""

    reply: str = Field(description="What to say to the shopper, in the Campus Customs voice.")
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id of each product to show as a card IN THE CHAT (from tool results only), most relevant first, max 6.",
    )
    show_on_page: bool = Field(
        False,
        description="True when the shopper is browsing a type/category/collection (e.g. 'what hoodies do you have?'): "
                    "the website then shows ALL matches of your most recent search_products call as product cards on the page.",
    )
    page_title: str | None = Field(
        None, description='Short heading for the page results when show_on_page is true, e.g. "Hoodies" or "Davenport College gear".'
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Problem 9: 2-3 short follow-up questions the SHOPPER might tap next, in their voice "
                    "(e.g. \"Is it in stock in M?\", \"Show similar crewnecks\"). Max ~40 characters each.",
    )


# ---------- HTTP API (main.py) ----------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class PageContext(BaseModel):
    """What the browser says about the current page (Problem 8). Untrusted: the server only
    uses the path to look the product up in the DB, and caps the lengths."""

    path: str = Field("/", max_length=200)
    results_title: str | None = Field(None, max_length=120)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Only used for shoppers who are not logged in; logged-in history comes from chat_messages.
    history: list[ChatTurn] = Field(default_factory=list)
    page: PageContext | None = None


class PageResults(BaseModel):
    """Chat search results the website renders on the page as a product-card grid (Problem 7)."""

    title: str = Field(description='Heading, e.g. "Hoodies"')
    query: str = Field(description="What was searched, e.g. 'category Hoodies'")
    total: int = Field(description="Number of matching products (all are in `products`, up to 60)")
    products: list[ProductCard]


class ChatResponse(BaseModel):
    """POST /api/chat response: the API contract between the agent backend and the website."""

    reply: str = Field(description="Chat bubble text")
    products: list[ProductCard] = Field(default_factory=list, description="Small cards inside the chat panel (max 6)")
    page: PageResults | None = Field(None, description="When set, the website shows these as product cards on the page")
    suggestions: list[str] = Field(default_factory=list, description="Quick-reply chips under the reply (max 3)")


class ChatHistoryResponse(BaseModel):
    messages: list[dict]


ViewingContext.model_rebuild()
