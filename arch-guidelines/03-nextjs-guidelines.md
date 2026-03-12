# Next.js Guidelines

Frontend architecture using Next.js 14/15 App Router.

## App Structure

```
apps/web/
├─ app/                      # Next.js App Router
│  ├─ layout.tsx            # Root layout
│  ├─ page.tsx              # Home page
│  ├─ globals.css           # Global styles
│  ├─ dashboard/
│  │  ├─ page.tsx           # Dashboard page
│  │  └─ layout.tsx         # Dashboard layout
│  ├─ api/                   # Route handlers (if needed)
│  │  └─ route.ts
│  └─ error.tsx             # Error boundary
├─ components/
│  ├─ ui/                   # Base UI components
│  │  ├─ Button.tsx
│  │  ├─ Card.tsx
│  │  └─ Input.tsx
│  └─ features/             # Feature-specific components
│     ├─ user-profile/
│     └─ data-table/
├─ lib/
│  ├─ api.ts                # API client setup
│  ├─ auth.ts               # Auth utilities
│  ├─ utils.ts              # Utility functions
│  └─ hooks/                # Custom hooks
│     └─ useAuth.ts
├─ public/                   # Static assets
├─ styles/
├─ tests/
│  ├─ unit/
│  └─ e2e/
├─ next.config.ts
├─ tailwind.config.ts
├─ tsconfig.json
└─ package.json
```

## App Router Patterns

### Server Components (Default)

Use Server Components for:
- Data fetching
- Database access
- Server-side rendering
- SEO-critical content

```typescript
// app/dashboard/page.tsx
import { UsersService } from "@acme/client-sdk";

export default async function DashboardPage() {
  // Fetch data on server
  const users = await UsersService.getUsers();

  return (
    <div>
      <h1>Dashboard</h1>
      <UserList users={users} />
    </div>
  );
}
```

### Client Components

Use Client Components for:
- Interactive UI (buttons, forms)
- Browser APIs (localStorage, geolocation)
- React hooks (useState, useEffect)
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

### Server-side with Generated Client

```typescript
// lib/api.ts
import { OpenAPI } from "@acme/client-sdk";

OpenAPI.BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export { UsersService, AuthService } from "@acme/client-sdk";
```

```typescript
// app/users/page.tsx
import { UsersService } from "@/lib/api";

export default async function UsersPage() {
  const users = await UsersService.getUsers();

  return (
    <ul>
      {users.map(user => (
        <li key={user.id}>{user.email}</li>
      ))}
    </ul>
  );
}
```

### Client-side with TanStack Query

```typescript
// lib/hooks/useUsers.ts
"use client";

import { useQuery } from "@tanstack/react-query";
import { UsersService } from "@acme/client-sdk";

export function useUsers() {
  return useQuery({
    queryKey: ["users"],
    queryFn: () => UsersService.getUsers(),
  });
}
```

```typescript
// components/UserListClient.tsx
"use client";

import { useUsers } from "@/lib/hooks/useUsers";

export function UserListClient() {
  const { data: users, isLoading } = useUsers();

  if (isLoading) return <div>Loading...</div>;

  return (
    <ul>
      {users?.map(user => (
        <li key={user.id}>{user.email}</li>
      ))}
    </ul>
  );
}
```

## Component Organization

### UI Components (`components/ui/`)

Base, reusable components. Often from shadcn/ui or design system.

```typescript
// components/ui/Button.tsx
import { cn } from "@/lib/utils";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
}

export function Button({
  className,
  variant = "primary",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "px-4 py-2 rounded font-medium",
        variant === "primary" && "bg-blue-600 text-white",
        variant === "secondary" && "bg-gray-200 text-gray-800",
        variant === "danger" && "bg-red-600 text-white",
        className
      )}
      {...props}
    />
  );
}
```

### Feature Components (`components/features/`)

Domain-specific components that compose UI components.

```typescript
// components/features/user-profile/UserProfileCard.tsx
import { Card, Button } from "@/components/ui";
import { User } from "@acme/client-sdk";

interface UserProfileCardProps {
  user: User;
  onEdit?: () => void;
}

export function UserProfileCard({ user, onEdit }: UserProfileCardProps) {
  return (
    <Card>
      <h2>{user.email}</h2>
      <Button onClick={onEdit}>Edit Profile</Button>
    </Card>
  );
}
```

## Layouts and Pages

### Root Layout

```typescript
// app/layout.tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Acme Platform",
  description: "Modern full-stack application",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <main className="min-h-screen">{children}</main>
      </body>
    </html>
  );
}
```

### Nested Layouts

```typescript
// app/dashboard/layout.tsx
export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex">
      <aside className="w-64 bg-gray-100">Sidebar</aside>
      <main className="flex-1 p-8">{children}</main>
    </div>
  );
}
```

## Route Handlers (API Routes)

Use sparingly - prefer FastAPI for business logic.

```typescript
// app/api/webhook/route.ts
import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const body = await request.json();

  // Process webhook

  return NextResponse.json({ success: true });
}
```

## Key Patterns

1. **Server Components by Default**: Start with Server Components, only use Client Components when needed
2. **Co-locate Data Fetching**: Fetch data close to where it's used
3. **Use Generated Client**: Import from `@acme/client-sdk` for type-safe API calls
4. **Shared UI Library**: Use `@acme/ui` for consistent components
5. **Tailwind for Styling**: Utility-first CSS with consistent design tokens
6. **Zod for Validation**: Runtime validation of external data
7. **Parallel Data Fetching**: Use `Promise.all()` for independent requests

## Environment Variables

```typescript
// .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Acme Platform

# Server-only
API_SECRET_KEY=secret
```

Access in code:
- `process.env.NEXT_PUBLIC_*` - Available in browser
- `process.env.*` - Server-side only

## Styling with Tailwind

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eff6ff",
          500: "#3b82f6",
          600: "#2563eb",
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

## Related Documents

- [Monorepo Structure](./01-monorepo-structure.md) - Workspace configuration
- [FastAPI Guidelines](./02-fastapi-guidelines.md) - Backend integration
- [Testing](./06-testing.md) - Frontend testing patterns
- [Development Workflow](./08-development-workflow.md) - Local development
