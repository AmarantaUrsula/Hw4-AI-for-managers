import { Link } from "react-router-dom";
import { Product, formatPrice, shortDescription } from "../api";
import SizeStrip from "./SizeStrip";

// Works for catalogue products (Products/Home) and chat search results (ChatResults):
// both link to the same single-item page, /products/:productId.
type CardProduct = Pick<Product, "product_id" | "name" | "price" | "image_url"> & {
  total_stock?: number;
  description?: string;
  short_description?: string;
  size_stock?: Record<string, number>;
};

export default function ProductCard({ product }: { product: CardProduct }) {
  const blurb = product.short_description ?? (product.description ? shortDescription(product.description) : "");
  return (
    <Link to={`/products/${product.product_id}`} className="card">
      <div className="card-img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {product.total_stock === 0 && <span className="badge sold">✕ Sold out</span>}
      </div>
      <div className="card-body">
        <h3>{product.name}</h3>
        <p className="price">{formatPrice(product.price)}</p>
        {blurb && <p className="muted">{blurb}</p>}
        <SizeStrip sizeStock={product.size_stock} compact />
      </div>
    </Link>
  );
}
