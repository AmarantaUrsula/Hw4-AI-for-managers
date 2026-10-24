import { useEffect, useRef } from "react";
import { useChatResults } from "../chatResults";
import ProductCard from "./ProductCard";

// The on-page product grid filled by chat searches (Problem 7). Each card is the same
// ProductCard used on the Products page, so clicking it opens /products/:productId.
export default function ChatResults() {
  const { results, version, clear } = useChatResults();
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (results) ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [version]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!results) return null;
  return (
    <section ref={ref} key={version} className="chat-results" aria-live="polite" aria-label="Chat search results">
      <div className="chat-results-head">
        <div>
          <p className="eyebrow">💬 From your chat</p>
          <h2>
            {results.title} <span className="count">({results.total})</span>
          </h2>
          <p className="muted">Search: {results.query}</p>
        </div>
        <button className="btn ghost" onClick={clear}>
          Clear results
        </button>
      </div>
      <div className="grid">
        {results.products.map((p, i) => (
          <div key={p.product_id} className="pop-in" style={{ animationDelay: `${Math.min(i, 12) * 40}ms` }}>
            <ProductCard product={p} />
          </div>
        ))}
      </div>
    </section>
  );
}
