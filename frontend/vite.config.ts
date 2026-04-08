import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";

// Prefer process.env so docker compose can override (VITE_BACKEND_URL=http://backend:5001).
// Otherwise frontend/.env.development → 127.0.0.1:5001 for local npm run dev.
export default defineConfig(({ mode }) => {
  const fileEnv = loadEnv(mode, process.cwd(), "");
  const backendUrl =
    process.env.VITE_BACKEND_URL ??
    fileEnv.VITE_BACKEND_URL ??
    "http://127.0.0.1:5001";

  return {
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      proxy: {
        "/auth": { target: backendUrl, changeOrigin: true },
        "/hotels": { target: backendUrl, changeOrigin: true },
        "/reservations": { target: backendUrl, changeOrigin: true },
        "/rewards": { target: backendUrl, changeOrigin: true },
      },
    },
  };
});
