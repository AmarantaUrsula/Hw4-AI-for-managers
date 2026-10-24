import { ReactNode, createContext, useContext, useState } from "react";
import { PageResults } from "./api";

// Shared state between the chat widget (which receives search results from /api/chat)
// and the on-page results grid (which renders them). Problem 7.
interface ChatResultsState {
  results: PageResults | null;
  version: number; // bumps on every new result set, so the grid can scroll/animate
  show: (r: PageResults) => void;
  clear: () => void;
}

const ChatResultsContext = createContext<ChatResultsState | null>(null);

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<PageResults | null>(null);
  const [version, setVersion] = useState(0);
  const show = (r: PageResults) => {
    setResults(r);
    setVersion((v) => v + 1);
  };
  return (
    <ChatResultsContext.Provider value={{ results, version, show, clear: () => setResults(null) }}>
      {children}
    </ChatResultsContext.Provider>
  );
}

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext);
  if (!ctx) throw new Error("useChatResults must be used inside ChatResultsProvider");
  return ctx;
}
