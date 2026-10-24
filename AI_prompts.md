# HW4 — AI Prompts Log

This file records the prompts I typed into the vibe coder (Claude Code) for each problem in HW4. Each section has the problem number and title, at least one prompt I typed, and a follow-up prompt when one was needed, with one sentence on what the first prompt was missing. Prompts are quoted with small typo fixes. The exact wording of every prompt is in `hw4_log.txt`.

The proof that each problem is done correctly and completely is the running site, the database writes, and the screenshots. Each section lists its evidence.

---

## Problem 1: Vibe coder prompts

**Prompt I typed:**
> This is a new homework assignment and all the work should be done and documented in '/Users/Liza/Library/CloudStorage/OneDrive-YaleUniversity/AI for managers/hw4'

**Follow-up prompt:**
> This is Problem 1 of 13 in this assignment. It is called Problem 1: Vibe coder prompts. Create AI_prompts.md and keep it updated as we work. This file is the log of what I am typing here in the vibe coder. Put one section for each problem. Each section must include: the problem number and title; at least one prompt I typed; one follow-up prompt if it was needed (and one sentence on what was lacking in the first prompt); our running site, database writes, and screenshots are the evidence that this homework was completed correctly and completely.

**What the first prompt was missing:** It set up the hw4 folder but did not say which problem this was or that it needed an `AI_prompts.md` file with one section per problem.

**Evidence:** This file (`hw4/AI_prompts.md`) and the full prompt/response log in `hw4/hw4_log.txt`.

---

## Problem 2: Analyze the database

**Prompt I typed:**
> Problem 2: Analyze the database. Look at the database data/campus_customs.db and understand the fields of each table. At minimum we need to understand catalogue, inventory, and users. Start the file output/harness.md. Write down each table and its fields, and one short line on why each field matters for the shop or the chatbot. We will keep growing this harness file later in later problems (models, tools, safety, specs).

**Follow-up prompt:** None needed. The first prompt named the database, the tables, the output file, and the format.

**Evidence:** `output/harness.md`, section 1 "Data". It covers all 4 tables (catalogue 102 rows, inventory 612, users 3, chat_messages 22), with every field, an example value, and why the field matters. The row counts and checks were read directly from `data/campus_customs.db` (no database writes in this problem).

---

## Problem 3: Build the Campus Customs website

**Prompt I typed:**
> Problem 3: Build the campus customs website. Scaffold a React + Vite + TypeScript front end for Campus Customs. Put a nav bar at the top that links to the main pages: Home, Products, About us, Log in, Create account. Pull Campus Customs-style wording from yalebulldogblue.com for Home and About Us, but write these pages in my voice — straightforward but genuinely warm about the importance and quality of these products, especially for Yalies. Do not copy the original site text verbatim. On the Products page, show product images from the catalogue (use the image paths in the database) with the basic product info (name, price, short description). Make each product open a single-item page (large image on one side, full product text on the other (e.g. description, price, size/stock when we have them)). Clicking a card on the Products page should take the shopper there. Add a chat interface in the bottom right of the site (a floating chat panel is fine). It does not need to talk to an agent yet — a stub that will call the backend later is enough for this problem. You will need a small API soon to read the database. It is fine to start a simple FastAPI app in backend/main.py just to serve products and images, then grow it into the agent backend in Problem 5.

**Follow-up prompt:** None needed. The prompt listed every page, the voice, the product card and detail layouts, the chat stub, and the backend file.

**Evidence:**
- Running site at http://localhost:5174 (frontend) and http://localhost:8001 (FastAPI). Run steps are in `README.md`.
- Screenshots in `output/screenshots/`: `p3_home.jpg`, `p3_products.jpg` (102 products with DB images), `p3_product_detail.jpg` (Basic Hoodie Big Yale, $68, stock XS 15 / S 5 / M 5 / L 8 / XL 2 / XXL 25, matching `inventory`), `p3_about.jpg`, `p3_create_account.jpg`, `p3_chat_stub.jpg` (chat panel getting the `/api/chat` stub reply).
- Database writes: none by design. The API opens the DB read-only, and after testing `users` still has 3 rows and `chat_messages` still has 22.
- API and page reference: `output/harness.md`, section 2.

---

## Problem 4: Create account and login

**Prompt I typed:**
> Problem 4: create account and login. Build a normal create-account/login flow. Create account: first name, last name, email, password, confirm password. Log in: email and password. New accounts go into the users table. Make sure to store passwords securely so hackers (human or AI) cannot access them. The seed database already has a test user you can use while building: email test@campuscustoms.yale.edu, password: password, hash function: PBKDF2-HMAC-SHA256, 120,000 iterations (stored as pbkdf2_sha256$salt$hash). How login checks a password:

**Follow-up prompt:**
> can you confirm you can log in as that user and that a brand new account also works (just make it up)?

**What the first prompt was missing:** It asked for the flow and the secure storage but never asked for proof that both a seed-user login and a brand-new signup actually work end to end.

**Second follow-up prompt:**
> Update output/harness.md with how auth works (what you store for a user and how passwords are protected).

**Third follow-up prompt:**
> Do you need more details on how login checks a password to build this properly or are you good?

**Fourth follow-up prompt:**
> ok thanks. Please read the salt out of the stored string (the middle piece) - do not make a new one at login. Anything else you need guidance on?

**Fifth follow-up prompt:**
> Write to a working copy instead (data/campus_customs_new.db) and keep campus_customs.db untouched, with a reset script like HW5.

**Evidence:**
- Running site: Log in and Create account at http://localhost:5174. The nav changes to "Hi, <first name> | Log out" once logged in.
- Database write: a new row in `users` in the working copy `data/campus_customs_new.db` (id 4, Grace Bulldog, grace.bulldog@yale.edu, created 2026-10-24) with a `pbkdf2_sha256$<32-char salt>$<64-hex>` hash and no plain-text password. Independently re-checked in `output/p4_users_check.txt` (both user 1 and user 4 MATCH). All writes now go to the working copy `data/campus_customs_new.db`. The original `data/campus_customs.db` was restored byte-for-byte (3 users), made read-only, and is never opened by the app. `./reset_db.sh` resets the working copy.
- Screenshots in `output/screenshots/`: `p4_login_wrong_password.jpg`, `p4_login_test_user.jpg` ("Hi, Test"), `p4_signup_mismatch.jpg`, `p4_new_account_logged_in.jpg` ("Hi, Grace").
- How auth works, what is stored for each user, and how passwords are protected: `output/harness.md`, section 3 ("How auth works (summary)", "What we store for a user", "How passwords are protected (at a glance)", then full details).

---

## Problem 5: PydanticAI agent backend

**Prompt I typed:**
> Problem 5: PydanticAI agent backend. Build the shop chatbot as a PydanticAI agent behind FastAPI, plugged into the front-end chat widget. Put the API app in backend/main.py — that is the file you run with Uvicorn. Keep the agent as these four files next to it: backend/prompts/prompt.md — system prompt (grow this same file later); backend/agent.py — agent entry/wiring; backend/tools.py — tools the agent can call; backend/model.py — Pydantic/PydanticAI structured types. In main.py, expose a chat route so a message from the website returns a reply from the agent (and whatever else you need for products/auth). You will need your AI model API key for the agent. Put Campus Customs voice and safety basics into prompts/prompt.md (you will expand tools and safety later). Start or update types in model.py for chat replies/product cards as needed. In output/harness.md note how the front end talks to FastAPI and how the agent is loaded (prompt file + model). Make sure the backend runs from the backend/ folder like this: uvicorn main:app --reload --port 8000

**Follow-up prompt:**
> Yes, stop the HW5 backend on port 8000 and run the HW4 backend there with uvicorn main:app --reload --port 8000.

**What the first prompt was missing:** It required port 8000 but didn't say what to do when that port was already taken by my HW5 backend, so I had to confirm stopping it.

**Evidence:**
- Running site: the HW4 backend runs from `backend/` with `uvicorn main:app --reload --port 8000`, and the chat panel (bottom right) answers through the PydanticAI agent (gpt-6-luna via Portkey) with live prices and stock, and shows clickable product cards.
- Database writes: logged-in chats are saved to `chat_messages` in the working copy (rows 23–28, user 4 Grace, assistant rows include `products_json`). Guest chats are not saved. The original DB still has 22 chat rows.
- Screenshots: `output/screenshots/p5_chat_logged_in_cards.jpg` (Grace, Davenport crewneck card, S sold out), `p5_chat_guest_cards.jpg` (guest gift search with 4 cards, then a follow-up), `p5_chat_port8000_size_fallback.jpg` (on port 8000: size S sold out, crewneck card shown with available sizes).
- Test table, data flow, and agent loading: `output/harness.md`, section 4.

---

## Problem 6: Product info and stock

**Prompt I typed:**
> Problem 6: product info and stock. Give the agent tools that look up real information from campus_customs.db: product description, price, how many are in stock (by size when the customer asks). The agent must use the database — it must NOT invent prices or quantities. If a size is out of stock, say so clearly. Expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. Add or update return types in models.py. In output/harness.md, list each tool and explain which model fields you chose for lookup results and why.

**Follow-up prompt:** None needed.

**Evidence:**
- Running site: on the Fencing Left Chest Hoodie page, the chat answered "$68.00. Size L is sold out; it's available in S, M, and XL" and then "Only 2 left in size XL", matching the product page (`output/screenshots/p6_chat_price_stock_soldout.jpg`).
- Database: tools read `catalogue.price` and `inventory.quantity` live from the working copy. `output/p6_tool_tests.md` shows 8 real questions, the tools called for each, and every number in each reply checked against the DB (8/8 pass). There are no DB writes in this problem; the lookups are read-only.
- Guard: `output/p6_guard_test.txt` shows a made-up "$49.99 / only 3 left" being rejected and corrected to "$68.00 / only 2 left".
- Tool list and why each return-type field was chosen: `output/harness.md`, section 5.

---

## Problem 7: Chat search that updates the page

**Prompt I typed:**
> Problem 7: chat search that updates the page. Now we will add a neat feature to that site. When a customer asks about a type of item — e.g. what hoodies do you have? — the agent should search the catalog and the website should dynamically show those matching items as product cards (image, name, price, short info). We want this in part because it looks really cool. This is an API contract: the agent returns structured product matches and then the front end renders them on the website. After the dynamic product cards are loaded by this new feature, make sure the same single item page behavior you built in Problem 3 still works: each product card — including the ones the chat just put on the page — should still open that detail view (large image + full info) when clicked. Update prompts/prompt.md and output/harness.md so it is clear how search results reach the page.

**Follow-up prompt:** None needed.

**Evidence:**
- Running site: "What hoodies do you have?" on the Home page filled the page with a "From your chat · Yale Hoodies (27)" grid of product cards (`output/screenshots/p7_chat_search_page_cards.jpg`). Clicking a card the chat put on the page opened the Problem 3 detail page with a large image and full info (`p7_card_opens_detail.jpg`). Asking from a product page moved to /products with "Quarter-zips (11)" (`p7_quarter_zips_on_products_page.jpg`). Narrowing to "grey ones under $60" updated the page to 1 card, and a price question left the page unchanged.
- Database: page cards are rebuilt live from `catalogue` + `inventory` for exactly the products `search_products` matched (read-only; no DB writes in this problem).
- API contract and data flow: `output/harness.md`, section 6. Prompt rules: "Browsing searches → product cards on the page" in `backend/prompts/prompt.md`.

---

## Problem 8: Customer memory

**Prompt I typed:**
> Problem 8: Customer memory. When a shopper is logged in, save their chat history in the database in an appropriate table and reload it when they return. The agent should know who is chatting (name, email) — put that in agent deps (or an equivalent clear pattern) and/or tools the agent can call. Also pass enough page context that if someone is on a product page and asks "do you have this in pink?" the agent knows which item they mean. Hint: you can put code into the agent context. Guests can still chat, but history only needs to persist for logged-in users. Document in output/harness.md: how user chat history is stored, what customer fields the agent sees, and how page context is passed.

**Follow-up prompt:** None needed.

**Evidence:**
- Running site: logged in as Grace on the Davenport College Crewneck page, "Do you have this in pink?" was answered about that crewneck (`output/screenshots/p8_this_in_pink_logged_in.jpg`). After a full browser reload, her chat came back, and "the crewneck I was looking at earlier… in a medium?" was answered from her saved history: "only 5 left" (`p8_memory_after_reload.jpg`). As a guest on the Fencing hoodie page, "this" also resolved correctly.
- Database writes: logged-in turns are saved in `chat_messages` (user_id 4, 14 rows); guest chats are not saved. Other users only see their own history. The original DB still has 22 chat rows.
- Docs: `output/harness.md`, section 7 (history storage, customer fields the agent sees, page context flow, tests).

---

## Problem 9: Usability improvements

**Prompt I typed:**
> Problem 9: usability improvements. Now that the core shop works, improve it. Choose and implement: 2 front end usability improvements; 2 agent/backend usability improvements. Front end improvements are things that make the site look better and easier to use. For example, ensure color blind friendly color palettes, organize information relatively densely so people can see options and functionality easily, and ensure design elements are on brand for a cohesive visual experience. Agent/backend improvements are things that make the agent output better, more accurate or softer. There could be new agent tools that make the agent run faster or cheaper. Write output/usability.md before or as you build. For each improvement, say: what you added; why it helps a Campus Customs shopper or the business. Then make sure all improvements actually show up in the running app because graders will read the write up and look for the features.

**Follow-up prompt:** None needed.

**Evidence:**
- Running site: (1) color-blind-safe size strips on every card + ✓/!/✕ size buttons; (2) sticky Products toolbar with My size / Sort / Hide sold out saved in the URL; (3) quick-reply chips in the chat; (4) the chat offers in-stock alternatives when a size is sold out. All verified in the browser: `output/screenshots/p9_*.jpg` (toolbar + strips, product page size buttons, grayscale check, suggestion chip clicked, find_alternatives).
- Database: toolbar count (18 hoodies with L in stock) and alternative stock levels match direct DB queries (read-only).
- Measured: `output/p9_alternatives_benchmark.md`. find_alternatives cut model requests 42%, tokens 40%, and time 32% on sold-out questions. Problem 6 tests still 8/8.
- Write-up: `output/usability.md` (what / why / where to see each improvement).

---

## Checkpoint: push to GitHub (after Problem 9)

**Prompt I typed:**
> Before we proceed with the rest of the problems let's push what we have so far to GitHub. We can do another push when the project is complete. Put the code in the hw4 folder and push it to a public GitHub repository. Do not put my real .env, campus_customs.db or products images in the GitHub repo. Use .gitignore; include .env.example with placeholders only. This image shows the expected file layout. The agent itself is four files under backend/: prompts/prompt.md, agent.py, tools.py and model.py. README.md should explain how to run the front end and back end after placing the data pack.

**Follow-up prompt:** None needed.

**Evidence:** public repo https://github.com/AmarantaUrsula/Hw4-AI-for-managers (branch `main`). `.gitignore` excludes `.env`, `data/` (database + images), the session secret, and the local test-password file; `.env.example` has placeholders only; `requirements.txt` and `README.md` (place data pack → `.env` → backend → frontend) added. All staged files were scanned for the real key, session secret, test password, and password hashes before pushing (none found).

**Follow-up prompt:**
> Rename backend/model.py to backend/models.py to match the layout image, update all imports and docs, test, and push.

**What the first prompt was missing:** It named the types file `model.py` while the layout image showed `models.py`, so the two didn't agree and the file had to be renamed to match the image.
