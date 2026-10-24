import { FormEvent, useEffect, useRef, useState } from "react";
import { Link, useLocation, useMatch, useNavigate } from "react-router-dom";
import { ChatProduct, ChatTurn, fetchChatHistory, formatPrice, sendChat } from "../api";
import { useAuth } from "../auth";
import { useChatResults } from "../chatResults";

interface Msg extends ChatTurn {
  products?: ChatProduct[];
  pageNote?: string;
  suggestions?: string[];
}

const greeting = (name?: string): Msg => ({
  role: "assistant",
  content: `Hi${name ? ` ${name}` : ""}! I'm the Campus Customs assistant. Ask me about products, sizes, colors, or what's in stock.`,
  suggestions: ["What hoodies do you have?", "Gifts under $50", "Show residential college gear"],
});

// Floating chat panel. Messages go to POST /api/chat, which runs the PydanticAI shop agent.
// Logged-in shoppers get their saved chat back; guests' history lives only in this panel.
// Every message also sends the current page path so the agent knows what "this" is.
export default function ChatWidget() {
  const { user } = useAuth();
  const chatResults = useChatResults();
  const navigate = useNavigate();
  const onDetailPage = useMatch("/products/:productId");
  const location = useLocation();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([greeting()]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  // Reset when the shopper logs in or out; restore a logged-in shopper's saved chat.
  useEffect(() => {
    setMessages([greeting(user?.first_name)]);
    if (!user) return;
    fetchChatHistory()
      .then((saved) => saved.length && setMessages([greeting(user.first_name), ...saved]))
      .catch(() => {});
  }, [user]);

  // Jump straight to the latest message when the panel opens (e.g. restored history);
  // scroll smoothly as new messages arrive.
  useEffect(() => {
    if (open) endRef.current?.scrollIntoView({ behavior: "auto" });
  }, [open]);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    await send(draft);
  }

  async function send(raw: string) {
    const text = raw.trim();
    if (!text || busy) return;
    const history: ChatTurn[] = messages.slice(1).map(({ role, content }) => ({ role, content }));
    setDraft("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setBusy(true);
    try {
      const page = { path: location.pathname, results_title: onDetailPage ? null : chatResults.results?.title };
      const res = await sendChat(text, history, page);
      let pageNote: string | undefined;
      if (res.page) {
        // Put the search results on the page as product cards (Problem 7).
        chatResults.show(res.page);
        if (onDetailPage) navigate("/products");
        pageNote = `Showing ${res.page.total} ${res.page.title.toLowerCase()} on the page`;
      }
      setMessages((m) => [...m, { role: "assistant", content: res.reply, products: res.products, pageNote, suggestions: res.suggestions }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "Sorry, I couldn't reach the shop right now. Please try again." },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat">
      {open && (
        <section className="chat-panel" aria-label="Chat with Campus Customs">
          <header className="chat-head">
            <span className="chat-avatar" aria-hidden>Y</span>
            <div className="chat-title">
              <strong>Campus Customs desk</strong>
              <small><span className="live-dot" aria-hidden /> Checks live sizes &amp; stock</small>
            </div>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-body">
            {messages.map((m, i) => (
              <div key={i} className={`chat-row ${m.role}`}>
                <div className={`chat-msg ${m.role}`}>{m.content}</div>
                {m.pageNote && <div className="chat-page-note">📋 {m.pageNote}</div>}
                {!!m.products?.length && (
                  <div className="chat-cards">
                    {m.products.map((p) => (
                      <Link key={p.product_id} to={p.url ?? `/products/${p.product_id}`} className="chat-card">
                        <img src={p.image_url} alt={p.name} />
                        <span className="chat-card-name">{p.name}</span>
                        <span className="chat-card-price">{formatPrice(p.price)}</span>
                      </Link>
                    ))}
                  </div>
                )}
                {i === messages.length - 1 && !busy && !!m.suggestions?.length && (
                  <div className="chat-suggestions" aria-label="Suggested questions">
                    {m.suggestions.map((sug) => (
                      <button key={sug} className="chat-suggestion" onClick={() => send(sug)}>
                        {sug}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {busy && (
              <div className="chat-msg assistant typing" aria-label="Looking that up">
                <span className="dot" /><span className="dot" /><span className="dot" />
              </div>
            )}
            <div ref={endRef} />
          </div>
          <form className="chat-form" onSubmit={onSubmit}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask about a product…"
              aria-label="Chat message"
              maxLength={2000}
            />
            <button type="submit" disabled={busy || !draft.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button className="chat-toggle" onClick={() => setOpen((o) => !o)} aria-label="Open chat">
        {open ? "×" : <><span className="chat-toggle-mark" aria-hidden>Y</span> Ask Campus Customs</>}
      </button>
    </div>
  );
}
