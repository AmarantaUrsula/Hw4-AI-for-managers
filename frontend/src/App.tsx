import { useEffect } from "react";
import { Route, Routes, useLocation, useMatch } from "react-router-dom";
import NavBar from "./components/NavBar";
import Footer from "./components/Footer";
import ChatWidget from "./components/ChatWidget";
import ChatResults from "./components/ChatResults";
import Home from "./pages/Home";
import Products from "./pages/Products";
import ProductDetail from "./pages/ProductDetail";
import About from "./pages/About";
import Login from "./pages/Login";
import Signup from "./pages/Signup";

// New page → start at the top (single-page apps keep the old scroll position otherwise).
// Filter changes on the same page (?size=…) keep the scroll, so the toolbar doesn't jump.
function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [pathname]);
  return null;
}

export default function App() {
  // Chat results show on every page except the single-item page, which keeps its own layout;
  // they are still there when the shopper goes back.
  const onDetailPage = useMatch("/products/:productId");
  return (
    <div className="app">
      <ScrollToTop />
      <NavBar />
      <main className="main">
        {!onDetailPage && <ChatResults />}
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="*" element={<p className="page">Page not found.</p>} />
        </Routes>
      </main>
      <Footer />
      <ChatWidget />
    </div>
  );
}
