import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/products", label: "Products" },
  { to: "/about", label: "About us" },
];

export default function NavBar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function onLogout() {
    await logout();
    navigate("/");
  }

  return (
    <>
      <div className="announce" role="note">
        <span>Fall ’26 on Old Campus</span>
        <span className="announce-dot" aria-hidden>✦</span>
        <span>Officially licensed Yale apparel</span>
        <span className="announce-dot" aria-hidden>✦</span>
        <span>57 Broadway, New Haven</span>
      </div>
    <header className="nav">
      <Link to="/" className="brand" aria-label="Campus Customs home">
        <span className="brand-mark" aria-hidden>Y</span>
        <span>
          Campus Customs
          <small>Est. on Broadway · New Haven, CT</small>
        </span>
      </Link>
      <nav className="nav-links">
        {links.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end}>
            {l.label}
          </NavLink>
        ))}
        {user ? (
          <>
            <span className="nav-user">Hi, {user.first_name}</span>
            <button className="nav-cta" onClick={onLogout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <NavLink to="/login">Log in</NavLink>
            <NavLink to="/signup" className="nav-cta">
              Create account
            </NavLink>
          </>
        )}
      </nav>
    </header>
    </>
  );
}
