import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Product, fetchProduct, formatPrice, stockLevel } from "../api";
import { SizeLegend } from "../components/SizeStrip";

function stockLabel(q: number) {
  if (q === 0) return "Sold out";
  if (q <= 5) return `Only ${q} left`;
  return "In stock";
}

// Same encoding as the card size strip: symbol + words, not color alone (Problem 9).
function stockShort(q: number) {
  const level = stockLevel(q);
  if (level === "out") return "✕ Sold out";
  if (level === "low") return `! Only ${q} left`;
  return `✓ ${q} left`;
}

export default function ProductDetail() {
  const { productId = "" } = useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [size, setSize] = useState<string | null>(null);

  useEffect(() => {
    setProduct(null);
    setError(null);
    setSize(null);
    fetchProduct(productId).then(setProduct).catch((e: Error) => setError(e.message));
  }, [productId]);

  if (error) {
    return (
      <section className="page">
        <p className="error">We couldn't find that product ({error}).</p>
        <Link to="/products">← Back to products</Link>
      </section>
    );
  }
  if (!product) return <section className="page"><p className="muted">Loading…</p></section>;

  const selected = product.inventory?.find((s) => s.size === size);

  return (
    <section className="page">
      <Link to="/products" className="back">← All products</Link>
      <div className="detail">
        <div className="detail-img">
          <img src={product.image_url} alt={product.name} />
        </div>
        <div className="detail-info">
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price big">{formatPrice(product.price)}</p>
          <p>{product.description}</p>

          <h3>Colors</h3>
          <div className="tags">
            {product.colors.map((c) => (
              <span key={c} className="tag">{c}</span>
            ))}
          </div>

          <h3>Size &amp; stock</h3>
          <SizeLegend />
          <div className="sizes">
            {product.inventory?.map((s) => (
              <button
                key={s.size}
                className={`size size-${stockLevel(s.quantity)} ${size === s.size ? "active" : ""}`}
                disabled={s.quantity === 0}
                onClick={() => setSize(s.size)}
                title={stockLabel(s.quantity)}
              >
                <strong>{s.size}</strong>
                <small>{stockShort(s.quantity)}</small>
              </button>
            ))}
          </div>
          <p className="muted">
            {selected ? `Size ${selected.size}: ${stockLabel(selected.quantity)}.` : `${product.total_stock} units in stock across all sizes.`}
          </p>
          <button className="btn" disabled title="Checkout comes in a later problem">
            Add to cart (coming soon)
          </button>

          <h3>Good to know</h3>
          <div className="tags">
            {product.search_tags.map((t) => (
              <span key={t} className="tag light">{t}</span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
