# Infrastructure

Terraform structure, cloud architecture, and deployment patterns.

## Directory Structure

```
infra/terraform/
├─ modules/
│  ├─ vpc/                    # Network infrastructure
│  ├─ database/               # RDS PostgreSQL
│  ├─ cache/                  # ElastiCache Redis
│  ├─ api_service/            # FastAPI ECS/Fargate
│  ├─ web_service/            # Next.js hosting
│  ├─ dns/                    # Route53
│  ├─ cdn/                    # CloudFront
│  └─ monitoring/             # CloudWatch, alarms
│
├─ environments/
│  ├─ dev/
│  │  ├─ main.tf
│  │  ├─ variables.tf
│  │  ├─ outputs.tf
│  │  ├─ backend.tf           # Remote state config
│  │  └─ terraform.tfvars
│  ├─ staging/
│  └─ prod/
│
└─ bootstrap/
   ├─ main.tf                 # S3 bucket for state
   ├─ dynamodb.tf             # State locking
   └─ iam.tf                  # Terraform execution role
```

## Module Structure

### Reusable Module Pattern

```hcl
# infra/terraform/modules/api_service/main.tf
variable "environment" {
  description = "Environment name"
  type        = string
}

variable "image_tag" {
  description = "Docker image tag to deploy"
  type        = string
}

variable "cpu" {
  description = "CPU units"
  type        = number
  default     = 256
}

variable "memory" {
  description = "Memory in MiB"
  type        = number
  default     = 512
}

# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.environment}-api"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Service
resource "aws_ecs_service" "api" {
  name            = "${var.environment}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = [aws_security_group.api.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }
}

output "service_url" {
  description = "URL of the API service"
  value       = "https://${aws_lb.main.dns_name}"
}
```

## Environment Configuration

### Development Environment

```hcl
# infra/terraform/environments/dev/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket         = "acme-terraform-state"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = "dev"
      Project     = "acme-platform"
      ManagedBy   = "terraform"
    }
  }
}

module "vpc" {
  source      = "../../modules/vpc"
  environment = "dev"
  cidr_block  = "10.0.0.0/16"
}

module "database" {
  source      = "../../modules/database"
  environment = "dev"
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnet_ids
  instance_class = "db.t3.micro"
}

module "api_service" {
  source      = "../../modules/api_service"
  environment = "dev"
  image_tag   = var.api_image_tag
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnet_ids
  database_url = module.database.connection_string
}
```

### Variables

```hcl
# infra/terraform/environments/dev/variables.tf
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "api_image_tag" {
  description = "API Docker image tag"
  type        = string
}

variable "web_image_tag" {
  description = "Web Docker image tag"
  type        = string
  default     = "latest"
}
```

### Outputs

```hcl
# infra/terraform/environments/dev/outputs.tf
output "api_url" {
  description = "API endpoint URL"
  value       = module.api_service.service_url
}

output "database_endpoint" {
  description = "Database connection endpoint"
  value       = module.database.endpoint
  sensitive   = true
}
```

## Remote State Setup

### Bootstrap Module

Run this once to set up state storage:

```hcl
# infra/terraform/bootstrap/main.tf
resource "aws_s3_bucket" "terraform_state" {
  bucket = "acme-terraform-state"
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"
  
  attribute {
    name = "LockID"
    type = "S"
  }
}
```

## AWS Architecture Patterns

### Recommended Stack

**API (FastAPI)**
- ECS Fargate or App Runner
- Application Load Balancer
- Auto-scaling (2-10 tasks)
- Secrets Manager for env vars

**Web (Next.js)**
- Option A: Vercel (recommended)
- Option B: ECS + CloudFront
- Option C: S3 + CloudFront (static export)

**Database**
- RDS PostgreSQL
- Multi-AZ in production
- Automated backups
- Read replicas for scale

**Cache**
- ElastiCache Redis
- Cluster mode for high availability

**CDN**
- CloudFront for static assets
- Custom domain + SSL

**DNS**
- Route53 hosted zone
- Health checks
- Failover routing (optional)

### Security Groups

```hcl
resource "aws_security_group" "api" {
  name_prefix = "${var.environment}-api-"
  vpc_id      = var.vpc_id
  
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

## Environment Differences

| Feature | Dev | Staging | Prod |
|---------|-----|---------|------|
| Instance sizes | Small | Medium | Large |
| Multi-AZ | No | Yes | Yes |
| Auto-scaling | 1-2 | 2-4 | 3-10 |
| Backups | 7 days | 14 days | 35 days |
| Monitoring | Basic | Standard | Enhanced |

## Key Principles

1. **Modules are reusable** - Same module used across all environments
2. **Environment separation** - Separate state per environment
3. **No hardcoded values** - Use variables for everything environment-specific
4. **Secrets in Secrets Manager** - Never in code or state
5. **Least privilege IAM** - Minimal permissions for each service
6. **Immutable infrastructure** - Replace, don't modify

## Terraform Commands

```bash
# Initialize
cd infra/terraform/environments/dev
terraform init

# Plan
terraform plan -var="api_image_tag=v1.2.3"

# Apply
terraform apply -var="api_image_tag=v1.2.3"

# Destroy (careful!)
terraform destroy
```

## CI/CD Integration

See [CI/CD Guidelines](./05-cicd.md) for automated Terraform workflows.

Basic flow:
1. PR: `terraform plan` posts results as comment
2. Merge: `terraform apply` runs automatically
3. Prod: Manual approval required before apply

## Related Documents

- [CI/CD Guidelines](./05-cicd.md) - Terraform in pipelines
- [Security](./07-security.md) - Security configurations
- [Development Workflow](./08-development-workflow.md) - Local Terraform usage
