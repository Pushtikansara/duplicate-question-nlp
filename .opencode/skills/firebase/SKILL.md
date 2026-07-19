---
name: firebase
description: Use when building with Firebase. Covers Firestore, authentication, cloud functions, hosting, and security rules.
---

# Firebase Skill

## Instructions

Firebase is Google's application development platform that provides a suite of cloud services including Firestore database, authentication, cloud functions, hosting, storage, and real-time capabilities. This skill covers the core Firebase services and best practices for building applications on the Firebase platform.

### Project Setup

Initialize Firebase in your project:

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize project
firebase init

# Install SDK
npm install firebase
```

Create the Firebase app configuration:

```typescript
import { initializeApp } from 'firebase/app'
import { getFirestore } from 'firebase/firestore'
import { getAuth } from 'firebase/auth'
import { getStorage } from 'firebase/storage'
import { getFunctions } from 'firebase/functions'

const firebaseConfig = {
  apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
  authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
  storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
}

const app = initializeApp(firebaseConfig)
export const db = getFirestore(app)
export const auth = getAuth(app)
export const storage = getStorage(app)
export const functions = getFunctions(app)
```

### Firestore Database

Firestore is a NoSQL document database designed for automatic scaling, high performance, and real-time synchronization.

- Data is stored in documents, which are organized into collections
- Documents have key-value pairs with support for various data types
- Subcollections enable hierarchical data organization
- Queries are indexed by default for performance
- Real-time listeners provide live data synchronization
- Transactions provide atomic read-modify-write operations
- Batch writes allow multiple operations in a single atomic commit

### Firestore Data Modeling

Model Firestore data based on query patterns:

- **Collections**: Top-level containers for documents (e.g., `users`, `posts`)
- **Documents**: Individual records with fields (max 1MB per document)
- **Subcollections**: Nested collections for related data (e.g., `users/{userId}/posts`)
- **References**: Document references for relationships

Design considerations:
- Keep documents small (under 1MB limit, but prefer under 100KB)
- Use subcollections for data that grows unboundedly
- Denormalize data for read efficiency, especially for frequently accessed fields
- Use composite indexes for complex queries
- Limit collection group queries with field filters

### Authentication

Firebase Authentication provides easy-to-use SDKs for user authentication:

- Email/Password authentication with built-in UI
- Phone number authentication
- Multi-factor authentication
- Federated identity providers (Google, Facebook, Apple, GitHub, etc.)
- Custom authentication with your own auth system
- Anonymous authentication

### Cloud Functions

Firebase Cloud Functions run backend code in response to Firebase events and HTTPS requests:

- Firestore triggers (onCreate, onUpdate, onDelete, onWrite)
- Authentication triggers (onCreate, onDelete user)
- HTTPS callable functions
- Scheduled functions (cron jobs)
- Storage triggers (onObjectFinalized, onObjectDeleted)
- Pub/Sub triggers for event-driven architectures

### Security Rules

Firebase Security Rules protect your data by controlling access at the server level:

- Firestore Security Rules for database access
- Storage Security Rules for file access
- Rules are written in a purpose-specific rules language
- Rules are evaluated on every read and write operation
- Use granular conditions for fine-grained access control

## Examples

### Example 1: Firestore CRUD Operations

```typescript
import { db } from './firebase'
import {
  collection, doc, getDoc, getDocs, addDoc, updateDoc,
  deleteDoc, query, where, orderBy, limit, startAfter,
  Timestamp, serverTimestamp, increment, arrayUnion, arrayRemove
} from 'firebase/firestore'

// CREATE
const docRef = await addDoc(collection(db, 'posts'), {
  title: 'My First Post',
  content: 'This is the post content',
  authorId: userId,
  published: false,
  tags: ['firebase', 'typescript'],
  likeCount: 0,
  createdAt: serverTimestamp(),
  updatedAt: serverTimestamp(),
})

// READ (single document)
const postSnap = await getDoc(doc(db, 'posts', postId))
if (postSnap.exists()) {
  const post = { id: postSnap.id, ...postSnap.data() }
}

// READ (with query)
const postsQuery = query(
  collection(db, 'posts'),
  where('published', '==', true),
  where('authorId', '==', userId),
  orderBy('createdAt', 'desc'),
  limit(10)
)
const querySnapshot = await getDocs(postsQuery)
const posts = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }))

// UPDATE
await updateDoc(doc(db, 'posts', postId), {
  title: 'Updated Title',
  likeCount: increment(1),
  tags: arrayUnion('updated'),
  updatedAt: serverTimestamp(),
})

// DELETE
await deleteDoc(doc(db, 'posts', postId))
```

### Example 2: Real-time Listener with Unsubscribe

```typescript
import { onSnapshot, collection, query, where, orderBy } from 'firebase/firestore'

function subscribeToPosts(userId: string, onUpdate: (posts: any[]) => void) {
  const postsQuery = query(
    collection(db, 'posts'),
    where('authorId', '==', userId),
    orderBy('createdAt', 'desc')
  )

  const unsubscribe = onSnapshot(postsQuery, (snapshot) => {
    const posts = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      // Handle metadata changes
      isNew: doc.metadata.hasPendingWrites,
    }))
    onUpdate(posts)
  }, (error) => {
    console.error('Listener error:', error)
  })

  // Return unsubscribe function for cleanup
  return unsubscribe
}

// Usage in React
useEffect(() => {
  const unsub = subscribeToPosts(userId, setPosts)
  return () => unsub() // Cleanup on unmount
}, [userId])
```

### Example 3: Authentication Flows

```typescript
import { auth } from './firebase'
import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  signInWithPopup,
  GoogleAuthProvider,
  sendPasswordResetEmail,
  updateProfile,
  User
} from 'firebase/auth'

// Sign up
async function signUp(email: string, password: string, displayName: string) {
  const userCredential = await createUserWithEmailAndPassword(auth, email, password)
  await updateProfile(userCredential.user, { displayName })
  return userCredential.user
}

// Sign in
async function signIn(email: string, password: string) {
  const userCredential = await signInWithEmailAndPassword(auth, email, password)
  return userCredential.user
}

// Google sign in
async function signInWithGoogle() {
  const provider = new GoogleAuthProvider()
  provider.setCustomParameters({ prompt: 'select_account' })
  const result = await signInWithPopup(auth, provider)
  return result.user
}

// Sign out
async function logout() {
  await signOut(auth)
}

// Auth state observer
function onAuthChanged(callback: (user: User | null) => void) {
  return onAuthStateChanged(auth, callback)
}

// Password reset
async function resetPassword(email: string) {
  await sendPasswordResetEmail(auth, email)
}
```

### Example 4: Transactions and Batched Writes

```typescript
import { runTransaction, writeBatch, doc, collection, increment } from 'firebase/firestore'

// Transaction (atomic read-modify-write)
async function transferPoints(fromUserId: string, toUserId: string, points: number) {
  try {
    await runTransaction(db, async (transaction) => {
      const fromRef = doc(db, 'users', fromUserId)
      const toRef = doc(db, 'users', toUserId)

      const fromDoc = await transaction.get(fromRef)
      if (!fromDoc.exists()) throw new Error('Sender not found')

      const currentPoints = fromDoc.data().points
      if (currentPoints < points) throw new Error('Insufficient points')

      transaction.update(fromRef, { points: increment(-points) })
      transaction.update(toRef, { points: increment(points) })
    })
    console.log('Transfer successful')
  } catch (error) {
    console.error('Transfer failed:', error)
  }
}

// Batched write (atomic multi-document write)
async function createPostWithNotifications(postId: string, userId: string, followers: string[]) {
  const batch = writeBatch(db)

  // Create the post
  batch.set(doc(db, 'posts', postId), {
    title: 'New Post',
    content: 'Post content',
    authorId: userId,
    createdAt: new Date(),
  })

  // Create notifications for followers
  for (const followerId of followers) {
    const notifRef = doc(collection(db, 'notifications'))
    batch.set(notifRef, {
      userId: followerId,
      type: 'new_post',
      postId: postId,
      read: false,
      createdAt: new Date(),
    })
  }

  await batch.commit()
}
```

### Example 5: Cloud Functions

```typescript
// functions/src/index.ts
import * as functions from 'firebase-functions'
import * as admin from 'firebase-admin'

admin.initializeApp()
const db = admin.firestore()

// Firestore trigger: onCreate
export const onNewPost = functions.firestore
  .document('posts/{postId}')
  .onCreate(async (snap, context) => {
    const post = snap.data()
    const userId = post.authorId

    // Update user's post count
    await db.doc(`users/${userId}`).update({
      postCount: admin.firestore.FieldValue.increment(1),
    })

    // Send notification to followers
    // ... notification logic
  })

// HTTPS callable function
export const createPost = functions.https.onCall(async (data, context) => {
  if (!context.auth) {
    throw new functions.https.HttpsError(
      'unauthenticated',
      'Must be signed in'
    )
  }

  const { title, content } = data
  if (title.length < 3) {
    throw new functions.https.HttpsError(
      'invalid-argument',
      'Title must be at least 3 characters'
    )
  }

  const post = await db.collection('posts').add({
    title,
    content,
    authorId: context.auth.uid,
    createdAt: admin.firestore.FieldValue.serverTimestamp(),
  })

  return { id: post.id }
})

// Scheduled function (cron)
export const cleanupOldPosts = functions.pubsub
  .schedule('every 24 hours')
  .onRun(async (context) => {
    const cutoff = new Date()
    cutoff.setDate(cutoff.getDate() - 30)

    const oldPosts = await db.collection('posts')
      .where('createdAt', '<', cutoff)
      .get()

    const batch = db.batch()
    oldPosts.docs.forEach(doc => batch.delete(doc.ref))
    await batch.commit()

    console.log(`Cleaned up ${oldPosts.size} old posts`)
  })
```

### Example 6: Security Rules

```javascript
// firestore.rules
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Helper functions
    function isAuthenticated() {
      return request.auth != null;
    }

    function isOwner(userId) {
      return request.auth.uid == userId;
    }

    function isAdmin() {
      return request.auth.token.admin == true;
    }

    // User profiles
    match /users/{userId} {
      allow read: if isAuthenticated();
      allow write: if isOwner(userId) || isAdmin();
      allow create: if isOwner(userId) && request.resource.data.name is string;
      allow delete: if isOwner(userId) || isAdmin();
    }

    // Posts
    match /posts/{postId} {
      allow read: if resource.data.published == true || isOwner(resource.data.authorId);
      allow create: if isAuthenticated() && request.resource.data.title is string;
      allow update: if isOwner(resource.data.authorId);
      allow delete: if isOwner(resource.data.authorId) || isAdmin();

      // Subcollections
      match /comments/{commentId} {
        allow read: if true;
        allow write: if isAuthenticated();
      }
    }
  }
}
```

### Example 7: Firebase Storage

```typescript
import { ref, uploadBytes, getDownloadURL, deleteObject, listAll } from 'firebase/storage'
import { storage } from './firebase'

// Upload file
async function uploadProfilePicture(userId: string, file: File) {
  const storageRef = ref(storage, `users/${userId}/avatar.jpg`)

  // Upload with metadata
  const metadata = {
    contentType: file.type,
    customMetadata: {
      userId,
      uploadedAt: new Date().toISOString(),
    },
  }

  const snapshot = await uploadBytes(storageRef, file, metadata)
  const downloadUrl = await getDownloadURL(snapshot.ref)
  return downloadUrl
}

// List files
async function listUserFiles(userId: string) {
  const folderRef = ref(storage, `users/${userId}/`)
  const result = await listAll(folderRef)
  const urls = await Promise.all(
    result.items.map(item => getDownloadURL(item))
  )
  return urls
}

// Delete file
async function deleteFile(path: string) {
  const fileRef = ref(storage, path)
  await deleteObject(fileRef)
}
```

## Best Practices

### Firestore Best Practices

- Create composite indexes for all query patterns via Firebase Console or CLI
- Use collection group queries sparingly and with field filters
- Limit document size to under 100KB for optimal read performance
- Use batched writes for atomic multi-document operations
- Implement data validation using Firestore `validate` functions in rules
- Use `serverTimestamp()` for consistency across all clients
- Avoid deeply nested collections; prefer shallow structures
- Use `limit()` on all queries to prevent excessive data retrieval
- Implement pagination with `startAfter()` and `limit()`

### Authentication Best Practices

- Use Firebase Auth emulator for local development
- Implement proper error handling for auth operations
- Use custom claims for role-based access control (admin, moderator)
- Enable anonymous auth for temporary user sessions
- Configure authorized domains in Firebase Console
- Set up email templates for production
- Use multi-factor authentication for sensitive applications

### Cloud Functions Best Practices

- Use the Firebase Emulator Suite for local function development
- Keep functions focused on a single responsibility
- Handle errors and return meaningful error messages
- Set function memory, timeout, and concurrency limits
- Use environment configuration for secrets and settings
- Avoid heavy computation in functions triggered by database writes
- Implement idempotency for functions that may be retried
- Use `maxInstances` to control function scaling

### Security Rules Best Practices

- Write restrictive rules by default; grant access explicitly
- Use custom functions to reduce rule duplication
- Validate data structure in create and update rules
- Use `request.resource.data` for data validation
- Deny all writes by default and only allow specific operations
- Test security rules with the Firebase Emulator
- Review rules regularly for security vulnerabilities
- Use `get()` and `exists()` functions for cross-document validation

## Common Mistakes

- **Not creating composite indexes**: Complex queries fail without composite indexes. Always check the Firebase Console for index creation prompts.
- **Using arrays for lists with many elements**: Array operations can be expensive for large arrays. Use a subcollection or map structure instead.
- **Reading too many documents**: Each document read counts against quota. Use pagination and selective field queries.
- **Writing large documents**: Documents over 1MB cause errors. Keep documents small and use subcollections for growing data.
- **Not handling offline data correctly**: Firebase caches data locally but offline writes can conflict. Handle pending writes appropriately.
- **Ignoring security rules**: Default rules allow all reads/writes. Always configure restrictive rules before production deployment.
- **Using real-time listeners unnecessarily**: Every listener consumes resources. Use `getDocs()` for one-time reads when real-time updates are not needed.
- **Not using the Emulator Suite**: Developing against production Firebase can lead to accidental charges. Always use emulators locally.
- **Denormalizing without a strategy**: Copying data across documents without a sync mechanism leads to inconsistent data.
- **Forgetting to cleanup listeners**: Subscriptions that are not unsubscribed cause memory leaks and unnecessary reads.

## Libraries

### Firebase Official SDKs

| Package | Purpose |
|---------|---------|
| firebase | Main SDK (includes all sub-sdks) |
| @firebase/app | Core Firebase initialization |
| firebase/firestore | Firestore database |
| firebase/auth | Authentication |
| firebase/storage | Cloud Storage |
| firebase/functions | Cloud Functions |
| firebase/messaging | FCM push notifications |
| firebase/analytics | Google Analytics |
| firebase/performance | Performance monitoring |
| firebase/remote-config | Remote configuration |
| firebase/database | Realtime Database (legacy) |

### Firebase Admin SDKs

| Language | Package |
|----------|---------|
| Node.js | firebase-admin |
| Python | firebase-admin |
| Go | firebase.google.com/go |
| Java | com.google.firebase:firebase-admin |

### Tools and Extensions

| Tool | Purpose |
|------|---------|
| Firebase CLI | Deployment, emulation, and management |
| Firebase Emulator Suite | Local development environment |
| Firebase Extensions | Pre-built backend solutions |
| Firefoo | GUI for Firestore management |
| Firetable | Airtable-like interface for Firestore |

## Design Principles

### Data Locality

Structure data based on how it is queried, not on how it is stored normalized. In NoSQL systems like Firestore, you should duplicate data across documents to support read patterns, accepting the trade-off of managing consistency across copies.

### Document Granularity

Design documents at the granularity of a single view or use case. A document should contain all the data needed for a specific purpose, minimizing the number of reads required to populate a screen.

### Security at the Edge

Security rules are the last line of defense. Never trust client-side validation alone. Enforce all security constraints in Firestore Security Rules, which run on Google's servers regardless of the client SDK used.

### Offline First

Design your application to work offline by default. Firestore's offline persistence should be enabled, and your application logic should handle the transition between offline and online states gracefully.

## Coding Standards

### File Organization

```
src/
  firebase/
    index.ts          # Firebase initialization
    auth.ts           # Auth-related functions
    firestore.ts      # Database queries and mutations
    storage.ts        # Storage operations
    types.ts          # TypeScript types for Firestore documents
  functions/
    src/
      index.ts        # Cloud Functions entry point
```

### Naming Conventions

- Collections: plural lowercase (e.g., `users`, `posts`, `orderItems`)
- Documents: use document ID (auto-generated or meaningful like `userId`)
- Fields: camelCase for JavaScript consistency (e.g., `createdAt`, `displayName`)
- Functions: verbNoun pattern (e.g., `createPost`, `getUserProfile`)
- Security rules functions: descriptive names (e.g., `isAuthenticated`, `isOwner`)

### Firestore Query Pattern

```typescript
// Consistent query pattern with error handling
async function getDocuments<T>(
  collectionName: string,
  conditions: QueryConstraint[]
): Promise<T[]> {
  try {
    const q = query(collection(db, collectionName), ...conditions)
    const snapshot = await getDocs(q)
    return snapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as T))
  } catch (error) {
    console.error(`Error fetching ${collectionName}:`, error)
    throw error
  }
}
```
