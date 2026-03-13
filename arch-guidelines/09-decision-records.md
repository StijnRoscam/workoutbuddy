# Decision Records

Architecture Decision Records (ADRs) documenting key technical choices.

## Format

```markdown
# ADR-XXX: Title

**Status:** Proposed / Accepted / Deprecated / Superseded by ADR-YYY

**Date:** YYYY-MM-DD

**Deciders:** [Names]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing or have agreed to implement?

## Consequences

What becomes easier or more difficult to do and any risks introduced by the change?

### Positive
- Benefit 1
- Benefit 2

### Negative
- Drawback 1
- Drawback 2

### Risks
- Risk 1 and mitigation
```

---

## ADR-001: Monorepo Structure

**Status:** Accepted

**Date:** 2024-01-15

**Deciders:** Engineering Team

### Context

We needed to decide how to organize a full-stack application with FastAPI backend, Next.js frontend, shared packages, and infrastructure code. Options considered:

1. **Multi-repo** - Separate repos for API, web, infra
2. **Monorepo with Nx** - Nx workspace management
3. **Monorepo with Turborepo** - Turborepo + pnpm workspaces
4. **Single repo without tooling** - Flat structure

### Decision

Use **pnpm workspaces + Turborepo** for monorepo management.

Structure:
```
├── apps/
│   ├── api/          # FastAPI
│   └── web/          # Next.js
├── packages/
│   ├── ui/           # Shared components
│   ├── client-sdk/   # Generated API client
│   └── config/       # Shared configs
└── infra/
    └── terraform/    # Infrastructure
```

### Consequences

**Positive:**
- Atomic commits across frontend and backend
- Shared code without publishing packages
- Single CI/CD pipeline
- Easy to generate TypeScript client from FastAPI OpenAPI
- Consistent tooling across projects

**Negative:**
- Larger repository size
- More complex initial setup
- Requires understanding of workspace tools

**Risks:**
- Build times could increase (mitigated by Turborepo caching)

---

## ADR-002: FastAPI Architecture Pattern

**Status:** Accepted

**Date:** 2024-01-20

**Deciders:** Backend Team

### Context

We needed to establish patterns for organizing FastAPI code. Options considered:

1. **Flat structure** - All code in single directory
2. **Layer-based** - Separate by technical layer (routes, models, services)
3. **Domain-based** - Organize by business domain
4. **Clean Architecture** - Strict separation with dependency inversion

### Decision

Use **layer-based organization** with clear separation:

```
app/
├── api/routes/       # HTTP layer
├── services/         # Business logic
├── repositories/     # Data access
├── schemas/          # Pydantic models
├── models/           # SQLAlchemy models
└── core/             # Config, security, db
```

Rules:
- Routes are thin (validation + delegation only)
- Services contain all business logic
- Repositories abstract database operations
- No business logic in routes or repositories

### Consequences

**Positive:**
- Clear separation of concerns
- Easy to test each layer independently
- Repository pattern allows swapping database later
- New developers can find code easily

**Negative:**
- More boilerplate than simple MVC
- Need to understand dependency injection

**Risks:**
- Over-engineering for small features (mitigated by pragmatic enforcement)

---

## ADR-003: TypeScript Client Generation

**Status:** Accepted

**Date:** 2024-01-25

**Deciders:** Full Team

### Context

We needed to keep frontend and backend types in sync. Options considered:

1. **Manual TypeScript types** - Write types by hand matching API
2. **GraphQL with codegen** - Use GraphQL with type generation
3. **tRPC** - Type-safe API calls via TypeScript
4. **OpenAPI generation** - Generate TS client from FastAPI OpenAPI

### Decision

Use **OpenAPI generation** with `openapi-typescript`.

Process:
1. FastAPI auto-generates OpenAPI spec at `/openapi.json`
2. CI generates TypeScript client to `packages/client-sdk/`
3. Frontend imports from `@acme/client-sdk`

### Consequences

**Positive:**
- Single source of truth (FastAPI schemas)
- Type-safe API calls in frontend
- No manual type maintenance
- Works with any HTTP client

**Negative:**
- Requires running backend to generate (or using checked-in spec)
- Less flexible than hand-written types

**Risks:**
- Generation could fail silently (mitigated by CI checks)

---

## ADR-004: Infrastructure as Code

**Status:** Accepted

**Date:** 2024-02-01

**Deciders:** Platform Team

### Context

We needed to manage cloud infrastructure. Options considered:

1. **AWS Console / ClickOps** - Manual setup
2. **AWS CDK** - TypeScript infrastructure
3. **Pulumi** - Multi-language infrastructure
4. **Terraform** - HCL infrastructure

### Decision

Use **Terraform** with module-based organization.

Structure:
```
infra/terraform/
├── modules/          # Reusable components
└── environments/     # Environment-specific configs
    ├── dev/
    ├── staging/
    └── prod/
```

Principles:
- Same module used across all environments
- Remote state with locking (S3 + DynamoDB)
- No hardcoded secrets
- Plan on PR, apply on merge

### Consequences

**Positive:**
- Repeatable, versioned infrastructure
- Code review for infrastructure changes
- Easy to recreate environments
- Large provider ecosystem

**Negative:**
- HCL learning curve
- State management complexity
- Drift detection needed

**Risks:**
- State corruption (mitigated by backups and locking)

---

## ADR-005: Database Migration Strategy

**Status:** Accepted

**Date:** 2024-02-10

**Deciders:** Backend Team

### Context

We needed to manage database schema changes. Options considered:

1. **Auto-migrate on startup** - Run migrations when app starts
2. **Separate migration job** - Kubernetes job or ECS task
3. **Manual migrations** - Developer runs locally
4. **Schema diff tools** - Compare and generate migrations

### Decision

Use **Alembic with explicit migration step** in deployment pipeline.

Flow:
1. Developer creates migration: `alembic revision --autogenerate`
2. Review migration in PR
3. Deployment runs migrations before app deploy
4. Rollback plan required for risky changes

Rules:
- Backward-compatible migrations only in production
- Add nullable columns or columns with defaults
- Never drop columns/tables in production
- Test migrations in staging first

### Consequences

**Positive:**
- Controlled, reviewable schema changes
- No accidental data loss
- Easy rollback with down migrations
- Version controlled schema history

**Negative:**
- Requires discipline for backward compatibility
- Multi-step process for renaming columns

**Risks:**
- Long migrations could cause downtime (mitigated by running during low-traffic)

---

## ADR-006: Deployment Strategy

**Status:** Accepted

**Date:** 2024-02-15

**Deciders:** Engineering Team

### Context

We needed to decide how to deploy applications. Options considered:

1. **Heroku / Railway / Render** - PaaS solutions
2. **EC2 with manual setup** - Virtual machines
3. **ECS Fargate** - Serverless containers
4. **Kubernetes (EKS)** - Container orchestration
5. **Vercel + ECS** - Hybrid approach

### Decision

Use **hybrid deployment**:

- **Frontend (Next.js)**: Vercel
  - Optimized for Next.js
  - Edge deployment
  - Preview deployments per PR

- **Backend (FastAPI)**: ECS Fargate
  - Container-based
  - Auto-scaling
  - Private networking with database

- **Database**: RDS PostgreSQL
  - Managed service
  - Automated backups

### Consequences

**Positive:**
- Best tool for each layer
- Vercel handles frontend complexities
- ECS provides flexibility for backend
- Cost-effective for our scale

**Negative:**
- Two deployment platforms to manage
- VPC peering or public API communication
- Different scaling characteristics

**Risks:**
- Network latency between services (mitigated by regional deployment)

---

## ADR-007: Testing Strategy

**Status:** Accepted

**Date:** 2024-02-20

**Deciders:** QA + Engineering Team

### Context

We needed to establish testing practices. Options considered:

1. **Unit tests only** - Fast but misses integration issues
2. **Heavy E2E** - Comprehensive but slow and flaky
3. **Testing pyramid** - Balanced approach
4. **Snapshot testing** - Easy to maintain but less valuable

### Decision

Follow **testing pyramid**:

- **70% Unit tests** - Fast, isolated, test business logic
- **20% Integration tests** - Test API + database together
- **10% E2E tests** - Critical user journeys only

Tools:
- Backend: pytest (unit + integration)
- Frontend: Vitest (unit), Playwright (E2E)

### Consequences

**Positive:**
- Fast feedback on unit tests
- Integration tests catch API contract issues
- E2E tests verify critical paths
- Maintainable test suite

**Negative:**
- Requires discipline to maintain pyramid ratio
- Integration tests need test database

**Risks:**
- Test suite could become slow (mitigated by parallel execution and caching)

---

## Creating New ADRs

When making significant architectural decisions:

1. Create new file: `docs/architecture/adr-XXX-title.md`
2. Use format above
3. Start with status "Proposed"
4. Discuss with team
5. Update to "Accepted" after approval
6. Link from this index

**When to write an ADR:**
- New technology choices
- Significant pattern changes
- Infrastructure changes
- Security model changes
- Data model changes

**When NOT to write an ADR:**
- Bug fixes
- Small refactorings
- Adding a new endpoint
- Updating dependencies

## Related Documents

- [Monorepo Structure](./01-monorepo-structure.md) - ADR-001 implementation
- [FastAPI Guidelines](./02-fastapi-guidelines.md) - ADR-002 implementation
- [Infrastructure](./04-infrastructure.md) - ADR-004 implementation
