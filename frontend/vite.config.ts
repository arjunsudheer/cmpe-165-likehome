import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

// Local dev:  VITE_BACKEND_URL unset → falls back to localhost:5001
// Docker:     docker-compose injects VITE_BACKEND_URL=http://backend:5001
const backendUrl = process.env.VITE_BACKEND_URL ?? "http://localhost:5001";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    proxy: {
      "/auth":         { target: backendUrl, changeOrigin: true },
      "/hotels":       { target: backendUrl, changeOrigin: true },
      "/reservations": { target: backendUrl, changeOrigin: true },
      "/rewards":      { target: backendUrl, changeOrigin: true },
      "/favorites":    { target: backendUrl, changeOrigin: true },
      '/saved-searches': { target: backendUrl, changeOrigin: true },
    },
  },
});
