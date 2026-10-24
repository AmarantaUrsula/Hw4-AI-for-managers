import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <span className="brand-mark" aria-hidden>Y</span>
          <div>
            <p className="footer-title">Campus Customs</p>
            <p>Officially licensed Yale apparel, made for the people who wear it every day.</p>
          </div>
        </div>
        <nav className="footer-col" aria-label="Shop">
          <p className="footer-head">Shop</p>
          <Link to="/products?cat=Hoodies">Hoodies</Link>
          <Link to="/products?cat=Crewnecks">Crewnecks</Link>
          <Link to="/products?cat=Quarter-zips">Quarter-zips</Link>
          <Link to="/products?cat=T-shirts+%26+tees">Tees</Link>
        </nav>
        <div className="footer-col">
          <p className="footer-head">Visit</p>
          <p>57 Broadway</p>
          <p>New Haven, CT 06511</p>
        </div>
        <div className="footer-col">
          <p className="footer-head">Questions?</p>
          <p>Ask the chat (bottom right) about sizes, stock, and prices — it checks live inventory.</p>
        </div>
      </div>
      <p className="footer-fine">Lux et veritas — and a good sweatshirt. © Campus Customs</p>
    </footer>
  );
}
