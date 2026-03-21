import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/auth": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
      "/reservation": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
      "/payment": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
      "/search": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
      "/db": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
});