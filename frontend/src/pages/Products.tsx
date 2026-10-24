import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Product, SIZES, category, fetchProducts } from "../api";
import ProductCard from "../components/ProductCard";
import { SizeLegend } from "../components/SizeStrip";

const CATEGORIES = ["All", "Hoodies", "Crewnecks", "T-shirts & tees", "Quarter-zips", "Jackets & full-zips"];
const SORTS = {
  featured: "Featured",
  "price-asc": "Price: low → high",
  "price-desc": "Price: high → low",
  name: "Name A–Z",
  stock: "Most in stock",
} as const;
type SortKey = keyof typeof SORTS;

// Problem 9: a dense, sticky toolbar. Every filter lives in the URL (?q=&cat=&size=&sort=&instock=1)
// so Back, refresh and shared links keep it.
export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useSearchParams();

  const query = params.get("q") ?? "";
  const cat = params.get("cat") ?? "All";
  const size = params.get("size") ?? "";
  const sort = (params.get("sort") ?? "featured") as SortKey;
  const inStockOnly = params.get("instock") === "1";

  const set = (key: string, value: string | null) =>
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (value === null || value === "" || (key === "cat" && value === "All") || (key === "sort" && value === "featured")) next.delete(key);
        else next.set(key, value);
        return next;
      },
      { replace: key === "q" },
    );

  useEffect(() => {
    fetchProducts().then(setProducts).catch((e: Error) => setError(e.message));
  }, []);

  const shown = useMemo(() => {
    if (!products) return [];
    const q = query.trim().toLowerCase();
    const list = products.filter((p) => {
      if (cat !== "All" && category(p.garment_type) !== cat) return false;
      if (size && !((p.size_stock?.[size] ?? 0) > 0)) return false;
      if (inStockOnly && p.total_stock === 0) return false;
      if (!q) return true;
      return [p.name, p.description, p.garment_type, ...p.colors, ...p.search_tags].join(" ").toLowerCase().includes(q);
    });
    const by: Record<SortKey, (a: Product, b: Product) => number> = {
      featured: () => 0,
      "price-asc": (a, b) => a.price - b.price || a.name.localeCompare(b.name),
      "price-desc": (a, b) => b.price - a.price || a.name.localeCompare(b.name),
      name: (a, b) => a.name.localeCompare(b.name),
      stock: (a, b) => b.total_stock - a.total_stock,
    };
    return [...list].sort(by[sort] ?? by.featured);
  }, [products, query, cat, size, sort, inStockOnly]);

  const filtered = query || cat !== "All" || size || inStockOnly || sort !== "featured";

  return (
    <section className="page">
      <h1>Products</h1>
      <div className="toolbar" role="search">
        <div className="toolbar-row">
          <input
            className="search"
            placeholder="Search by name, college, sport, color…"
            value={query}
            onChange={(e) => set("q", e.target.value)}
            aria-label="Search products"
          />
          <label className="tb-select">
            Sort
            <select value={sort} onChange={(e) => set("sort", e.target.value)}>
              {Object.entries(SORTS).map(([k, label]) => (
                <option key={k} value={k}>{label}</option>
              ))}
            </select>
          </label>
          <label className="tb-check">
            <input type="checkbox" checked={inStockOnly} onChange={(e) => set("instock", e.target.checked ? "1" : null)} />
            Hide sold out
          </label>
        </div>
        <div className="toolbar-row">
          <div className="chips" aria-label="Category">
            {CATEGORIES.map((c) => (
              <button key={c} className={c === cat ? "chip active" : "chip"} onClick={() => set("cat", c)} aria-pressed={c === cat}>
                {c}
              </button>
            ))}
          </div>
        </div>
        <div className="toolbar-row">
          <span className="tb-label">My size</span>
          <div className="chips" aria-label="Show only products with this size in stock">
            <button className={!size ? "chip active" : "chip"} onClick={() => set("size", null)} aria-pressed={!size}>Any</button>
            {SIZES.map((s) => (
              <button key={s} className={s === size ? "chip active" : "chip"} onClick={() => set("size", s === size ? null : s)} aria-pressed={s === size}>
                {s}
              </button>
            ))}
          </div>
          <SizeLegend />
        </div>
        <div className="toolbar-row tb-status">
          {products && (
            <span aria-live="polite">
              <strong>{shown.length}</strong> of {products.length} products
              {size && <> · size <strong>{size}</strong> in stock</>}
            </span>
          )}
          {filtered && (
            <button className="link-btn" onClick={() => setParams(new URLSearchParams())}>
              Reset filters
            </button>
          )}
        </div>
      </div>
      {error && <p className="error">Couldn't load products ({error}). Is the backend running on :8000?</p>}
      {!products && !error && <p className="muted">Loading products…</p>}
      {products && shown.length === 0 && (
        <p className="muted">No products match these filters. Try another size or <button className="link-btn" onClick={() => setParams(new URLSearchParams())}>reset filters</button>.</p>
      )}
      <div className="grid">
        {shown.map((p) => (
          <ProductCard key={p.product_id} product={p} />
        ))}
      </div>
    </section>
  );
}
