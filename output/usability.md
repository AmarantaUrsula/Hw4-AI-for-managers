# Campus Customs — Usability Improvements (Problem 9)

Four improvements: two on the front end and two in the agent/backend. Each section says **what I added**, **why it helps a Campus Customs shopper or the business**, and **where to see it in the running app**. I wrote this file before building (as a plan) and updated it after each feature was verified in the browser.

**To see them:** backend `cd backend && uvicorn main:app --reload --port 8000`, frontend `cd frontend && npm run dev`, then open http://localhost:5174.

**Why these four.** In the working copy `data/campus_customs_new.db`, **77 of 102 products have at least one sold-out size** (145 of 612 size rows are 0), and **71 products have a size with 5 or fewer left**. Before these changes, a shopper only found that out by opening each product. Size availability is the biggest source of friction in this shop, so three of the four improvements target it, and the fourth makes the chat easier to use.

| # | Improvement | Type | Try it |
|---|---|---|---|
| 1 | Color-blind-safe size & stock indicators | Front end | Products page: size strip under every card. Any product page: size buttons + legend |
| 2 | Products toolbar: My size, Sort, Hide sold out | Front end | Products page: sticky toolbar above the grid |
| 3 | Suggested follow-up replies (quick-reply chips) | Agent/backend | Open the chat: chips under the greeting and under every reply |
| 4 | `find_alternatives` tool for sold-out sizes | Agent/backend | On the Fencing Left Chest Hoodie page, ask the chat "Do you have this in a large?" |

---

## Front end 1 — Color-blind-safe size & stock indicators

**What I added**
- A **size strip** at the bottom of every product card, on the Products page, Home "Student favorites", and the cards the chat puts on the page (`components/SizeStrip.tsx`). It shows `XS S M L XL XXL`, each in one of three states:

  | State | Look | Shape / text cue |
  |---|---|---|
  | In stock (6+) | Solid **Yale-blue** chip, white text | Filled |
  | Low (1–5 left) | **Amber** chip, dark text, darker border | **"!"** after the size |
  | Sold out (0) | White chip, **dashed gray** outline | Size **crossed out** + **"✕"** |

- A **legend** ("M in stock · M! 5 or fewer left · M✕ sold out") in the Products toolbar and above the size buttons on each product page.
- The **product page size buttons** use the same encoding with words: "✓ 12 left", "! Only 2 left" (amber), "✕ Sold out" (dashed, crossed out, disabled).
- The red "Sold out" card badge became a dark on-brand badge with "✕ Sold out", and every state has an `aria-label` for screen readers ("L: sold out").
- Color choices were checked rather than assumed. Contrast ratios: white on Yale blue **12.2:1**, dark on amber **8.3:1**, gray on white **4.8:1**, all above the WCAG AA minimum of 4.5:1. Blue / amber / gray avoids the red–green pair that ~1 in 12 men can't tell apart. A **grayscale test** of the Products page (`p9_fe_grayscale_check.jpg`) shows all three states are still distinguishable with no color at all.

**Why it helps**
- **Shoppers** see whether *their* size exists before clicking. That's 77 products where they'd otherwise hit a dead end. Low stock is visible at a glance ("Only 2 left in XL"), which is honest urgency that helps shoppers decide.
- **Color-blind and low-vision shoppers** get the same information through shape, symbol, and text, not color alone.
- **Business:** fewer wasted clicks and fewer "is it in stock?" chat questions (each of which costs model tokens). It also looks more polished and stays on brand: Yale blue plus one accent color, no off-brand red.

**Where to see it:** `/products` (every card), `/` (Student favorites), `/products/fencing-left-chest-hoodie` (buttons + legend). Screenshots: `screenshots/p9_fe_toolbar_and_size_strips.jpg`, `p9_fe_detail_size_buttons.jpg`, `p9_fe_grayscale_check.jpg`.

---

## Front end 2 — Products toolbar: My size, Sort, Hide sold out

**What I added** (`pages/Products.tsx`)
- A **sticky toolbar** that stays under the nav while you scroll, with everything in a compact area:
  - search box + **Sort** (Featured, Price low → high, Price high → low, Name A–Z, Most in stock) + **Hide sold out**
  - category chips (Hoodies, Crewnecks, …)
  - **My size** chips (Any, XS–XXL): shows only products that have that size **in stock**, using live inventory
  - the size legend, a live **"18 of 102 products · size L in stock"** count, and **Reset filters**
- All filters are **saved in the URL**, e.g. `/products?cat=Hoodies&size=L&sort=price-asc`. Back, refresh, and shared links keep them.
- A **denser grid** (smaller minimum card width), so more options are visible per screen. There's also a friendly "no products match… reset filters" message and visible yellow focus rings for keyboard users.

**Why it helps**
- **Shoppers:** "every hoodie in my size, cheapest first" is now 3 clicks instead of opening 25 product pages. Tested: Hoodies + L + Price low → high gives **18 of 25 hoodies**, matching a direct DB count, with the $45 Yale Sports Hoodie Tennis first.
- **Shareable:** a student can send a roommate a link to "M crewnecks under the cheapest price".
- **Business:** shoppers who can't find their size leave. Filtering to in-stock sizes keeps them on products they can actually buy.

**Where to see it:** http://localhost:5174/products?cat=Hoodies&size=L&sort=price-asc. Screenshot: `screenshots/p9_fe_toolbar_and_size_strips.jpg`.

---

## Agent/backend 1 — Suggested follow-up replies (quick-reply chips)

**What I added**
- **Contract:** `ChatReply.suggestions` (agent output) → `ChatResponse.suggestions` (API). The agent writes 2–3 short next questions **in the shopper's voice**, tailored to the conversation. `main.py` `clean_suggestions()` trims, de-duplicates, and caps them at 3.
- **Prompt rule** (`prompts/prompt.md`, "Suggested follow-ups"): they must be answerable with the tools, with no account, checkout, or off-topic suggestions, and none after a refusal.
- **Chat panel:** the chips appear under the **latest** reply (and under the greeting: "What hoodies do you have?", "Gifts under $50", "Show residential college gear"). **One tap sends it** as the shopper's message.

**Why it helps**
- **Shoppers** don't have to work out what to ask or type on a phone. The useful next step (other sizes, price, similar styles) is one tap away.
- **Softer, guided conversation:** after "L is sold out", the chips offer "Show other sizes" / "Is another hoodie in L?" instead of leaving the shopper at a dead end.
- **Business/safety:** chips keep conversations inside what the shop can answer (catalogue, sizes, prices), which means fewer off-topic or confused messages.

**Tested:** on the Fencing hoodie page, "Do you have this in a large?" returned the chips "Show other sizes · Is another hoodie in L? · Show similar fencing gear". Tapping **Show other sizes** sent it as a message, and the reply was "available in S and M, and only 2 are left in XL. XS, L, and XXL are sold out" (correct vs. the DB), with new chips "Show similar styles in L · How much is this hoodie?".

**Where to see it:** open the chat on any page. Screenshot: `screenshots/p9_be_suggestion_chip_clicked.jpg`.

---

## Agent/backend 2 — `find_alternatives` tool for sold-out sizes

**What I added**
- A new agent tool, `find_alternatives(product, size, max_price, limit)` (`backend/tools.py`). In **one call** it returns up to 6 similar products that **have the requested size in stock**, each with its live quantity and label for that size ("In stock (8)", "Only 2 left") and **why** it's similar. Ranking: same category, then shared name words and tags (college, sport, school, style, color), then closest price. Return types `AlternativesResult` / `Alternative` are in `backend/model.py`.
- **Prompt rule:** when the shopper's size is sold out, say so clearly first, then call `find_alternatives` and offer the top 2–3 as "similar styles that have your size" (as chat cards).
- Its prices and quantities are recorded for the Problem 6 output guard, so the agent still can't invent a number.

**Why it helps**
- **Shoppers:** "L is sold out" becomes "L is sold out, but the Crew, Squash and Volleyball Left Chest Hoodies have L". That's a real next step instead of a dead end.
- **Business:** this **saves the sale** on the most common failure in this catalogue (77 products have a sold-out size).
- **Faster and cheaper:** measured with `scripts/benchmark_alternatives.py` (same model and prompt, the same 3 sold-out questions, with vs. without the tool; full table in `p9_alternatives_benchmark.md`):

  | Agent | Model requests | Tokens | Seconds |
  |---|---|---|---|
  | **With** `find_alternatives` | **7** | **30,219** | **13.6** |
  | Without (search + get_stock) | 12 | 50,478 | 20.1 |
  | **Change** | **−42%** | **−40%** | **−32%** |

- **More accurate:** without the tool, the Fencing question got "78 matches, including the Basic Hoodie Big Yale, Baseball Left Chest Crewneck…" (crewnecks and quarter-zips as "alternatives" to a hoodie). With it, the reply was 3 similar hoodies, each with live L stock.

**Where to see it:** open http://localhost:5174/products/fencing-left-chest-hoodie, open the chat, and ask "Do you have this in a large?". Reply: "Size L is sold out… Similar styles available in L include the Crew Left Chest Hoodie, Squash Left Chest Hoodie, and Volleyball Left Chest Hoodie" plus 3 cards (their L stock is 8, 25, and 8 in the DB). Screenshot: `screenshots/p9_be_find_alternatives.jpg`.

---

## Checks

- All four features were verified in the running app (frontend :5174 → backend :8000) on 2026-10-24. Screenshots are in `output/screenshots/p9_*.jpg`.
- Data checks: toolbar count (18 hoodies in L) and alternative stock levels match direct DB queries.
- Regression: `scripts/test_problem6.py` re-run with all changes in place still gives **8/8** price and stock answers matching the DB.
- No DB writes are needed for these features (all reads use the working copy). Chats are still saved only for logged-in users (Problem 8).
