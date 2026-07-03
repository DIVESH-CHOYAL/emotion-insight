import basicSsl from '@vitejs/plugin-basic-ssl';
import { defineConfig } from "@lovable.dev/vite-tanstack-config";

export default defineConfig({
  tanstackStart: {
    server: { entry: "server" },
  },
  vite: {
    plugins: [basicSsl()],
    server: {
      https: true,
      port: 8080,
      host: true,
    }
  }
});
