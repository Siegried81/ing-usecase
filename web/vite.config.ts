import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// base: "./" so a built bundle opens from a file path or any sub-path - the
// deck machine should not need a web server configured a particular way.
export default defineConfig({ plugins: [react()], base: "./" });
