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
    // This proxy used to point at :8010, but scripts/serve_web.py listens
    // on :8000 by default (see its own --port default and usage docstring).
    // Every proxied request failed with a connection-refused that Vite's dev
    // proxy surfaces to the browser as a 500 - this was the "Generate
    // recommendations: Error 500" report, reproduced end-to-end through the
    // real dev server (a direct curl to :8000 "worked" because it bypassed
    // this proxy entirely).
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/site": "http://127.0.0.1:8000",
    },
  },
});
