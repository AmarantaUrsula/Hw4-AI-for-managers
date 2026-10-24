import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Product, fetchProducts } from "../api";
import Leaves from "../components/Leaves";
import ProductCard from "../components/ProductCard";

const FEATURED = [
  "basic-hoodie-big-yale",
  "2025-yale-vs-harvard-t-shirt",
  "davenport-college-crewneck",
  "benjamin-franklin-1-4-zip",
];

// Hero collage: three real catalogue photos as tilted "polaroids".
const COLLAGE = [
  { id: "champion-reverse-weave-hoodie-1", caption: "Reverse weave, Cross Campus" },
  { id: "benjamin-franklin-1-4-zip", caption: "Quarter-zip, seminar ready" },
  { id: "2025-yale-vs-harvard-t-shirt", caption: "The Game, 2025" },
];

// "Shop the look": moments of a fall semester, each linked to a filtered Products page.
const LOOKS = [
  { title: "Library late nights", blurb: "Soft crewnecks for Sterling stacks and 2 a.m. p-sets.", img: "davenport-college-crewneck", to: "/products?cat=Crewnecks" },
  { title: "Crisp fall layers", blurb: "Quarter-zips that go from seminar to dinner.", img: "benjamin-franklin-1-4-zip", to: "/products?cat=Quarter-zips" },
  { title: "Game day", blurb: "Hoodies loud enough for the Bowl, warm enough for November.", img: "champion-reverse-weave-hoodie-1", to: "/products?cat=Hoodies" },
  { title: "Statement outerwear", blurb: "Jackets for walks down Hillhouse when the leaves turn.", img: "brooks-brothers-bomber-jacket-yale", to: "/products?cat=Jackets+%26+full-zips" },
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
      <section className="hero-wrap">
        <Leaves />
        <div className="hero">
          <div className="hero-text rise">
            <p className="eyebrow">Fall ’26 · Officially licensed Yale apparel</p>
            <h1>
              Wear Yale like <em>you mean it.</em>
            </h1>
            <p>
              Campus Customs makes the sweatshirts, tees, and quarter-zips that Yalies actually live in —
              through problem sets, late nights in the library, and every Harvard–Yale weekend. We keep it
              simple: good fabric, sharp prints, and designs that make you proud to put them on.
            </p>
            <div className="hero-actions">
              <Link to="/products" className="btn">Shop the collection</Link>
              <Link to="/about" className="btn ghost">Our story</Link>
            </div>
            <p className="hero-note">Not sure what fits? Ask the chat — it checks live sizes and stock.</p>
          </div>
          <div className="collage" aria-label="Featured pieces">
            {COLLAGE.map((c, i) => (
              <Link key={c.id} to={`/products/${c.id}`} className={`polaroid p${i + 1}`}>
                <img src={`/media/products/${c.id}.jpg`} alt={c.caption} />
                <span>{c.caption}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      <section className="page">
        <div className="section-head">
          <p className="eyebrow">Shop the look</p>
          <h2>Dressed for a New Haven fall</h2>
        </div>
        <div className="looks">
          {LOOKS.map((l) => (
            <Link key={l.title} to={l.to} className="look">
              <img src={`/media/products/${l.img}.jpg`} alt="" loading="lazy" />
              <div className="look-text">
                <h3>{l.title}</h3>
                <p>{l.blurb}</p>
                <span className="look-cta">Shop {l.title.toLowerCase()} →</span>
              </div>
            </Link>
          ))}
        </div>

        <div className="pillars">
          <div>
            <span className="pillar-icon" aria-hidden>❦</span>
            <h3>Made for Yalies</h3>
            <p>Every residential college, every varsity team, every grad and professional school — find the piece that says exactly where you belong.</p>
          </div>
          <div>
            <span className="pillar-icon" aria-hidden>✦</span>
            <h3>Built to last</h3>
            <p>Heavyweight fleece, soft tri-blends, and prints that hold up wash after wash. These are clothes for four years and the reunions after.</p>
          </div>
          <div>
            <span className="pillar-icon" aria-hidden>♥</span>
            <h3>Bulldog pride, gifted</h3>
            <p>Shopping for a proud Yale mom, dad, or grandparent? We have that too — the easiest way to bring family into the Bulldog story.</p>
          </div>
        </div>

        <div className="section-head">
          <p className="eyebrow">Student favorites</p>
          <h2>What’s walking around Old Campus</h2>
        </div>
        <div className="grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
        <p className="center">
          <Link to="/products" className="btn ghost">See the full collection →</Link>
        </p>
      </section>
    </>
  );
}
