// Thin client for the FastAPI backend (backend/main.py). Vite proxies /api and /media to the backend on :8000.

export interface StockRow {
  size: string;
  quantity: number;
}

export interface Product {
  product_id: string;
  name: string;
  garment_type: string;
  description: string;
  colors: string[];
  search_tags: string[];
  image_file_path: string;
  image_url: string;
  price: number;
  total_stock: number;
  inventory?: StockRow[];
  size_stock?: Record<string, number>; // {"XS": 0, "S": 12, ...} — Problem 9 size strip
}

// Product card as returned by /api/chat (backend model.ProductCard).
export interface ChatProduct {
  product_id: string;
  name: string;
  price: number;
  image_url: string;
  url?: string;
  total_stock?: number;
  category?: string;
  short_description?: string;
  size_stock?: Record<string, number>;
}

// Chat search results the website shows on the page (backend model.PageResults, Problem 7).
export interface PageResults {
  title: string;
  query: string;
  total: number;
  products: ChatProduct[];
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

// POST /api/chat response (backend model.ChatResponse) — the chat -> page API contract.
export interface ChatReply {
  reply: string;
  products: ChatProduct[];
  page: PageResults | null;
  suggestions: string[]; // Problem 9 quick-reply chips
}

export interface ChatHistoryMessage extends ChatTurn {
  products: ChatProduct[];
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const fetchProducts = () => getJson<Product[]>("/api/products");

export const fetchProduct = (id: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(id)}`);

// What page the shopper is on (Problem 8), so "do you have this in pink?" on a product page
// means that product. The backend looks the product up from the path.
export interface PageContext {
  path: string;
  results_title?: string | null;
}

// history is only used by the backend when the shopper is not logged in.
export async function sendChat(message: string, history: ChatTurn[], page: PageContext): Promise<ChatReply> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, page }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? `${res.status} ${res.statusText}`);
  return data as ChatReply;
}

export const fetchChatHistory = () =>
  getJson<{ messages: ChatHistoryMessage[] }>("/api/chat/history").then((d) => d.messages);

export const formatPrice = (price: number) => `$${price.toFixed(2)}`;

// garment_type has ~22 spellings in the DB; fold them into shopper-friendly categories.
export function category(garmentType: string): string {
  const t = garmentType.toLowerCase();
  if (t.includes("quarter-zip")) return "Quarter-zips";
  if (t.includes("jacket") || t.includes("full-zip")) return "Jackets & full-zips";
  if (t.includes("hood")) return "Hoodies";
  if (t.includes("crewneck sweatshirt") || t === "crewneck" || t.includes("mockneck")) return "Crewnecks";
  if (t.includes("t-shirt") || t.includes("shirt")) return "T-shirts & tees";
  return "Other";
}

export function shortDescription(text: string, max = 90): string {
  if (text.length <= max) return text;
  return text.slice(0, text.lastIndexOf(" ", max)) + "…";
}

// ---------- auth (Problem 4) ----------

export interface User {
  id: number;
  first_name: string;
  last_name: string;
  name: string;
  email: string;
}

export interface SignupInput {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

// Session lives in an HttpOnly cookie set by the backend; the browser sends it automatically.
async function postAuth<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`/api/auth/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    credentials: "same-origin",
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail ?? `${res.status} ${res.statusText}`);
  return data as T;
}

export const signup = (input: SignupInput) => postAuth<{ user: User }>("signup", input).then((d) => d.user);
export const login = (email: string, password: string) =>
  postAuth<{ user: User }>("login", { email, password }).then((d) => d.user);
export const logout = () => postAuth<{ ok: boolean }>("logout");
export const fetchMe = () => getJson<{ user: User | null }>("/api/auth/me").then((d) => d.user);

// ---------- stock levels (Problem 9) ----------

export const SIZES = ["XS", "S", "M", "L", "XL", "XXL"];
export const LOW_STOCK = 5;
export type StockLevel = "in" | "low" | "out";

export function stockLevel(quantity: number): StockLevel {
  if (quantity <= 0) return "out";
  return quantity <= LOW_STOCK ? "low" : "in";
}
