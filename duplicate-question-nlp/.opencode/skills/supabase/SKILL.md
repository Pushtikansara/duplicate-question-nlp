---
name: supabase
description: Use when building with Supabase. Covers database, auth, storage, realtime, and edge functions.
---

# Supabase Skill

## Instructions

Supabase is an open-source Firebase alternative that provides a suite of backend services built on top of PostgreSQL. It offers database management, authentication, file storage, real-time subscriptions, and edge functions. This skill covers the core Supabase services and their integration.

### Project Setup

Initialize a Supabase project:

```bash
# Using Supabase CLI (local development)
npx supabase init
npx supabase start

# Using npm in an existing project
npm install @supabase/supabase-js
```

Create a Supabase client:

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_ANON_KEY!
)
```

### Database (PostgreSQL)

Supabase provides a full PostgreSQL database with 100% of PostgreSQL features. Use the SQL Editor in the dashboard or connect directly with your preferred PostgreSQL client.

- Use Row-Level Security (RLS) for data access control
- Enable RLS on every table that contains user-specific data
- Write SQL policies that restrict access at the database level
- Use the Supabase JavaScript client for type-safe queries
- Leverage PostgreSQL extensions: PostGIS, pgvector, pg_graphql, pg_net

### Authentication

Supabase Auth provides a complete authentication system with built-in providers and user management.

Features:
- Email/password authentication
- Passwordless login (magic link, OTP)
- OAuth providers (Google, GitHub, GitLab, Apple, Azure, etc.)
- Phone authentication (SMS)
- Multi-factor authentication (MFA)
- Anonymous sign-in
- Session management with JWT tokens

### Storage

Supabase Storage allows file uploads and management with built-in security.

- Create buckets for organizing files (public, private, or restricted)
- Set up RLS policies for storage access control
- Use the `storage` API for file operations
- Support for image transformations
- Built-in CDN for fast file delivery
- File size and MIME type restrictions

### Realtime

Supabase Realtime provides real-time data synchronization using WebSockets.

- Subscribe to database changes (INSERT, UPDATE, DELETE)
- Broadcast custom events
- Presence tracking for user online status
- Uses PostgreSQL replication under the hood

### Edge Functions

Supabase Edge Functions are serverless TypeScript functions running on Deno.

- Deploy globally on the edge
- Use for webhooks, API endpoints, and data processing
- Integrate with Supabase services via the Supabase client
- Use TypeScript/JavaScript with Deno runtime
- Environment variables for configuration

## Examples

### Example 1: Database Queries with Supabase Client

```typescript
import { supabase } from './supabaseClient'

// SELECT with filtering
const { data, error } = await supabase
  .from('posts')
  .select(`
    id,
    title,
    content,
    author:user_id (id, name, avatar_url),
    likes:post_likes (count)
  `)
  .eq('published', true)
  .gte('created_at', '2024-01-01')
  .order('created_at', { ascending: false })
  .limit(20)
  .range(0, 19)

// INSERT
const { data: newPost, error } = await supabase
  .from('posts')
  .insert({
    title: 'My Post',
    content: 'Post content',
    user_id: userId,
  })
  .select()
  .single()

// UPDATE
const { error } = await supabase
  .from('posts')
  .update({ title: 'Updated Title' })
  .eq('id', postId)

// DELETE
const { error } = await supabase
  .from('posts')
  .delete()
  .eq('id', postId)
```

### Example 2: Row-Level Security Policies

```sql
-- Enable RLS on a table
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

-- Policy: users can view published posts and their own drafts
CREATE POLICY "view_posts" ON posts
FOR SELECT
USING (
  published = true
  OR user_id = auth.uid()
);

-- Policy: users can insert their own posts
CREATE POLICY "insert_own_posts" ON posts
FOR INSERT
WITH CHECK (user_id = auth.uid());

-- Policy: users can update their own posts
CREATE POLICY "update_own_posts" ON posts
FOR UPDATE
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());

-- Policy: users can delete their own posts
CREATE POLICY "delete_own_posts" ON posts
FOR DELETE
USING (user_id = auth.uid());
```

### Example 3: Authentication Flows

```typescript
// Sign up with email
const { data, error } = await supabase.auth.signUp({
  email: 'user@example.com',
  password: 'secure_password',
  options: {
    data: {
      name: 'John Doe',
      role: 'user',
    },
  },
})

// Sign in
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'secure_password',
})

// OAuth sign in
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'github',
  options: {
    redirectTo: 'https://example.com/callback',
  },
})

// Sign out
const { error } = await supabase.auth.signOut()

// Get current session
const { data: { session } } = await supabase.auth.getSession()

// Listen to auth state changes
supabase.auth.onAuthStateChange((event, session) => {
  console.log('Auth event:', event)
  if (session) {
    // User is signed in
  } else {
    // User is signed out
  }
})

// Password reset
const { error } = await supabase.auth.resetPasswordForEmail('user@example.com', {
  redirectTo: 'https://example.com/update-password',
})
```

### Example 4: Storage Operations

```typescript
// Upload a file
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`public/${userId}/avatar.jpg`, file, {
    cacheControl: '3600',
    upsert: true,
    contentType: 'image/jpeg',
  })

// Download a file
const { data, error } = await supabase.storage
  .from('avatars')
  .download(`public/${userId}/avatar.jpg`)

// Get public URL
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl(`public/${userId}/avatar.jpg`)

// List files in a bucket
const { data, error } = await supabase.storage
  .from('avatars')
  .list('public', {
    limit: 100,
    offset: 0,
    sortBy: { column: 'created_at', order: 'desc' },
  })

// Delete files
const { error } = await supabase.storage
  .from('avatars')
  .remove([`public/${userId}/old_avatar.jpg`])

// Create signed URL for temporary access
const { data, error } = await supabase.storage
  .from('private-documents')
  .createSignedUrl(`docs/${userId}/report.pdf`, 60 * 60) // 1 hour expiry
```

### Example 5: Realtime Subscriptions

```typescript
// Subscribe to database changes
const channel = supabase
  .channel('public:posts')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'public',
      table: 'posts',
      filter: `user_id=eq.${userId}`,
    },
    (payload) => {
      console.log('Change received:', payload)
    }
  )
  .subscribe()

// Subscribe to specific event types
supabase
  .channel('posts-insert')
  .on(
    'postgres_changes',
    { event: 'INSERT', schema: 'public', table: 'posts' },
    (payload) => {
      console.log('New post:', payload.new)
    }
  )
  .subscribe()

// Broadcast custom events
const channel = supabase.channel('custom-events')
channel.subscribe((status) => {
  if (status === 'SUBSCRIBED') {
    channel.send({
      type: 'broadcast',
      event: 'cursor-pos',
      payload: { x: 100, y: 200 },
    })
  }
})

// Presence tracking
supabase
  .channel('room-1')
  .on('presence', { event: 'sync' }, () => {
    console.log('Online users:', channel.presenceState())
  })
  .on('presence', { event: 'join' }, ({ key, newPresences }) => {
    console.log('User joined:', newPresences)
  })
  .subscribe(async (status) => {
    if (status === 'SUBSCRIBED') {
      await channel.track({ online_at: new Date().toISOString() })
    }
  })

// Cleanup subscriptions
supabase.removeChannel(channel)
```

### Example 6: Edge Functions

```typescript
// supabase/functions/hello-world/index.ts
import { serve } from 'https://deno.land/std@0.177.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

serve(async (req) => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_ANON_KEY')!
  )

  const { data: posts } = await supabase
    .from('posts')
    .select('id, title')
    .limit(10)

  return new Response(
    JSON.stringify({ posts }),
    { headers: { 'Content-Type': 'application/json' } }
  )
})

// Deploy function
// npx supabase functions deploy hello-world
// npx supabase functions serve hello-world --env-file .env.local
```

### Example 7: MFA (Multi-Factor Authentication)

```typescript
// Enroll in MFA
const { data, error } = await supabase.auth.mfa.enroll({
  factorType: 'totp',
  friendlyName: 'My Authenticator',
})

// Show QR code
const qrCode = data.totp.qr_code // Use this to display QR code

// Verify enrollment
const { error } = await supabase.auth.mfa.challengeAndVerify({
  factorId: data.id,
  code: '123456',
})

// Unenroll
const { error } = await supabase.auth.mfa.unenroll({
  factorId: data.id,
})
```

## Best Practices

### Database Best Practices

- Always enable RLS on tables with user-specific data
- Create a `profiles` table that references `auth.users` for user data
- Use `auth.uid()` in RLS policies for user identification
- Create efficient indexes on columns used in RLS policies
- Use the `select()` with specific column names instead of `select('*')`
- Leverage PostgreSQL views for complex read operations
- Use `upsert` for create-or-update operations
- Implement soft deletes with `deleted_at` timestamp for recoverable data
- Use JSONB columns for flexible metadata with GIN indexes

### Authentication Best Practices

- Always use HTTPS in production
- Implement rate limiting for auth endpoints
- Use passwordless methods for better user experience
- Store refresh tokens securely (HTTP-only cookies)
- Implement session timeout for sensitive applications
- Use custom SMTP for production email delivery
- Set up redirect URLs in the Supabase dashboard
- Test OAuth flows thoroughly in development and staging
- Use anonymous sign-in for preview access

### Storage Best Practices

- Set appropriate bucket privacy (public vs. private)
- Implement storage RLS policies matching table RLS
- Use file size and MIME type restrictions at the bucket level
- Serve images with transformations for optimal performance
- Use CDN URLs for public files
- Implement automatic file cleanup for temporary uploads
- Set cache control headers for static assets
- Limit upload rates to prevent abuse

### Realtime Best Practices

- Subscribe only to changes your application needs
- Use filters to limit the scope of subscriptions
- Clean up subscriptions when components unmount
- Handle reconnection logic for dropped WebSocket connections
- Use presence for collaborative features
- Limit broadcast payload size for performance
- Use channels appropriate to data access patterns

## Common Mistakes

- **Not enabling RLS on tables**: By default, tables have RLS disabled, allowing full public access. Always enable RLS on tables with sensitive data.
- **Using `select('*')` without RLS filtering**: Without proper RLS policies, select all can expose data across users.
- **Storing tokens in localStorage**: JWT tokens can be accessed by XSS. Use HTTP-only cookies for production.
- **Not handling auth state changes**: Users can be logged out, tokens can expire. Always subscribe to auth state changes.
- **Ignoring CORS configuration**: Edge Functions require explicit CORS headers for browser requests.
- **Large realtime payloads**: Sending large objects through realtime degrades performance. Send only what's needed.
- **Not setting up proper storage RLS**: Storage buckets need their own RLS policies, separate from database tables.
- **Over-fetching in queries**: Use specific columns and filters to minimize data transfer.
- **Running expensive queries with realtime subscriptions**: Complex queries in realtime channels can overload the database.
- **Forgetting to remove channels on unmount**: Memory leaks occur when subscriptions are not cleaned up.

## Libraries

### Supabase Official Packages

| Package | Purpose |
|---------|---------|
| @supabase/supabase-js | Main client library for browser and Node.js |
| @supabase/ssr | Server-side rendering support (Next.js, SvelteKit) |
| @supabase/auth-ui-react | Pre-built auth UI components for React |
| @supabase/auth-ui-shared | Auth UI utilities |
| supabase | CLI for local development and deployment |
| postgrest-js | Direct PostgREST client (used internally) |
| gotrue-js | GoTrue authentication client (used internally) |
| realtime-js | Realtime client (used internally) |
| storage-js | Storage client (used internally) |

### Community Libraries

| Library | Purpose |
|---------|---------|
| supabase-js v2 | (Current major version) |
| prisma-supabase | Use Prisma with Supabase's PostgreSQL |
| supabase-dart | Flutter/Dart client |
| supabase-swift | iOS/Swift client |
| supabase-py | Python client (community) |
| supabase-kt | Kotlin client (community) |

## Design Principles

### Security by Default

Supabase operates on a zero-trust model. By default, tables are not accessible without RLS policies. Every database access must be explicitly authorized through policies. This principle extends to Storage (file-level RLS) and Realtime (channel authorization).

### PostgreSQL as the Core

Unlike Firebase which uses a proprietary NoSQL database, Supabase's core is a full PostgreSQL database. This means you get all PostgreSQL features: ACID transactions, SQL, extensions, joins, views, triggers, and stored procedures. Design with traditional SQL practices in mind, not document database patterns.

### Single Service Architecture

Supabase services (Auth, Storage, Realtime, Edge Functions) are designed to work together. Auth provides the user identity, RLS enforces permissions, and all services integrate with the database. Prefer using Supabase's integrated services over external alternatives for tighter security and simpler architecture.

### Client-Side Security

Security in Supabase is enforced at the database level, not the client level. RLS policies run on the server, so even if a malicious client tries to access unauthorized data, the database rejects the query. Never trust client-side code for security; always enforce policies in the database.

## Coding Standards

### Client Initialization

```typescript
// lib/supabaseClient.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
})
```

### Query Pattern

```typescript
// Consistent query patterns
async function getPosts(userId: string) {
  const { data, error } = await supabase
    .from('posts')
    .select('id, title, created_at')
    .eq('user_id', userId)
    .order('created_at', { ascending: false })

  if (error) throw error
  return data
}
```

### Error Handling

```typescript
import { SupabaseClient } from '@supabase/supabase-js'

async function handleQuery<T>(
  query: Promise<{ data: T | null; error: Error | null }>
): Promise<T> {
  const { data, error } = await query
  if (error) {
    console.error('Supabase query error:', error.message)
    throw new Error(`Database error: ${error.message}`)
  }
  if (!data) {
    throw new Error('No data returned')
  }
  return data
}
```

### RLS Policy Naming

```sql
-- Naming convention: <action>_<description>
-- Examples:
CREATE POLICY "select_own_posts" ON posts FOR SELECT USING (user_id = auth.uid());
CREATE POLICY "insert_own_posts" ON posts FOR INSERT WITH CHECK (user_id = auth.uid());
CREATE POLICY "update_own_posts" ON posts FOR UPDATE USING (user_id = auth.uid());
CREATE POLICY "delete_own_posts" ON posts FOR DELETE USING (user_id = auth.uid());

-- Admin policies
CREATE POLICY "admin_select_all" ON posts FOR SELECT USING (auth.jwt() ->> 'role' = 'admin');
```
