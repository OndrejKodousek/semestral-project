import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const isDocsBuild = mode === "docs";

  return {
    plugins: [react()],
    build: {
      outDir: isDocsBuild ? "../docs/html/website-dist" : "dist",
      emptyOutDir: true,
      rollupOptions: {
        output: {
          entryFileNames: `assets/[name].js`,
          chunkFileNames: `assets/[name].js`,
          assetFileNames: `assets/[name].[ext]`,
        },
      },
    },
  };
});
