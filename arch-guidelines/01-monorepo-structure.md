# Monorepo Structure

Overview of the repository layout, workspace configuration, and tooling setup.

## Repository Layout

```
repo/
├─ apps/
│  ├─ api/                 # FastAPI application
│  └─ web/                 # Next.js application
│
├─ packages/
│  ├─ client-sdk/          # Generated TypeScript API client
│  ├─ ui/                  # Shared utilities (cn helper)
│  └─ config/              # Shared TypeScript config
│
├─ infra/
│  └─ terraform/
│     ├─ modules/          # Reusable infrastructure modules
│     ├─ environments/
│     │  ├─ dev/
│     │  ├─ staging/
│     │  └─ prod/
│     └─ bootstrap/        # Remote state setup
│
├─ docker/
│  ├─ api.Dockerfile
│  └─ web.Dockerfile
│
├─ scripts/                # Helper scripts
├─ .github/workflows/      # CI/CD workflows
├─ docker-compose.yml
├─ Makefile
├─ package.json            # Root workspace config
├─ pnpm-workspace.yaml
├─ turbo.json
└─ pyproject.toml          # Python tooling config (optional)
```

## Directory Purposes

### `apps/`

Deployable applications. Each app is self-contained with its own:
- Dependencies
- Build configuration
- Tests
- Dockerfile

**apps/api/**: FastAPI backend service
**apps/web/**: Next.js frontend application

### `packages/`

Shared code libraries consumed by apps and other packages.

**packages/client-sdk/**: TypeScript client from FastAPI OpenAPI
- Placeholder until `pnpm generate:client` is run against a live API
- Imported as `@workoutbuddy/client-sdk`

**packages/ui/**: Shared utilities
- Exports `cn()` (clsx + tailwind-merge helper)
- Imported as `@workoutbuddy/ui`
- **Note:** shadcn/ui components live inside each app (`apps/web/components/ui/`)
  so each app retains full control over component source — this is the intended
  shadcn/ui design philosophy

**packages/config/**: Shared configuration
- Base TypeScript config (`typescript.json`)
- Tailwind v4 is configured per-app in CSS (`globals.css`) — no shared `tailwind.config.ts`
- ESLint uses flat config per-app (`eslint.config.mjs`) — no shared ESLint package needed

## Workspace Configuration

### Root package.json

```json
{
  "name": "workoutbuddy",
  "private": true,
  "packageManager": "pnpm@10.32.1",
  "scripts": {
    "dev": "turbo run dev --parallel",
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint",
    "typecheck": "turbo run typecheck",
    "generate:client": "openapi-typescript http://localhost:8000/openapi.json -o packages/client-sdk/src/index.ts"
  },
  "devDependencies": {
    "turbo": "^2.0.0"
  },
  "pnpm": {
    "onlyBuiltDependencies": ["sharp", "unrs-resolver"]
  }
}
```

### pnpm-workspace.yaml

```yaml
packages:
  - "apps/*"
  - "packages/*"
```

### turbo.json

Turborepo v2 uses `tasks` (not `pipeline`). The schema URL also changed.

```json
{
  "$schema": "https://turborepo.dev/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "globalEnv": ["NODE_ENV"],
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": [".next/**", "!.next/cache/**", "dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "test": {
      "dependsOn": ["build"]
    },
    "lint": {},
    "typecheck": {
      "dependsOn": ["^typecheck"]
    }
  }
}
```

## Key Decisions

### Why pnpm?

- Fast, disk-space efficient
- Built-in workspace support
- Strict dependency management
- Content-addressable store

### Why Turborepo?

- Task caching and parallelization
- Task graph dependencies (`dependsOn`)
- Remote caching support
- Incremental builds

### Workspace Dependencies

```json
{
  "dependencies": {
    "@workoutbuddy/ui": "workspace:*",
    "@workoutbuddy/client-sdk": "workspace:*",
    "@workoutbuddy/config": "workspace:*"
  }
}
```

Use `workspace:*` to reference other packages in the monorepo. This:
- Links packages locally during development
- Replaces with actual versions on publish
- Enables atomic commits across packages

## Adding New Apps/Packages

### New App

1. Create directory: `apps/my-app/`
2. Initialize package.json:
   ```json
   {
     "name": "@workoutbuddy/my-app",
     "private": true,
     "scripts": {
       "dev": "...",
       "build": "...",
       "typecheck": "tsc --noEmit"
     }
   }
   ```
3. Tasks are picked up automatically by turbo.json — add app-specific overrides only if needed
4. Reference workspace packages: `"@workoutbuddy/ui": "workspace:*"`

### New Package

1. Create directory: `packages/my-package/`
2. Initialize package.json with `"name": "@workoutbuddy/my-package"`
3. Create `src/index.ts` entry point
4. Export public API
5. Reference in consuming apps: `"@workoutbuddy/my-package": "workspace:*"`

## Python in the Monorepo

Python apps (like `apps/api/`) are self-contained with:
- `pyproject.toml` for dependencies and tooling
- `uv` for package management
- `ruff` for linting/formatting
- `mypy` for type checking
- `pytest` for testing

The root may have a `pyproject.toml` for shared Python tooling configuration, but each app manages its own dependencies.

## Related Documents

- [FastAPI Guidelines](./02-fastapi-guidelines.md) - API app structure
- [Next.js Guidelines](./03-nextjs-guidelines.md) - Web app structure
- [Infrastructure](./04-infrastructure.md) - Terraform organization
