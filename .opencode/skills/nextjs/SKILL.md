---
name: nextjs
description: Use when building full-stack React applications with Next.js. Covers App Router, Server Components, data fetching, and deployment.
---

# Next.js Skill

## Overview
Next.js is a React framework for production-grade applications. It provides file-based routing, server-side rendering, static generation, API routes, and full-stack capabilities. The App Router (introduced in v13) is the recommended approach for new projects.

## Instructions
- Use the App Router (`app/` directory) for all new projects; the Pages Router (`pages/`) is legacy
- Default to React Server Components; only add `'use client'` when you need interactivity, browser APIs, or React hooks
- Fetch data at the component level using async Server Components
- Keep client components as leaf nodes in the component tree — push them to the leaves
- Use the `next/image` component for optimized images
- Use `next/link` for client-side navigation instead of `<a>` tags
- Configure redirects, headers, and rewrites in `next.config.js`
- Use environment variables prefixed with `NEXT_PUBLIC_` for client-side exposure
- Leverage Incremental Static Regeneration (ISR) for pages with dynamic but cacheable content
- Use `generateStaticParams` for fully static pages from dynamic routes

## Core Concepts

### App Router
- Files: `page.js` (route UI), `layout.js` (shared wrapper), `loading.js` (loading UI), `error.js` (error boundary), `not-found.js` (404)
- Dynamic routes: `[slug]/page.js` for single param, `[...slug]/page.js` for catch-all
- Route groups: `(groupName)` to organize without affecting URL paths
- Parallel routes: `@slot` for rendering multiple pages simultaneously in the same layout
- Intercepting routes: `(..)` to intercept and show a route in the current layout context

### Server Components
- Render on the server, reducing client bundle size
- Can directly access databases, filesystems, and backend services
- Cannot use hooks, event handlers, or browser APIs
- Can import client components, but not vice versa
- Reduce the amount of JavaScript sent to the browser
- Support `async/await` directly in the component function body

### Client Components
- Mark with `'use client'` directive at the top of the file
- Enable interactivity, event handlers, effects, and browser APIs
- Hydrate on the client after server rendering
- Minimize client component code; extract server-renderable parts into Server Components
- Client components can still be server-rendered on initial load

### Data Fetching
- Fetch directly in Server Components with `async` and `await`
- Use `fetch` with `cache: 'force-cache'` (default), `cache: 'no-store'`, or `next: { revalidate: N }` for ISR
- Use React `cache()` function to deduplicate requests within a render pass
- Use Server Actions (`'use server'`) for mutations — form submissions, data updates
- Use Route Handlers for building API endpoints in the App Router
- Use `generateMetadata` for dynamic metadata and SEO
- Stream content with `loading.js` and `Suspense` boundaries

### Server Actions
- Functions marked with `'use server'` that run on the server
- Can be called directly from forms and client components
- Support revalidation via `revalidatePath()` and `revalidateTag()`
- Can be defined inline in Server Components or imported in client components
- Handle form validation and error handling within the action function
- Support progressive enhancement — forms work without JavaScript

### Middleware
- Runs before every request, edge runtime
- Use for authentication, redirects, i18n, bot detection, A/B testing
- Export a `middleware` function from `middleware.ts` in the project root
- Use `NextResponse` to redirect, rewrite, or set headers
- Use `NextRequest` to access cookies, headers, geolocation, and UA data

## Examples

### Server Component with Data Fetching
```tsx
// app/posts/[slug]/page.tsx
import { notFound } from 'next/navigation'

interface PostPageProps {
  params: Promise<{ slug: string }>
}

async function getPost(slug: string) {
  const res = await fetch(`https://api.example.com/posts/${slug}`, {
    next: { revalidate: 3600 },
  })
  if (!res.ok) return null
  return res.json()
}

export default async function PostPage({ params }: PostPageProps) {
  const { slug } = await params
  const post = await getPost(slug)
  if (!post) notFound()

  return (
    <article>
      <h1>{post.title}</h1>
      <div dangerouslySetInnerHTML={{ __html: post.content }} />
    </article>
  )
}

export async function generateMetadata({ params }: PostPageProps) {
  const { slug } = await params
  const post = await getPost(slug)
  if (!post) return { title: 'Post Not Found' }
  return { title: post.title, description: post.excerpt }
}
```

### Client Component with Server Action
```tsx
'use client'

import { useActionState } from 'react'
import { createPost } from './actions'

export function CreatePostForm() {
  const [state, formAction, pending] = useActionState(createPost, {
    errors: {},
    success: false,
  })

  return (
    <form action={formAction}>
      <input name="title" placeholder="Title" />
      {state.errors.title && <p>{state.errors.title}</p>}

      <textarea name="content" placeholder="Content" />
      {state.errors.content && <p>{state.errors.content}</p>}

      <button disabled={pending}>
        {pending ? 'Saving...' : 'Create Post'}
      </button>
    </form>
  )
}
```

### Layout with Navigation
```tsx
// app/layout.tsx
import Link from 'next/link'

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <header>
          <nav>
            <Link href="/">Home</Link>
            <Link href="/about">About</Link>
            <Link href="/posts">Posts</Link>
          </nav>
        </header>
        <main>{children}</main>
      </body>
    </html>
  )
}
```

### Route Handler
```tsx
// app/api/posts/route.ts
import { NextResponse } from 'next/server'

export async function GET() {
  const posts = await db.posts.findAll()
  return NextResponse.json(posts)
}

export async function POST(request: Request) {
  const body = await request.json()
  const post = await db.posts.create(body)
  return NextResponse.json(post, { status: 201 })
}
```

## Best Practices
- Use `next/script` with the correct strategy (`afterInteractive`, `beforeInteractive`, `lazyOnload`)
- Optimize fonts with `next/font` to eliminate layout shift
- Use `next/dynamic` for dynamic imports of client components with no SSR if needed
- Use `generateStaticParams` with `revalidate` for hybrid rendering
- Use `loading.tsx` for instant loading states
- Always provide metadata with `generateMetadata` or `metadata` export
- Structure layouts to minimize re-renders when navigating between pages
- Use the `shallow` routing pattern for URL updates without data fetching

## Common Mistakes
- Putting `'use client'` on the entire page when only a small interactive element needs it
- Fetching the same data in multiple components instead of lifting fetch to a shared Server Component
- Using `useEffect` for data fetching when Server Components can do it
- Not handling loading, error, and empty states in data-fetching components
- Importing server-only code (DB, tokens) into client components accidentally
- Forgetting to use `revalidatePath` or `revalidateTag` after Server Action mutations
- Using `<a>` instead of `<Link>` for internal navigation, losing client-side transitions
- Not using the `Web vitals` report to track real-user performance

## Libraries
- **next-auth** / **auth.js** — authentication for Next.js
- **@prisma/client** — database ORM (works seamlessly with Server Components)
- **next-intl** — internationalization for App Router
- **@sentry/nextjs** — error monitoring and performance tracking
- **next-mdx-remote** — render MDX in Server Components
- **@next/bundle-analyzer** — analyze JavaScript bundle sizes
- **next-sitemap** — generate sitemaps programmatically
- **next-seo** (legacy) — SEO management (use `generateMetadata` for App Router)
- **next-themes** — theme switching with dark mode support
- **swr** — React Hooks for data fetching (alternative to Server Components)

## Design Principles
- **Zero JavaScript by Default**: Render as much as possible on the server before sending to client
- **File-Based Routing**: Routes are defined by the directory structure, not configuration
- **Hybrid Rendering**: Choose between SSG, SSR, ISR, and CSR per page
- **Full-Stack Integration**: APIs, authentication, and database access in a single project
- **Progressive Enhancement**: Applications work without JavaScript and enhance with it
- **Edge-Ready**: Deploy globally with edge functions for low-latency responses

## Coding Standards
- Use `.tsx` extension for all components
- One default export per page/layout/route handler file
- Extract reusable logic into `lib/` directory
- Place types in `types/` or co-locate with component files
- Use `import type` for type-only imports
- Follow the file conventions: `page.tsx`, `layout.tsx`, `loading.tsx`, `error.tsx`
- Use kebab-case for route directories, PascalCase for components
- Define metadata with the `Metadata` type from `next`
- Use the `Route` type for route segment parameters

## Performance
- Use `next/image` with proper width, height, and lazy loading
- Configure `experimental.optimizePackageImports` for tree-shaking
- Use ISR for content that changes but needs SEO
- Implement streaming with Suspense boundaries for slow data fetches
- Leverage static generation for marketing pages and documentation
- Use the `priority` attribute on above-the-fold images
- Avoid large client bundles by analyzing with `@next/bundle-analyzer`
- Enable `experimental.turbo` for faster local development
- Use `next/compression` or configure compression at the reverse proxy level

## Security
- Validate and sanitize all user input in Server Actions
- Use Server Actions for mutations to keep business logic on the server
- Never expose API keys or secrets to the client — use `NEXT_PUBLIC_` only for safe values
- Implement CSRF protection for forms
- Use HTTP-only cookies for session tokens
- Configure CSP headers in `next.config.js` or middleware
- Validate request body schemas in Route Handlers and Server Actions
- Rate-limit API routes to prevent abuse
- Use `next-auth` for battle-tested authentication flows
- Sanitize `dangerouslySetInnerHTML` content with DOMPurify on the server
