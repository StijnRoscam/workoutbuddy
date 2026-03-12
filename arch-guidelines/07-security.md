# Security Guidelines

Security practices and patterns for the stack.

## Security Layers

```
┌─────────────────────────────────────┐
│  Application (Input validation,     │
│  auth, secure headers)              │
├─────────────────────────────────────┤
│  Network (TLS, VPC, security groups)│
├─────────────────────────────────────┤
│  Infrastructure (IAM, least privilege)
├─────────────────────────────────────┤
│  Secrets (Encryption, rotation)     │
└─────────────────────────────────────┘
```

## Authentication

### FastAPI JWT Setup

```python
# app/core/security.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt
```

```python
# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.config import settings

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user
```

### Route Protection

```python
# app/api/routes/users.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.models.user import User

@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
```

## Authorization (RBAC)

```python
# app/core/roles.py
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

class Permission(str, Enum):
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    ADMIN_READ = "admin:read"
    ADMIN_WRITE = "admin:write"

ROLE_PERMISSIONS = {
    Role.USER: [Permission.USER_READ, Permission.USER_WRITE],
    Role.ADMIN: [Permission.USER_READ, Permission.USER_WRITE, Permission.ADMIN_READ],
    Role.SUPERADMIN: list(Permission),
}

def has_permission(user: User, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS.get(user.role, [])
```

## Input Validation

### Pydantic Schemas

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, validator
import re

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    
    @validator('password')
    def password_strength(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain digit')
        return v
```

## CORS Configuration

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)
```

## Security Headers

```python
# app/main.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

## Secrets Management

### Development

```bash
# .env (never commit this file!)
DATABASE_URL=postgresql://user:pass@localhost/db
SECRET_KEY=your-secret-key-here
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
```

### Production

```hcl
# AWS Secrets Manager
resource "aws_secretsmanager_secret" "api" {
  name = "${var.environment}/api/config"
}

resource "aws_secretsmanager_secret_version" "api" {
  secret_id = aws_secretsmanager_secret.api.id
  secret_string = jsonencode({
    database_url = "postgresql://..."
    secret_key   = random_password.secret_key.result
  })
}
```

```python
# app/core/config.py
import boto3
import json

def load_secrets_from_aws():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=f"{settings.environment}/api/config")
    return json.loads(response['SecretString'])
```

## Database Security

1. **Use parameterized queries** (SQLAlchemy does this automatically)
2. **Encrypt at rest** - Enable RDS encryption
3. **Encrypt in transit** - Use SSL/TLS connections
4. **Rotate credentials** - Use IAM auth or rotate passwords regularly
5. **Least privilege** - DB user has minimal required permissions

## Infrastructure Security

### AWS Security Groups

```hcl
resource "aws_security_group" "api" {
  name_prefix = "${var.environment}-api-"
  vpc_id      = var.vpc_id
  
  # Only accept traffic from ALB
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  # Allow outbound to database (specific SG)
  egress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.database.id]
  }
}
```

### IAM Roles

```hcl
resource "aws_iam_role" "api_task" {
  name = "${var.environment}-api-task"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "api_secrets" {
  name = "api-secrets-access"
  role = aws_iam_role.api_task.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue"
      ]
      Resource = aws_secretsmanager_secret.api.arn
    }]
  })
}
```

## Frontend Security

### Next.js Security Headers

```typescript
// next.config.ts
const nextConfig = {
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
};

export default nextConfig;
```

### XSS Prevention

```typescript
// Always sanitize user input
import DOMPurify from 'isomorphic-dompurify';

function SafeHTML({ html }: { html: string }) {
  const clean = DOMPurify.sanitize(html);
  return <div dangerouslySetInnerHTML={{ __html: clean }} />;
}
```

## Security Checklist

### Repository
- [ ] No secrets in code (use git-secrets or pre-commit)
- [ ] Dependency scanning (Dependabot/Renovate)
- [ ] Branch protection rules
- [ ] Required reviews before merge
- [ ] Signed commits (optional)

### Application
- [ ] All inputs validated (Pydantic/Zod)
- [ ] Authentication required for protected routes
- [ ] Proper authorization checks
- [ ] Rate limiting enabled
- [ ] Secure session management
- [ ] CSRF protection (if using forms)
- [ ] SQL injection prevention (parameterized queries)

### Infrastructure
- [ ] TLS 1.2+ everywhere
- [ ] Secrets in Secrets Manager (not env vars in prod)
- [ ] Least privilege IAM
- [ ] Network segmentation (VPC, private subnets)
- [ ] Security groups restrict access
- [ ] CloudTrail logging enabled
- [ ] WAF for public endpoints

## Security Scanning

```bash
# Python dependency vulnerabilities
pip install safety
safety check

# Infrastructure scanning
checkov --directory infra/terraform/
tfsec infra/terraform/

# Container scanning
trivy image myapp:latest
```

## Incident Response

1. **Detect** - Monitoring and alerting
2. **Contain** - Isolate affected systems
3. **Eradicate** - Remove threat
4. **Recover** - Restore services
5. **Learn** - Post-incident review

## Related Documents

- [FastAPI Guidelines](./02-fastapi-guidelines.md) - Authentication implementation
- [Infrastructure](./04-infrastructure.md) - Security groups and IAM
- [CI/CD](./05-cicd.md) - Security scanning in pipelines
