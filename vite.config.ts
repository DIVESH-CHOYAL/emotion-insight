import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  server: {
    // Plain HTTP — the Vite proxy below handles backend communication.
    // No self-signed cert issues this way.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  tanstackStart: {
    server: { entry: "server" },
  },
});
