# Development Workflow

Local development setup, tools, and best practices.

## Prerequisites

- **Node.js** 20+ with pnpm 9+
- **Python** 3.12+ with uv
- **Docker** and Docker Compose
- **Git** with GitHub CLI (optional)
- **AWS CLI** (for infrastructure work)
- **Terraform** 1.7+ (for infrastructure work)

## Quick Start

```bash
# 1. Clone repo
git clone https://github.com/acme/platform.git
cd platform

# 2. Install dependencies
pnpm install
cd apps/api && uv sync

# 3. Start infrastructure
docker compose up -d

# 4. Run migrations
cd apps/api && uv run alembic upgrade head

# 5. Start development
pnpm dev  # Starts both API and web
```

## Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Optional: Localstack for AWS services
  localstack:
    image: localstack/localstack:latest
    ports:
      - "4566:4566"
    environment:
      - SERVICES=s3,sqs,secretsmanager

volumes:
  postgres_data:
  redis_data:
```

## Makefile Commands

```makefile
# Makefile
.PHONY: dev api web test db migrate infra-plan infra-apply

# Development
dev:
	@docker compose up -d
	@pnpm dev

api:
	@cd apps/api && uv run uvicorn app.main:app --reload --port 8000

web:
	@cd apps/web && pnpm dev

# Database
db:
	@docker compose up -d postgres redis

migrate:
	@cd apps/api && uv run alembic upgrade head

migration:
	@cd apps/api && uv run alembic revision --autogenerate -m "$(msg)"

# Testing
test:
	@pnpm test
	@cd apps/api && uv run pytest

test-api:
	@cd apps/api && uv run pytest -v

test-web:
	@cd apps/web && pnpm test

# Linting
lint:
	@cd apps/api && uv run ruff check .
	@pnpm lint

lint-fix:
	@cd apps/api && uv run ruff check --fix .
	@cd apps/api && uv run ruff format .
	@pnpm lint:fix

typecheck:
	@cd apps/api && uv run mypy .
	@pnpm typecheck

# Infrastructure
infra-init:
	@cd infra/terraform/environments/dev && terraform init

infra-plan:
	@cd infra/terraform/environments/dev && terraform plan

infra-apply:
	@cd infra/terraform/environments/dev && terraform apply

# Client SDK generation
generate-client:
	@openapi-typescript http://localhost:8000/openapi.json -o packages/client-sdk/src/index.ts
	@cd packages/client-sdk && pnpm build

# Cleanup
clean:
	@docker compose down -v
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name .turbo -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
```

## Environment Variables

### Local Development (.env)

```bash
# apps/api/.env
DATABASE_URL=postgresql://app:app@localhost:5432/app
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000"]

# apps/web/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME="Acme Platform (Dev)"
```

## VS Code Configuration

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./apps/api/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "ruff",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.ruff": true,
    "source.organizeImports": true
  },
  "typescript.tsdk": "node_modules/typescript/lib",
  "tailwindCSS.experimental.configFile": "apps/web/tailwind.config.ts"
}
```

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "charliermarsh.ruff",
    "bradlc.vscode-tailwindcss",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "hashicorp.terraform"
  ]
}
```

## Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
        files: ^apps/api/
      - id: ruff-format
        files: ^apps/api/

  - repo: local
    hooks:
      - id: typecheck-api
        name: Type check API
        entry: bash -c "cd apps/api && uv run mypy ."
        language: system
        files: ^apps/api/.*\.py$
        pass_filenames: false
```

Install:
```bash
pip install pre-commit
pre-commit install
```

## Development Scripts

```bash
# scripts/setup.sh
#!/bin/bash
set -e

echo "Setting up development environment..."

# Check prerequisites
command -v pnpm >/dev/null 2>&1 || { echo "pnpm required but not installed"; exit 1; }
command -v uv >/dev/null 2>&1 || { echo "uv required but not installed"; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Docker required but not installed"; exit 1; }

# Install Node dependencies
echo "Installing Node dependencies..."
pnpm install

# Install Python dependencies
echo "Installing Python dependencies..."
cd apps/api
uv sync
cd ../..

# Start infrastructure
echo "Starting infrastructure..."
docker compose up -d

# Wait for Postgres
echo "Waiting for Postgres..."
sleep 5

# Run migrations
echo "Running migrations..."
cd apps/api
uv run alembic upgrade head
cd ../..

echo "Setup complete! Run 'make dev' to start development server."
```

## IDE Setup

### Cursor/VS Code Extensions

**Python:**
- Python (Microsoft)
- Ruff (Astral Software)
- Python Test Explorer

**TypeScript/JavaScript:**
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- Auto Rename Tag

**Infrastructure:**
- HashiCorp Terraform
- Docker

**General:**
- GitLens
- Todo Tree
- Error Lens

## Debugging

### FastAPI

```bash
# Run with debugger
cd apps/api
uv run python -m debugpy --listen 5678 --wait-for-client -m uvicorn app.main:app --reload
```

VS Code launch.json:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "cwd": "${workspaceFolder}/apps/api"
    }
  ]
}
```

### Next.js

VS Code launch.json:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Next.js: debug",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "pnpm",
      "runtimeArgs": ["dev"],
      "cwd": "${workspaceFolder}/apps/web",
      "console": "integratedTerminal"
    }
  ]
}
```

## Hot Reload

Both FastAPI and Next.js support hot reload:

- **API changes** - Automatically restart on Python file changes
- **Web changes** - Instant HMR for components
- **Client SDK** - Regenerate when API schemas change

## Troubleshooting

### Port Already in Use

```bash
# Kill processes on ports 3000 and 8000
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### Database Connection Issues

```bash
# Reset database
docker compose down -v
docker compose up -d postgres
sleep 5
cd apps/api && uv run alembic upgrade head
```

### Dependency Issues

```bash
# Clean reinstall
rm -rf node_modules pnpm-lock.yaml
rm -rf apps/api/.venv
pnpm install
cd apps/api && uv sync
```

## Best Practices

1. **Use make commands** - Consistent interface for common tasks
2. **Pre-commit hooks** - Catch issues before commit
3. **Feature branches** - Create branch per feature: `git checkout -b feature/description`
4. **Small commits** - Commit frequently with clear messages
5. **Test locally** - Run full test suite before pushing
6. **Update dependencies** - Use Dependabot/Renovate PRs weekly
7. **Clean environment** - Run `make clean` if weird issues occur

## Related Documents

- [Monorepo Structure](./01-monorepo-structure.md) - Workspace setup
- [Testing](./06-testing.md) - Running tests locally
- [Security](./07-security.md) - Pre-commit security hooks
