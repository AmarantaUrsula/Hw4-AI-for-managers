import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Product, fetchProducts } from "../api";
import ProductCard from "../components/ProductCard";

const FEATURED = [
  "basic-hoodie-big-yale",
  "2025-yale-vs-harvard-t-shirt",
  "davenport-college-crewneck",
  "benjamin-franklin-1-4-zip",
];

export default function Home() {
  const [featured, setFeatured] = useState<Product[]>([]);

  useEffect(() => {
    fetchProducts()
      .then((all) => setFeatured(FEATURED.map((id) => all.find((p) => p.product_id === id)).filter((p): p is Product => !!p)))
      .catch(() => setFeatured([]));
  }, []);

  return (
    <>
      <section className="hero">
        <div className="hero-text">
          <p className="eyebrow">Officially licensed Yale apparel</p>
          <h1>Wear Yale like you mean it.</h1>
          <p>
            Campus Customs makes the sweatshirts, tees, and quarter-zips that Yalies actually live in —
            through problem sets, late nights in the library, and every Harvard–Yale weekend. We keep it
            simple: good fabric, sharp prints, and designs that make you proud to put them on.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn">Shop the collection</Link>
            <Link to="/about" className="btn ghost">Our story</Link>
          </div>
        </div>
        <img className="hero-img" src="/media/products/basic-hoodie-big-yale.jpg" alt="Navy Yale hoodie" />
      </section>

      <section className="page">
        <div className="pillars">
          <div>
            <h3>Made for Yalies</h3>
            <p>Every residential college, every varsity team, every grad and professional school — find the piece that says exactly where you belong.</p>
          </div>
          <div>
            <h3>Built to last</h3>
            <p>Heavyweight fleece, soft tri-blends, and prints that hold up wash after wash. These are clothes for four years and the reunions after.</p>
          </div>
          <div>
            <h3>Bulldog pride, gifted</h3>
            <p>Shopping for a proud Yale mom, dad, or grandparent? We have that too — the easiest way to bring family into the Bulldog story.</p>
          </div>
        </div>

        <h2>Student favorites</h2>
        <div className="grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
        <p className="center">
          <Link to="/products" className="btn ghost">See all products →</Link>
        </p>
      </section>
    </>
  );
}
