# Testing Guidelines

Testing strategies and frameworks for the stack.

## Testing Pyramid

```
     /\
    /  \     E2E (Playwright)
   /----\
  /      \   Integration (API + DB)
 /--------\
/          \ Unit (Jest, pytest)
```

Target distribution: 70% unit, 20% integration, 10% E2E

## FastAPI Testing

### Test Structure

```
apps/api/
└─ tests/
   ├─ unit/
   │  ├─ services/
   │  │  └─ test_user_service.py
   │  └─ repositories/
   │     └─ test_user_repository.py
   ├─ integration/
   │  ├─ api/
   │  │  └─ test_users_api.py
   │  └─ conftest.py
   └─ conftest.py
```

### Unit Tests

```python
# tests/unit/services/test_user_service.py
import pytest
from unittest.mock import Mock
from app.services.user_service import UserService
from app.schemas.user import UserCreate

class TestUserService:
    def setup_method(self):
        self.db = Mock()
        self.service = UserService(self.db)
    
    def test_create_user_success(self):
        # Arrange
        user_in = UserCreate(email="test@example.com", password="secret")
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.service.create(user_in)
        
        # Assert
        assert result.email == "test@example.com"
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()
    
    def test_create_user_duplicate_email(self):
        # Arrange
        user_in = UserCreate(email="exists@example.com", password="secret")
        self.db.query.return_value.filter.return_value.first.return_value = Mock()
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            self.service.create(user_in)
```

### Integration Tests

```python
# tests/integration/api/test_users_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.db import get_db

client = TestClient(app)

@pytest.fixture
def test_db():
    # Create test database session
    from app.core.db import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def override_get_db(test_db):
    def _get_db():
        try:
            yield test_db
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db

class TestUsersAPI:
    def test_create_user(self, test_db):
        response = client.post(
            "/users/",
            json={"email": "new@example.com", "password": "secret123"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "new@example.com"
        assert "password" not in data
    
    def test_get_users(self, test_db):
        # Create test user
        client.post("/users/", json={"email": "test@example.com", "password": "secret123"})
        
        response = client.get("/users/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
```

### Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest
from app.core.db import Base, engine

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create all tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop all tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    from app.core.db import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
```

## Next.js Testing

### Test Structure

```
apps/web/
└─ tests/
   ├─ unit/
   │  ├─ components/
   │  │  └─ Button.test.tsx
   │  └─ lib/
   │     └─ utils.test.ts
   ├─ integration/
   │  └─ api/
   └─ e2e/
      └─ dashboard.spec.ts
```

### Unit Tests with Vitest

```typescript
// tests/unit/components/Button.test.tsx
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from '@/components/ui/Button';

describe('Button', () => {
  it('renders with correct text', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
  
  it('applies variant styles', () => {
    render(<Button variant="danger">Delete</Button>);
    const button = screen.getByText('Delete');
    expect(button).toHaveClass('bg-red-600');
  });
});
```

### API Integration Tests

```typescript
// tests/integration/api/users.test.ts
import { describe, it, expect } from 'vitest';
import { UsersService } from '@acme/client-sdk';

describe('Users API', () => {
  it('fetches users list', async () => {
    const users = await UsersService.getUsers();
    expect(Array.isArray(users)).toBe(true);
  });
  
  it('creates a new user', async () => {
    const newUser = await UsersService.createUser({
      email: 'test@example.com',
      password: 'password123'
    });
    expect(newUser.email).toBe('test@example.com');
    expect(newUser.id).toBeDefined();
  });
});
```

### E2E Tests with Playwright

```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard');
  });
  
  test('displays user information', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Dashboard');
    await expect(page.locator('[data-testid="user-email"]')).toBeVisible();
  });
  
  test('navigates to settings', async ({ page }) => {
    await page.click('text=Settings');
    await expect(page).toHaveURL('/settings');
  });
  
  test('creates new item', async ({ page }) => {
    await page.fill('[name="title"]', 'Test Item');
    await page.click('button[type="submit"]');
    
    await expect(page.locator('text=Test Item')).toBeVisible();
  });
});
```

## Test Configuration

### FastAPI (pytest)

```ini
# apps/api/pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
```

### Next.js (Vitest)

```typescript
// apps/web/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
    },
  },
});
```

### Playwright

```typescript
// apps/web/playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Test Commands

```bash
# FastAPI
cd apps/api
pytest                          # Run all tests
pytest -m unit                 # Unit tests only
pytest -m integration          # Integration tests only
pytest --cov=app               # With coverage

# Next.js
cd apps/web
pnpm test                      # Run all tests
pnpm test:unit                 # Unit tests
pnpm test:e2e                  # E2E tests (Playwright)
pnpm test:coverage             # With coverage
```

## Best Practices

1. **Test behavior, not implementation** - Test what code does, not how
2. **One assertion per test** - Keep tests focused
3. **Use descriptive names** - `test_user_can_login_with_valid_credentials`
4. **Arrange-Act-Assert** - Structure tests clearly
5. **Mock external dependencies** - APIs, databases in unit tests
6. **Test edge cases** - Empty inputs, errors, boundaries
7. **Fast feedback** - Tests should run in <10 seconds locally
8. **Flaky test = bug** - Never ignore intermittent failures

## Coverage Targets

| Type | Minimum | Target |
|------|---------|--------|
| Unit | 70% | 80% |
| Integration | 50% | 60% |
| E2E | Critical paths | Critical paths |

## Related Documents

- [FastAPI Guidelines](./02-fastapi-guidelines.md) - Backend testing
- [Next.js Guidelines](./03-nextjs-guidelines.md) - Frontend testing
- [CI/CD](./05-cicd.md) - Test automation
