import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `npm run dev` serves the shop at http://localhost:5174.
// /api and /media are proxied to the FastAPI backend (backend/main.py), which runs on
// port 8000: `cd backend && uvicorn main:app --reload --port 8000`.
// Set CC_API_PORT to point at a backend on another port.
declare const process: { env: Record<string, string | undefined> }; // Node global (no @types/node needed)
const api = `http://127.0.0.1:${process.env.CC_API_PORT ?? "8000"}`;

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    strictPort: true,
    proxy: {
      "/api": api,
      "/media": api,
    },
  },
});
