# HW4 — Campus Customs shop + AI shopping assistant

A Yale apparel shop for **Campus Customs**. It has a React + Vite + TypeScript website and a FastAPI backend with a **PydanticAI shopping agent** in the chat panel. The agent answers questions from the live catalogue and inventory, never invents prices or stock, remembers logged-in customers, knows which product page you're on, and fills the page with product cards when you ask "what hoodies do you have?".

## Repository layout

```
hw4/
├── AI_prompts.md            # prompts typed into the vibe coder, one section per problem
├── requirements.txt         # backend Python packages
├── .env.example             # settings template (copy to .env; placeholders only)
├── .gitignore
├── README.md
├── reset_db.sh              # reset the working-copy database to the original
├── data/                    # ← put the data pack here (NOT in the repo, see data/README.md)
├── frontend/                # Vite React TypeScript app
├── backend/
│   ├── main.py              # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py             # agent entry/wiring (loads prompt + model, context, output guards)
│   ├── model.py             # Pydantic / PydanticAI structured types
│   ├── tools.py             # tools the agent can call
│   ├── prompts/prompt.md    # system prompt
│   ├── auth.py              # create account / log in (PBKDF2 password hashing)
│   └── db.py                # database paths: original vs working copy
├── scripts/                 # evidence scripts (tool tests, benchmark)
└── output/
    ├── harness.md           # data, API, agent, tools, memory, page context — the reference doc
    ├── usability.md         # Problem 9 usability improvements
    ├── screenshots/         # evidence screenshots per problem (pN_*.jpg)
    └── *.md / *.txt         # test results
```

The agent is the four files `backend/prompts/prompt.md`, `backend/agent.py`, `backend/tools.py` and `backend/model.py`, next to `backend/main.py`.

## 1. Place the data pack

The database and product images are **not** in this repo. Copy them into `data/`:

```
hw4/data/campus_customs.db
hw4/data/products/*.jpg        (102 images)
```

The original `campus_customs.db` is never modified. On first start the backend copies it to `data/campus_customs_new.db` (the **working copy**), and all reads and writes (new accounts, saved chats) go there. To start fresh at any time, run this from `hw4/`:

```bash
./reset_db.sh
```

## 2. Settings (.env)

```bash
cp .env.example .env
```

Then edit `.env` and set `PORTKEY_API_KEY` to your own Portkey key. `PORTKEY_MODEL` is `gpt-6-luna`. `.env` is gitignored.

## 3. Run the backend (FastAPI + agent)

Python 3.13:

```bash
pip install -r requirements.txt
cd backend
uvicorn main:app --reload --port 8000
```

Check it: http://localhost:8000/api/health → `{"status":"ok","products":102}`. API docs: http://localhost:8000/docs.

> Uvicorn's `--reload` only watches `.py` files. After editing `prompts/prompt.md`, restart it (or save any `.py` file).

## 4. Run the frontend (React + Vite + TypeScript)

In a second terminal (Node 20+):

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5174**. Vite forwards `/api` and `/media` to the backend on port 8000.

## 5. Try it

- **Log in** with the seed test user: `test@campuscustoms.yale.edu` / `password`. Or **Create account** (stored with PBKDF2-SHA256, 120,000 iterations).
- Open the **💬 Chat** button (bottom right):
  - "What hoodies do you have?" — the page fills with matching product cards
  - on a product page: "Do you have this in pink?" / "Is this in a large?" — it uses the product on screen, says clearly if a size is sold out, and suggests similar items in your size
  - "How much is the Basic Hoodie Big Yale?" — exact price from the database
- **Products** page: filter by "My size", sort by price, hide sold out. Each card shows color-blind-safe size availability.

## Docs

- `output/harness.md` covers the data model, API, how the agent is loaded, every tool and its return types, how chat history and customer and page context reach the agent, and the test results.
- `output/usability.md` describes the four usability improvements and where to see them.
- `AI_prompts.md` lists the prompts used to build this, by problem.
