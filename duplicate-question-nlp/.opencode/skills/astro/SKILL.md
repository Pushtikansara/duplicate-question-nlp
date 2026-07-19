---
name: astro
description: Use when building content-focused websites with Astro. Covers islands architecture, content collections, integrations.
---

# Astro Skill

## Overview
Astro is a web framework for building content-driven websites like blogs, marketing sites, e-commerce, and documentation. Its innovative islands architecture delivers fast performance by shipping zero JavaScript by default, hydrating only interactive components on demand.

## Instructions
- Default to `.astro` files for templates — they render to static HTML with zero JS
- Use the islands pattern: add `client:load`, `client:idle`, `client:visible`, or `client:media` directives to hydrate interactive components
- Use `---` frontmatter (the component script) for server-side logic, data fetching, and imports
- Fetch data at the top level of the frontmatter — it runs only at build time for static sites
- Use Content Collections for type-safe content management with MDX, Markdown, JSON, YAML
- Use View Transitions for smooth page transitions (experimental but stable)
- Add integrations via `astro add` command (React, Vue, Svelte, Tailwind, and more)
- Use `Astro.glob()` to import multiple files from the filesystem (e.g., all blog posts)
- Use `Astro.request` to access request information (URL, headers, cookies) in SSR mode
- Deploy to any static host (Netlify, Vercel, Cloudflare Pages) or use SSR adapters

## Core Concepts

### Astro Components
- Use `---` for the component script (JavaScript/TypeScript that runs at build time)
- Use `<!-- HTML -->` for the template — standard HTML with `{expression}` interpolation
- No JavaScript is shipped to the client unless explicitly marked with a client directive
- Components are scoped by default — CSS styles don't leak to other components
- Use `<slot />` for children content composition
- Props are typed with TypeScript interfaces in the frontmatter

### Islands Architecture
- Interactive UI components are islands of interactivity in a sea of static HTML
- Each island loads independently — no global hydration
- Client directives control when and how components hydrate:
  - `client:load` — hydrate immediately on page load (use sparingly)
  - `client:idle` — hydrate when the browser is idle (requestIdleCallback)
  - `client:visible` — hydrate when the component scrolls into viewport
  - `client:media` — hydrate only when a media query matches
  - `client:only` — render only on client (no SSR), use for browser-only components
- Islands can share state via stores (nanostores, zustand) that work across frameworks

### Content Collections
- Define schemas in `src/content/config.ts` using Zod
- Organize content in `src/content/<collection-name>/` directories
- Query content with `getCollection()` and `getEntry()`
- Content is type-safe with automatic TypeScript inference from schemas
- Support for Markdown, MDX, JSON, YAML, and TOML files
- Use image optimization with `astro:assets` for responsive images in content
- Support draft mode, pagination, and RSS feed generation

### Routing
- File-based routing in `src/pages/`
- Dynamic routes: `src/pages/blog/[slug].astro`
- Static routes: `src/pages/blog/my-post.astro`
- Fallback routes for 404: `src/pages/404.astro`
- Endpoints for API routes: `src/pages/api/hello.ts` (export GET, POST, etc.)
- Redirects via `src/pages/redirects.astro` or `astro.config.mjs`
- Layouts are components that wrap page content via `<slot />` or `<Content />`

### View Transitions
- Enable with `viewTransitions: true` in `astro.config.mjs`
- Use `<ViewTransitions />` component in your layout
- Animate between pages with CSS `view-transition-name`
- No full page reload — preserves scroll position, state, and audio/video
- Custom animations with `@keyframes` and `::view-transition-*` pseudo-elements

## Examples

### Basic Page with Data Fetching
```astro
---
import Layout from '../layouts/BlogLayout.astro'
import { getCollection } from 'astro:content'

const posts = await getCollection('blog')
---
<Layout title="Blog">
  <h1>Latest Posts</h1>
  <ul>
    {posts.map(post => (
      <li>
        <a href={`/blog/${post.slug}`}>
          <article>
            <h2>{post.data.title}</h2>
            <time datetime={post.data.pubDate.toISOString()}>
              {post.data.pubDate.toLocaleDateString()}
            </time>
            <p>{post.data.description}</p>
          </article>
        </a>
      </li>
    ))}
  </ul>
</Layout>
```

### Interactive Island (React Counter)
```astro
---
import Counter from '../components/Counter.tsx'
---

<h1>Interactive Counter</h1>
<Counter client:idle />
```

```tsx
// src/components/Counter.tsx
import { useState } from 'react'

export default function Counter() {
  const [count, setCount] = useState(0)
  return <button onClick={() => setCount(c => c + 1)}>Count: {count}</button>
}
```

### Content Collection Schema
```ts
// src/content/config.ts
import { defineCollection, z } from 'astro:content'

const blogCollection = defineCollection({
  type: 'content',
  schema: ({ image }) => z.object({
    title: z.string().max(100),
    description: z.string().max(280),
    pubDate: z.date(),
    updatedDate: z.date().optional(),
    heroImage: image().optional(),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
    author: z.enum(['alice', 'bob', 'charlie']),
    readingTime: z.number().min(1).optional(),
  }),
})

const teamCollection = defineCollection({
  type: 'data',
  schema: z.object({
    name: z.string(),
    role: z.string(),
    avatar: image(),
    social: z.object({
      twitter: z.string().url().optional(),
      github: z.string().url().optional(),
    }).optional(),
  }),
})

export const collections = {
  blog: blogCollection,
  team: teamCollection,
}
```

### Dynamic Route with Pagination
```astro
---
import Layout from '../../layouts/BlogLayout.astro'
import { getCollection } from 'astro:content'

export async function getStaticPaths({ paginate }) {
  const posts = await getCollection('blog')
  return paginate(posts, { pageSize: 10 })
}

const { page } = Astro.props
---
<Layout title={`Blog - Page ${page.currentPage}`}>
  <h1>Blog</h1>
  {page.data.map(post => (
    <article>
      <a href={`/blog/${post.slug}`}>{post.data.title}</a>
    </article>
  ))}
  {page.url.prev && <a href={page.url.prev}>Previous</a>}
  {page.url.next && <a href={page.url.next}>Next</a>}
</Layout>
```

### API Endpoint (SSR)
```ts
// src/pages/api/contact.ts
import type { APIRoute } from 'astro'

export const POST: APIRoute = async ({ request }) => {
  const body = await request.json()
  const { name, email, message } = body

  if (!name || !email || !message) {
    return new Response(JSON.stringify({ error: 'Missing fields' }), {
      status: 400,
    })
  }

  await sendEmail({ name, email, message })

  return new Response(JSON.stringify({ success: true }), {
    status: 200,
  })
}
```

## Best Practices
- Minimize the number of client-side components — prefer static HTML and CSS
- Use `client:idle` or `client:visible` instead of `client:load` when possible
- Combine personalization islands (e.g., a newsletter signup) for better performance
- Use `Astro.url` to access the current URL in component scripts
- Use `Astro.slots` for advanced slot composition patterns
- Set `compressHTML: true` in config for smaller HTML output
- Use `build.assets` to prefix asset URLs for CDN deployment
- Configure `trailingSlash` behavior explicitly in config
- Use `build.format: 'file'` or `'directory'` consistently
- Enable `prefetch` for internal links to improve perceived performance
- Use the `image` component for optimized responsive images
- Add RSS feed with `@astrojs/rss` for content sites

## Common Mistakes
- Wrapping an entire page in a client component when only a small widget needs interactivity
- Using `client:load` everywhere instead of `client:idle` or `client:visible`
- Not defining a schema for content collections (losing type safety)
- Forgetting that `fetch()` in frontmatter runs at build time, not request time
- Using `Astro.request` in static mode (only available in SSR/pre-rendered hybrid)
- Not configuring the correct `output` mode (`'static'`, `'server'`, `'hybrid'`)
- Importing client-side libraries in `.astro` frontmatter (use island components instead)
- Overusing interactive components on pages with mostly static content
- Not setting `trailingSlash` consistently between dev and prod
- Mixing framework components without proper client directives (no JS in final output)

## Libraries
- **@astrojs/react** — React integration for islands
- **@astrojs/mdx** — MDX support with component embedding
- **@astrojs/tailwind** — Tailwind CSS integration
- **@astrojs/vercel** — Vercel serverless/edge adapter
- **@astrojs/netlify** — Netlify Functions adapter
- **@astrojs/cloudflare** — Cloudflare Pages adapter
- **@astrojs/sitemap** — automatic sitemap generation
- **@astrojs/rss** — RSS feed generation
- **@astrojs/partytown** — third-party script optimization via web workers
- **@astrojs/image** — image optimization (legacy; use `astro:assets` in newer versions)
- **astro-navigation** — automatic navigation from content structure
- **astro-seo** — SEO metadata management
- **starlight** — documentation theme built on Astro

## Design Principles
- **Zero JS by Default**: No JavaScript is shipped until you explicitly add it
- **Islands Architecture**: Interactive components are isolated and lazily hydrated
- **Content-First**: Optimized for content-heavy sites with built-in CMS features
- **MISO (Multi-framework) Islands**: Use React, Vue, Svelte, or Solid in the same page
- **Server-First**: Components render on the server, sending HTML to the client
- **Progressive Enhancement**: Interactive islands enhance static content, not replace it

## Coding Standards
- `.astro` extension for Astro component files
- Frontmatter (`---`) at the top of `.astro` files before HTML template
- TypeScript in frontmatter with `interface Props` for component props
- CSS within `<style>` tags is scoped by default
- Use `<style global>` for unscoped styles
- Separate TypeScript logic into `src/lib/` directory
- Content collections go in `src/content/` with schema in `src/content/config.ts`
- Pages in `src/pages/` following file-based routing
- Components in `src/components/`, layouts in `src/layouts/`
- Public assets in `public/` (served as-is, no processing)
- Image assets in `src/` (processed and optimized by Astro)
- Use PascalCase for component files and names

## Performance
- Astro sites typically ship 90%+ less JavaScript than equivalent React SPAs
- Use `Astro.glob()` to tree-shake unused content
- Enable `build.assetsInlineLimit` to inline small assets as base64
- Use `<Image />` from `astro:assets` with proper width/height to prevent CLS
- Configure `server.host` for production SSR deployments
- Use CDN caching with `Cache-Control` headers in SSR endpoints
- Implement prefetching with `data-astro-prefetch` on links
- Use the `@astrojs/partytown` for deferring heavy third-party scripts
- Set `build.concurrency` for parallel HTML generation
- Use `vite.build.rollupOptions.output.manualChunks` for granular code splitting
- Global CSS is preferred over per-component CSS when styles are shared
- Minimize unused CSS with `@astrojs/tailwind` purge or manual cleanup
- Use `astro check` for type checking and `astro build` for production builds
- Monitor the `dist/` directory size — content sites should be < 500KB total
