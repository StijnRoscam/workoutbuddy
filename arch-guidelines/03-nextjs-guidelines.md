# Next.js Guidelines

Frontend architecture using Next.js 16 (App Router), React 19, and Tailwind CSS v4.

## App Structure

```
apps/web/
├─ app/                      # Next.js App Router
│  ├─ layout.tsx            # Root layout (fonts, metadata, html shell)
│  ├─ page.tsx              # Home / landing page
│  ├─ globals.css           # Tailwind v4 imports + design tokens
│  ├─ error.tsx             # Root error boundary (must be "use client")
│  ├─ dashboard/
│  │  ├─ page.tsx           # Dashboard overview page
│  │  └─ layout.tsx         # Dashboard layout (sidebar + main)
│  └─ api/                  # Route handlers (use sparingly)
│     └─ route.ts
├─ components/
│  ├─ ui/                   # shadcn/ui components (owned, editable source)
│  │  ├─ button.tsx         # Button (uses @base-ui/react)
│  │  ├─ button-variants.ts # buttonVariants CVA — server-safe, no "use client"
│  │  ├─ card.tsx
│  │  └─ input.tsx
│  └─ features/             # Feature-specific components
│     └─ workout-list/
│        └─ WorkoutCard.tsx
├─ lib/
│  ├─ api.ts                # apiFetch wrapper + re-exports from client-sdk
│  ├─ utils.ts              # cn() utility (from shadcn/ui init)
│  └─ hooks/                # Custom hooks (client-only)
│     └─ useApi.ts
├─ public/                   # Static assets
├─ components.json           # shadcn/ui registry config
├─ next.config.ts
├─ tsconfig.json
├─ eslint.config.mjs
├─ postcss.config.mjs
├─ .env.example
└─ package.json
```

## App Router Patterns

### Server Components (Default)

Use Server Components for:
- Data fetching
- Server-side rendering
- SEO-critical content
- Any component that does not need interactivity

```typescript
// app/dashboard/page.tsx
import { apiFetch } from "@/lib/api";
import type { Workout } from "@workoutbuddy/client-sdk";

export default async function DashboardPage() {
  // Fetch data on the server — no useEffect, no loading state needed
  const workouts = await apiFetch<Workout[]>("/workouts");

  return (
    <div>
      <h1>Dashboard</h1>
      <WorkoutList workouts={workouts} />
    </div>
  );
}
```

### Client Components

Add `"use client"` only when the component needs:
- React hooks (`useState`, `useEffect`, etc.)
- Browser APIs
- Event handlers

```typescript
"use client";

import { useState } from "react";

export function Counter() {
  const [count, setCount] = useState(0);

  return (
    <button onClick={() => setCount(c => c + 1)}>
      Count: {count}
    </button>
  );
}
```

## Data Fetching

### Server-side (`lib/api.ts`)

```typescript
// lib/api.ts
import { API_BASE_URL } from "@workoutbuddy/client-sdk";

export { API_BASE_URL };

export async function apiFetch<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}
```

```typescript
// app/workouts/page.tsx  (Server Component)
import { apiFetch } from "@/lib/api";
import type { Workout } from "@workoutbuddy/client-sdk";

export default async function WorkoutsPage() {
  const workouts = await apiFetch<Workout[]>("/workouts");

  return (
    <ul>
      {workouts.map(w => <li key={w.id}>{w.name}</li>)}
    </ul>
  );
}
```

### Client-side (`lib/hooks/useApi.ts`)

A minimal hook ships by default. Swap it for **TanStack Query** when caching,
mutations, or background refetching are needed — the interface is compatible.

```typescript
// lib/hooks/useApi.ts
"use client";

import { useState, useEffect } from "react";
import { apiFetch } from "@/lib/api";

export function useApi<T>(path: string) {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    let cancelled = false;
    apiFetch<T>(path)
      .then(d => { if (!cancelled) { setData(d); setIsLoading(false); } })
      .catch(e => { if (!cancelled) { setError(e); setIsLoading(false); } });
    return () => { cancelled = true; };
  }, [path]);

  return { data, isLoading, error };
}
```

```typescript
// components/features/workout-list/WorkoutListClient.tsx
"use client";

import { useApi } from "@/lib/hooks/useApi";
import type { Workout } from "@workoutbuddy/client-sdk";

export function WorkoutListClient() {
  const { data: workouts, isLoading } = useApi<Workout[]>("/workouts");

  if (isLoading) return <p>Loading...</p>;

  return (
    <ul>
      {workouts?.map(w => <li key={w.id}>{w.name}</li>)}
    </ul>
  );
}
```

## Component Organization

### UI Components (`components/ui/`)

shadcn/ui components live here as owned, editable source files — not a package
import. Add new components with:

```bash
pnpm dlx shadcn@latest add <component-name>
```

**Important — `buttonVariants` and the client boundary:**

`button.tsx` carries `"use client"` because it uses `@base-ui/react`. To apply
button styles to a `<Link>` inside a Server Component, import `buttonVariants`
from the separate server-safe file:

```typescript
// Server Component — safe to import
import { buttonVariants } from "@/components/ui/button-variants";
import Link from "next/link";

<Link href="/dashboard" className={buttonVariants({ variant: "default" })}>
  Dashboard
</Link>
```

```typescript
// Client Component — use the Button component directly
"use client";
import { Button } from "@/components/ui/button";

<Button onClick={handleClick}>Save</Button>
```

For rendering a button as a different element in a client context, use the
`render` prop from `@base-ui/react`:

```typescript
"use client";
import { Button } from "@/components/ui/button";
import Link from "next/link";

<Button render={<Link href="/dashboard" />}>Dashboard</Button>
```

### Feature Components (`components/features/`)

Domain-specific components that compose UI components.

```typescript
// components/features/workout-list/WorkoutCard.tsx
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import type { Workout } from "@workoutbuddy/client-sdk";

export function WorkoutCard({ workout }: { workout: Workout }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{workout.name}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{workout.duration_minutes} min</p>
      </CardContent>
    </Card>
  );
}
```

## Layouts and Pages

### Root Layout

```typescript
// app/layout.tsx
import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({ variable: "--font-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: { default: "WorkoutBuddy", template: "%s | WorkoutBuddy" },
  description: "Your personal workout tracking companion.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${geistSans.variable} ${geistMono.variable} min-h-screen antialiased`}>
        {children}
      </body>
    </html>
  );
}
```

### Nested Layouts

```typescript
// app/dashboard/layout.tsx
export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <aside className="bg-sidebar text-sidebar-foreground border-sidebar-border w-60 shrink-0 border-r">
        {/* Sidebar nav */}
      </aside>
      <main className="flex-1 overflow-auto p-8">{children}</main>
    </div>
  );
}
```

## Route Handlers (API Routes)

Use sparingly — prefer FastAPI for business logic.

```typescript
// app/api/webhook/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();
  // Process webhook
  return NextResponse.json({ success: true });
}
```

## Styling with Tailwind v4

Tailwind v4 is **CSS-first** — there is no `tailwind.config.ts`. All theme
customisation is done inside `globals.css` via `@theme` blocks.

### Design tokens (`app/globals.css`)

```css
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";

@custom-variant dark (&:is(.dark *));

@theme inline {
  /* Brand palette — swap these 10 variables to retheme the entire app.
     Use https://oklch.com to pick new values. */
  --color-brand-50:  var(--brand-50);
  --color-brand-500: var(--brand-500);
  --color-brand-600: var(--brand-600);
  --color-brand-700: var(--brand-700);
  --color-brand-900: var(--brand-900);

  /* shadcn/ui semantic tokens (do not remove) */
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary:    var(--primary);
  /* ... rest of shadcn tokens ... */
}

:root {
  /* Brand color values (Tailwind blue by default) */
  --brand-50:  oklch(0.97 0.013 246.0);
  --brand-500: oklch(0.623 0.214 259.8);
  --brand-600: oklch(0.546 0.245 262.9);
  --brand-700: oklch(0.488 0.243 264.4);
  --brand-900: oklch(0.379 0.146 265.5);

  /* shadcn/ui base token values */
  --background: oklch(1 0 0);
  --foreground: oklch(0.145 0 0);
  /* ... */
}
```

Tailwind v4 uses **`oklch` color space** instead of hex or `hsl()`.

### Using brand colors in components

```tsx
<div className="bg-brand-600 text-white hover:bg-brand-700">
  Primary action
</div>
```

## Key Patterns

1. **Server Components by Default**: Start with Server Components; add `"use client"` only when needed
2. **Co-locate Data Fetching**: Fetch data close to where it's used
3. **`buttonVariants` for links, `<Button>` for actions**: Keep the client boundary clean
4. **Use Generated Client**: Import types from `@workoutbuddy/client-sdk`; regenerate with `pnpm generate:client` after API changes
5. **Tailwind v4 CSS tokens**: Theme via `--brand-*` variables in `globals.css`, not via a config file
6. **shadcn/ui is owned source**: Edit components directly; re-add via `pnpm dlx shadcn@latest add`
7. **Parallel Data Fetching**: Use `Promise.all()` for independent server-side requests

## Environment Variables

```bash
# apps/web/.env.local  (never commit)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=WorkoutBuddy

# Server-only (no NEXT_PUBLIC_ prefix)
API_SECRET_KEY=secret
```

- `NEXT_PUBLIC_*` — available in browser and server
- Everything else — server-side only

## Related Documents

- [Monorepo Structure](./01-monorepo-structure.md) - Workspace configuration
- [FastAPI Guidelines](./02-fastapi-guidelines.md) - Backend integration
- [Testing](./06-testing.md) - Frontend testing patterns
- [Development Workflow](./08-development-workflow.md) - Local development
