# Architecture Guidelines Cheat Sheet

Quick reference for the monorepo structure and patterns.

## Where Things Go

### Code
| What | Where | Doc |
|------|-------|-----|
| FastAPI app | `apps/api/` | [FastAPI Guidelines](./02-fastapi-guidelines.md) |
| Next.js app | `apps/web/` | [Next.js Guidelines](./03-nextjs-guidelines.md) |
| Shared UI utility (`cn`) | `packages/ui/` | [Monorepo Structure](./01-monorepo-structure.md) |
| Auto-generated API client | `packages/client-sdk/` | [Monorepo Structure](./01-monorepo-structure.md) |
| Shared configs (tsconfig) | `packages/config/` | [Monorepo Structure](./01-monorepo-structure.md) |

### Infrastructure
| What | Where | Doc |
|------|-------|-----|
| Terraform modules | `infra/terraform/modules/` | [Infrastructure](./04-infrastructure.md) |
| Environment configs | `infra/terraform/environments/{dev,staging,prod}/` | [Infrastructure](./04-infrastructure.md) |
| Docker files | `docker/` or app-specific `Dockerfile` | [Monorepo Structure](./01-monorepo-structure.md) |

### Operations
| What | Where | Doc |
|------|-------|-----|
| CI/CD workflows | `.github/workflows/` | [CI/CD](./05-cicd.md) |
| Local dev scripts | `scripts/` or `Makefile` | [Development Workflow](./08-development-workflow.md) |
| Docker Compose | `docker-compose.yml` (root) | [Development Workflow](./08-development-workflow.md) |

## Quick Decisions

**Building a new API endpoint?**
1. Add route in `apps/api/app/api/routes/`
2. Add Pydantic schemas in `apps/api/app/schemas/`
3. Add business logic in `apps/api/app/services/`
4. Regenerate client SDK: `pnpm generate:client`

**Adding a new database model?**
1. Define model in `apps/api/app/models/`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Apply locally: `alembic upgrade head`
4. Commit migration file

**Creating a new page?**
1. Add to `apps/web/app/` (App Router)
2. Use shadcn/ui components from `apps/web/components/ui/`
3. Fetch data using `apiFetch` from `@/lib/api` (Server Components) or `useApi` hook (Client Components)
4. When API is live, import generated types from `@workoutbuddy/client-sdk`

**Adding infrastructure?**
1. Create reusable module in `infra/terraform/modules/`
2. Use module in `infra/terraform/environments/{env}/`
3. Run `terraform plan` in PR, `terraform apply` on merge

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Frontend | Next.js 16 (App Router), React 19, TypeScript, Tailwind v4 |
| UI components | shadcn/ui (via `@base-ui/react`) |
| Monorepo | pnpm v10, Turborepo v2 |
| Python | uv, Ruff, mypy, pytest |
| Database | PostgreSQL, Redis |
| Infrastructure | Terraform, AWS |
| CI/CD | GitHub Actions |

## Common Commands

```bash
# Start everything
docker compose up -d && pnpm dev

# Run API only
cd apps/api && uv run uvicorn app.main:app --reload

# Run web only
cd apps/web && pnpm dev

# Generate API client from FastAPI (API must be running)
pnpm generate:client

# Run tests
pnpm test                    # Frontend (from root)
cd apps/api && pytest        # Backend

# Typecheck all packages
pnpm typecheck

# Terraform
make tf-plan ENV=dev
make tf-apply ENV=dev
```

## Golden Rules

1. **Thin routes, thick services** - Keep API routes minimal, put logic in services
2. **Generate don't duplicate** - Generate TS client from FastAPI OpenAPI, don't hand-write
3. **Same code, different config** - Use env vars, no environment-specific logic
4. **Backward-compatible migrations** - Don't break existing code with DB changes
5. **Type safety everywhere** - Pydantic models → OpenAPI → TypeScript client
6. **Server Components by default** - Only add `"use client"` when interactivity is required
7. **`buttonVariants` on links, `Button` on actions** - Use `buttonVariants` from `button-variants.ts` to style `<Link>` in Server Components; use the `<Button>` component for interactive actions

## Navigation

- [Monorepo Structure](./01-monorepo-structure.md) - Workspace layout and tooling
- [FastAPI Guidelines](./02-fastapi-guidelines.md) - Backend patterns
- [Next.js Guidelines](./03-nextjs-guidelines.md) - Frontend patterns
- [Infrastructure](./04-infrastructure.md) - Terraform and cloud
- [CI/CD](./05-cicd.md) - Pipelines and automation
- [Testing](./06-testing.md) - Testing strategies
- [Security](./07-security.md) - Security practices
- [Development Workflow](./08-development-workflow.md) - Local development
- [Decision Records](./09-decision-records.md) - Architectural decisions
