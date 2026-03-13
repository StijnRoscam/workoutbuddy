# CI/CD Guidelines

GitHub Actions workflows, quality gates, and deployment automation.

## Workflow Structure

```
.github/workflows/
├─ ci.yml                    # Main CI pipeline (PRs)
├─ deploy-api.yml           # API deployment
├─ deploy-web.yml           # Web deployment
├─ terraform-plan.yml       # Terraform plan on PR
├─ terraform-apply.yml      # Terraform apply on merge
└─ release.yml              # Release automation
```

## Main CI Pipeline

### ci.yml

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.changes.outputs.api }}
      web: ${{ steps.changes.outputs.web }}
      infra: ${{ steps.changes.outputs.infra }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            api:
              - 'apps/api/**'
              - 'packages/client-sdk/**'
            web:
              - 'apps/web/**'
              - 'packages/ui/**'
            infra:
              - 'infra/**'

  api-checks:
    needs: changes
    if: ${{ needs.changes.outputs.api == 'true' }}
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apps/api
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install uv
        uses: astral-sh/setup-uv@v3
      
      - name: Install dependencies
        run: uv sync
      
      - name: Lint
        run: uv run ruff check .
      
      - name: Format check
        run: uv run ruff format --check .
      
      - name: Type check
        run: uv run mypy .
      
      - name: Test
        run: uv run pytest
      
      - name: Generate OpenAPI
        run: uv run python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > openapi.json
      
      - name: Upload OpenAPI artifact
        uses: actions/upload-artifact@v4
        with:
          name: openapi-spec
          path: apps/api/openapi.json

  web-checks:
    needs: changes
    if: ${{ needs.changes.outputs.web == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 9
      
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      
      - name: Lint
        run: pnpm lint
      
      - name: Type check
        run: pnpm typecheck
      
      - name: Build
        run: pnpm build
      
      - name: Test
        run: pnpm test

  terraform-checks:
    needs: changes
    if: ${{ needs.changes.outputs.infra == 'true' }}
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: infra/terraform/environments/dev
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: "1.7.0"
      
      - name: Terraform Format
        run: terraform fmt -check -recursive
      
      - name: Terraform Init
        run: terraform init
      
      - name: Terraform Validate
        run: terraform validate
      
      - name: Terraform Plan
        run: terraform plan -input=false
```

## Deployment Workflows

### deploy-api.yml

```yaml
name: Deploy API

on:
  push:
    branches: [main]
    paths:
      - 'apps/api/**'
      - 'packages/client-sdk/**'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'dev'
        type: choice
        options:
          - dev
          - staging
          - prod

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'dev' }}
    permissions:
      id-token: write
      contents: read
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build, tag, and push image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: acme-api
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG apps/api/
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          echo "image=$ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG" >> $GITHUB_OUTPUT
      
      - name: Update ECS service
        run: |
          aws ecs update-service \
            --cluster ${{ github.event.inputs.environment }}-api \
            --service ${{ github.event.inputs.environment }}-api \
            --force-new-deployment
```

### deploy-web.yml

```yaml
name: Deploy Web

on:
  push:
    branches: [main]
    paths:
      - 'apps/web/**'
      - 'packages/ui/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 9
      
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      
      - name: Build
        run: pnpm build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          working-directory: apps/web
```

## Terraform Workflows

### terraform-plan.yml

```yaml
name: Terraform Plan

on:
  pull_request:
    paths:
      - 'infra/**'

jobs:
  plan:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    strategy:
      matrix:
        environment: [dev, staging, prod]
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
      
      - name: Terraform Init
        working-directory: infra/terraform/environments/${{ matrix.environment }}
        run: terraform init
      
      - name: Terraform Plan
        working-directory: infra/terraform/environments/${{ matrix.environment }}
        run: terraform plan -no-color -input=false 2>&1 | tee plan.txt
      
      - name: Comment PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const plan = fs.readFileSync('infra/terraform/environments/${{ matrix.environment }}/plan.txt', 'utf8');
            const output = plan.length > 65000 ? plan.substring(0, 65000) + '...' : plan;
            
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `### Terraform Plan (${{ matrix.environment }})
              \`\`\`
              ${output}
              \`\`\`
              `
            });
```

### terraform-apply.yml

```yaml
name: Terraform Apply

on:
  push:
    branches: [main]
    paths:
      - 'infra/**'

jobs:
  apply-dev:
    runs-on: ubuntu-latest
    environment: dev
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS Credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1
      
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
      
      - name: Terraform Init
        working-directory: infra/terraform/environments/dev
        run: terraform init
      
      - name: Terraform Apply
        working-directory: infra/terraform/environments/dev
        run: terraform apply -auto-approve -input=false

  apply-staging:
    needs: apply-dev
    runs-on: ubuntu-latest
    environment: staging
    steps:
      # Similar to dev...

  apply-prod:
    needs: apply-staging
    runs-on: ubuntu-latest
    environment: prod  # Requires manual approval
    steps:
      # Similar to dev...
```

## Quality Gates

All PRs must pass:

1. **Lint** - No style violations (Ruff, ESLint)
2. **Format** - Code is properly formatted (Ruff, Prettier)
3. **Type Check** - No type errors (mypy, tsc)
4. **Test** - All tests pass (pytest, vitest)
5. **Build** - Production build succeeds
6. **Terraform** - No validation errors, plan succeeds

## Deployment Sequence

For a typical release:

1. **DB Migrations** - Run Alembic migrations
2. **Infra Changes** - Apply Terraform if needed
3. **API Deploy** - Deploy new API version
4. **Web Deploy** - Deploy new frontend
5. **Smoke Tests** - Verify deployment health

## Secrets Management

Configure in GitHub Settings → Secrets and Variables:

**Repository Secrets:**
- `AWS_DEPLOY_ROLE_ARN` - OIDC role for AWS access
- `VERCEL_TOKEN` - Vercel deployment token
- `DATABASE_URL` - Production database (if needed in CI)

**Environment Secrets (per environment):**
- `TF_VAR_api_image_tag` - Override image tag
- `TF_VAR_database_password` - Database credentials
- `NEXT_PUBLIC_API_URL` - API endpoint for frontend

## Deployment Rollback

### API Rollback

```bash
# Deploy previous version
aws ecs update-service \
  --cluster prod-api \
  --service prod-api \
  --task-definition acme-api:PREVIOUS_REVISION
```

### Database Rollback

Test migrations in staging before prod. Backward-compatible only:
- Add columns (nullable or with defaults)
- Add tables
- Add indexes

Never in production:
- Drop columns
- Drop tables
- Rename columns

## Related Documents

- [Infrastructure](./04-infrastructure.md) - Terraform setup
- [Testing](./06-testing.md) - Test configuration
- [Security](./07-security.md) - Security hardening
```
