---
name: vite
description: Use when building projects with Vite. Covers configuration, plugins, HMR, build optimization.
---

# Vite Skill

## Overview
Vite is a next-generation build tool and development server that leverages native ES modules for fast cold starts and Hot Module Replacement (HMR). It supports Vue, React, Svelte, Solid, Lit, vanilla JS/TS, and SSR projects with minimal configuration.

## Instructions
- Use the official scaffolding tool: `npm create vite@latest` to start new projects
- Leverage Vite's built-in support for TypeScript, JSX, CSS preprocessing, and asset handling
- Configure project settings in `vite.config.ts` — avoid modifying the framework config directly
- Use environment variables prefixed with `VITE_` for client-side exposure
- Use the `import.meta.env` object to access environment variables
- Use absolute imports with the `@` alias configured in `vite.config.ts`
- Prefer ESM for all configuration files; Vite runs them natively
- Use `define` in config for replacing global constants at build time
- Leverage Vite's optimized dependency pre-bundling for faster cold starts
- Use `vite build --mode <mode>` for environment-specific builds

## Core Concepts

### Dev Server
- Serves files over native ESM — no bundling during development
- Cold start is instant regardless of project size
- Files are transformed on-demand when requested by the browser
- HMR updates modules without full page reload, preserving application state
- HMR works with CSS, JS/TS, Vue, React, and other frameworks
- Dev server runs on port 5173 by default; configurable with `server.port`

### Build
- Uses Rollup under the hood for production builds
- Outputs optimized, tree-shaken, code-split bundles
- CSS is automatically extracted, minified, and code-split
- Assets are hashed for cache busting
- Build output goes to `dist/` by default
- Run `vite build` for production; `vite build --watch` for continuous builds

### Plugins
- Vite plugins are Rollup-compatible with Vite-specific hooks
- Plugin order matters: alias, vite:resolve, build hooks, vite:html, vite:css, rollup
- Use `vite-plugin-*` naming convention for community plugins
- Plugins can add virtual modules, transform code, inject scripts, and more
- Common plugins: `@vitejs/plugin-react`, `@vitejs/plugin-vue`, `vite-plugin-pwa`

### Environment Variables
- `.env` files loaded from project root
- `.env.local` overrides `.env` (not committed)
- `.env.development` loaded in dev mode
- `.env.production` loaded in build mode
- Only variables with `VITE_` prefix are exposed to client code
- Access via `import.meta.env.VITE_API_URL`
- Use `import.meta.env.MODE`, `import.meta.env.PROD`, `import.meta.env.DEV` for environment checks

## Examples

### Basic Vite Config (React + TypeScript)
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  build: {
    target: 'es2020',
    minify: 'terser',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },
})
```

### Plugin Example
```ts
import { defineConfig, type Plugin } from 'vite'

function injectVersion(): Plugin {
  return {
    name: 'inject-version',
    transformIndexHtml(html) {
      return html.replace('</head>', `<meta name="version" content="${process.env.npm_package_version}"></head>`)
    },
    config() {
      return {
        define: {
          __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
        },
      }
    },
  }
}

export default defineConfig({
  plugins: [injectVersion()],
})
```

### Library Mode Configuration
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    lib: {
      entry: 'src/index.ts',
      name: 'MyLibrary',
      formats: ['es', 'cjs', 'umd'],
      fileName: format => `my-library.${format}.js`,
    },
    rollupOptions: {
      external: ['react', 'react-dom'],
      output: {
        globals: {
          react: 'React',
          'react-dom': 'ReactDOM',
        },
      },
    },
  },
})
```

### Worker Setup
```ts
// vite.config.ts
import { defineConfig } from 'vite'

export default defineConfig({
  worker: {
    format: 'es',
    plugins: () => [],
  },
})

// src/worker.ts
self.onmessage = (e) => {
  const result = heavyComputation(e.data)
  self.postMessage(result)
}

// src/main.ts
const worker = new Worker(new URL('./worker.ts', import.meta.url), { type: 'module' })
worker.postMessage(data)
worker.onmessage = (e) => console.log(e.data)
```

## Best Practices
- Always commit `vite.config.ts` with the project
- Add `dist/` and `.env.local` to `.gitignore`
- Use `optimizeDeps.include` for dependencies that need pre-bundling
- Use `optimizeDeps.exclude` for dependencies that should not be pre-bundled
- Configure `server.proxy` during development to avoid CORS issues
- Use `clearScreen: false` to keep terminal output visible
- Set `build.sourcemap` to `true` for debugging production issues
- Use `build.chunkSizeWarningLimit` (default 500kB) to monitor bundle sizes
- Analyze bundle with `vite-plugin-inspect` or `rollup-plugin-visualizer`
- Use CSS modules with `*.module.css` naming convention for scoped styles

## Common Mistakes
- Not using the `VITE_` prefix for environment variables used in client code
- Forgetting to configure the proxy for API requests during development
- Importing from `node_modules` without proper tree-shaking configuration
- Using CommonJS modules in SSR without configuring `ssr.external`
- Not handling the `__dirname` difference in ESM (`import.meta.url` instead)
- Using `require()` in ESM context (Vite uses ESM natively)
- Forgetting to add `@vitejs/plugin-react` for React Fast Refresh
- Not configuring `resolve.alias` for clean import paths (leads to `../../../` hell)
- Using `process.env` directly instead of `import.meta.env`
- Overriding `define` values without using `JSON.stringify()`
- Misunderstanding that `import.meta.env` is statically replaced at build time

## Libraries
- **@vitejs/plugin-react** — React Fast Refresh + JSX transform
- **@vitejs/plugin-vue** — Vue SFC compilation + HMR
- **vite-plugin-pwa** — progressive web app support with workbox
- **vite-plugin-inspect** — inspect transform steps and module graph
- **vite-tsconfig-paths** — TypeScript path alias resolution (alternative to manual alias config)
- **rollup-plugin-visualizer** — bundle visualization for analyzing output
- **vite-plugin-svgr** — import SVGs as React components
- **vite-plugin-checker** — type checking and linting in a separate worker thread
- **unplugin-auto-import** — auto-import React hooks and other APIs
- **vite-plugin-ssr** — server-side rendering for Vite (alternative to Next.js)

## Design Principles
- **Instant Server Start**: Serve unbundled ES modules; no bundling during dev
- **Fast HMR**: Module-level granularity; only invalidate the exact module that changed
- **No-Bundle Dev**: Use native ESM import/export in the browser during development
- **Optimized Build**: Tree-shaking, code-splitting, and lazy loading via Rollup
- **Framework Agnostic**: Core is framework-independent; framework support via plugins
- **Configurable Convention**: Sensible defaults with full customization when needed

## Coding Standards
- Config file: `vite.config.ts` (or `.js` for JS projects)
- Entry point: `index.html` at project root (not hidden in `src/`)
- Source directory: `src/` by convention
- Public assets: `public/` directory, served at root path
- Environment files: `.env`, `.env.local`, `.env.development`, `.env.production`
- Output directory: `dist/` (configurable with `build.outDir`)
- Use `.ts` extension for typed config files
- Keep Vite config focused on build/dev concerns — separate app config into its own files

## Performance Tuning
- Enable `build.cssCodeSplit` to extract CSS per chunk (default: true)
- Use `build.rollupOptions.output.manualChunks` to split vendor code
- Set `build.target` to modern browsers for smaller bundles (e.g., `es2020`)
- Use `build.minify: 'esbuild'` for faster builds; `'terser'` for smaller bundles
- Configure `optimizeDeps.include` for dependencies with many internal imports
- Use `experimental: { renderBuiltUrl }` for CDN URL transformations
- Enable `server.watch.usePolling` for file systems that don't support file events
- Use `build.reportCompressedSize: false` to speed up build time
- Lazy-load heavy dependencies with dynamic imports
- Use `vite build --profile` for generating a performance profile

## SSR Support
- Vite has built-in SSR support via `vite.ssr` config
- Use `ssr.external` to externalize Node.js dependencies
- Use `ssr.noExternal` to force bundling of specific deps
- SSR entry point: separate from client entry; typically `src/entry-server.ts`
- Use `vite dev` for SSR development with HMR
- Use `@vitejs/plugin-react` with SSR for React streaming (React 18+)
- Hydration mismatch is caught and reported by Vite in dev mode
- Build SSR separately with `vite build --ssr`
