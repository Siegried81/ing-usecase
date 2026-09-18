import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base: "./" so a built bundle opens from a file path or any sub-path - the
// deck machine should not need a web server configured a particular way.
//
// /api and /site are proxied to scripts/serve_web.py in dev, so the UI can
// generate recommendations and open the generated website without a second
// origin. A built bundle served by that same backend needs no proxy at all,
// which is why the client uses relative URLs.
export default defineConfig({
  plugins: [react()],
  base: "./",
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8010",
      "/site": "http://127.0.0.1:8010",
    },
  },
});
