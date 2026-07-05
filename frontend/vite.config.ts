/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Dev server proxies /api to the local FastAPI backend; the production build is served
// by that same FastAPI app from frontend/dist. The triple-slash reference above adds the
// typed `test` field (vitest) without pulling in vitest's nested Vite types.
export default defineConfig({
  plugins: [react()],
  build: { outDir: "dist" },
  server: { proxy: { "/api": "http://127.0.0.1:8000" } },
  test: { environment: "jsdom", globals: true, setupFiles: "./src/setupTests.ts" },
});
