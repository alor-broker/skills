---
name: web-development
description: "Web application development using Next.js, SQLite, and Drizzle ORM. Use when: (1) Building or modifying web apps with this stack, (2) Handling HTTP requests routed to the app, (3) Working with database operations via Drizzle ORM, (4) Starting or managing the web server on Railway."
---

# Web Development

## Tech Stack

- **Framework**: Next.js (React-based full-stack framework)
- **Database**: SQLite (lightweight relational database)
- **ORM**: Drizzle ORM (type-safe SQL query builder for SQLite)

## Deployment

- **Domain**: `$RAILWAY_PUBLIC_DOMAIN` (environment variable)
- **Port**: `$PORT` (environment variable, defaults to 3000)
- **Platform**: Railway (handles networking, SSL, and routing)
- **Project Folder**: `/data/veles/workspace/web`

## Starting the Web Server

For Railway production deployment, use the production build:

```bash
cd /data/veles/workspace/web
HOST=0.0.0.0 npm start
```

This runs the Next.js production server on `$PORT` (environment variable). Railway handles:
- Process management (auto-restart on crash)
- Port binding and networking
- External routing from `$RAILWAY_PUBLIC_DOMAIN`

## Handling Requests

Railway handles all networking (DNS, SSL, load balancing). Your task is to:

1. **Create API routes** in `app/api/` directory (Next.js App Router)
2. **Handle incoming HTTP requests** - GET, POST, PUT, DELETE, etc.
3. **Process requests** and return JSON responses
4. **Use Drizzle ORM** for database operations

### Example API Route

```typescript
// app/api/example/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { users } from '@/lib/db/schema';

export async function GET(request: NextRequest) {
  const allUsers = await db.select().from(users);
  return NextResponse.json(allUsers);
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const newUser = await db.insert(users).values(body).returning();
  return NextResponse.json(newUser);
}
```

### Database Operations with Drizzle

```typescript
import { db } from '@/lib/db';
import { users, posts } from '@/lib/db/schema';

// Select
const allUsers = await db.select().from(users).where(eq(users.id, 1));

// Insert
await db.insert(users).values({ name: 'John', email: 'john@example.com' });

// Update
await db.update(users).set({ name: 'Jane' }).where(eq(users.id, 1));

// Delete
await db.delete(users).where(eq(users.id, 1));
```

## Project Structure

```
/data/veles/workspace/web/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   │   └── users/
│   │       └── route.ts   # Example API endpoint
│   ├── page.tsx          # Main page
│   └── layout.tsx        # Root layout
├── lib/
│   ├── db.ts             # Drizzle database instance
│   └── schema.ts         # Database schema definitions
├── drizzle/
│   └── config.ts         # Drizzle configuration
├── package.json
├── drizzle.config.ts
└── next.config.js
```

## Environment Variables

Railway provides these environment variables automatically:

| Variable | Description | Example |
|----------|-------------|---------|
| `PORT` | Port the app should listen on | `8080` |
| `RAILWAY_PUBLIC_DOMAIN` | Public domain for the app | `agbot-production.up.railway.app` |
| `RAILWAY_PROJECT_NAME` | Railway project name | `agbot` |
| `RAILWAY_SERVICE_NAME` | Railway service name | `agbot` |

## Important Notes

- Railway manages external networking - you don't need to configure DNS or SSL
- The app runs as a standard Next.js application
- Use environment variables for sensitive data (database URL, API keys)
- Drizzle provides type safety - leverage TypeScript types from the schema
