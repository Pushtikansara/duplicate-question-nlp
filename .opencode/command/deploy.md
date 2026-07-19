---
description: Create a deployment plan for production release.
---

# Deployment Planning Prompt

You are tasked with creating a comprehensive deployment plan for a production release.

## Input

{{input}}

## Deployment Plan Template

### 1. Release Overview

- **Release version**: semantic version (MAJOR.MINOR.PATCH)
- **Release date**: target date and time window
- **Release manager**: responsible person
- **Change summary**: high-level description of what is being released
- **Rollback contact**: person authorized to initiate rollback

### 2. Pre-Deployment Checklist

- [ ] Code freeze is in effect for the release branch
- [ ] All pull requests have been reviewed and approved
- [ ] All tests pass: unit, integration, e2e, performance
- [ ] Static analysis and linting pass
- [ ] Security scan has been completed (SAST, DAST, dependency scan)
- [ ] Database migrations are backward-compatible
- [ ] Feature flags are configured and tested
- [ ] All API versions are compatible (no breaking changes without deprecation notice)
- [ ] Monitoring and alerting are configured for new services
- [ ] Runbook for operational tasks is updated
- [ ] Stakeholders have been notified of the release window
- [ ] Smoke test script is prepared

### 3. Build Process

- **Build system**: Docker / Gradle / Webpack / etc.
- **Build steps**:
  1. Checkout release branch at specific commit
  2. Install dependencies (with lockfile verification)
  3. Run static analysis and tests in build pipeline
  4. Build artifacts (container images, compiled binaries, asset bundles)
  5. Version tag artifacts with commit SHA and release version
  6. Push artifacts to artifact registry (Docker Hub, ECR, Nexus, etc.)
  7. Sign artifacts for supply chain security
- **Build verification**: verify artifact digest matches build output

### 4. Environment Configuration

| Environment | Purpose | Configuration Source |
|-------------|---------|---------------------|
| development | Local dev and feature testing | .env, docker-compose |
| staging | Pre-production validation | Vault / SSM / K8s Secrets |
| production | Live user-facing environment | Vault / SSM / K8s Secrets |

- All secrets stored in secrets manager (never in version control)
- Configuration per environment via environment variables or external config service
- Feature flags to gradually expose new functionality

### 5. Infrastructure as Code

- **Terraform / Pulumi / CloudFormation**: version-controlled infrastructure
- **Changes for this release**:
  - New resources: [list]
  - Modified resources: [list]
  - Removed resources: [list]
- **Plan output**: reviewed and approved
- **State locking**: enabled to prevent concurrent modifications

### 6. CI/CD Pipeline

- **Pipeline platform**: GitHub Actions / GitLab CI / Jenkins / CircleCI
- **Pipeline stages**:
  1. Validate: lint, typecheck, unit tests
  2. Build: compile, package, containerize
  3. Test: integration, e2e, security scan, performance test
  4. Deploy: apply IaC, run migrations, deploy artifacts
  5. Verify: smoke tests, health checks, canary analysis
- **Deployment strategy**: blue-green / rolling / canary / feature-flag-based
  - Canary percentage: 5% -> 25% -> 50% -> 100%
  - Observation period between each step: X minutes

### 7. Database Migrations

- **Migration files**: numbered and idempotent
- **Backward compatibility**: old code must work with new schema
- **Migration steps**:
  1. Add new columns/tables (nullable, with defaults)
  2. Deploy application code (can now use new schema)
  3. Backfill data for new columns
  4. Add NOT NULL constraints or indexes (requires locking window)
  5. Remove deprecated columns/tables in future release
- **Rollback migrations**: reverse migration scripts prepared and tested

### 8. Monitoring and Alerting

- **Dashboards updated**: latency, error rate, throughput, saturation
- **Alerts configured**:
  - P1: Service down, data loss, security incident (immediate response)
  - P2: Elevated error rate, latency spike (respond within 1 hour)
  - P3: Disk usage, memory trends (respond within 24 hours)
- **Log aggregation**: structured logging, centralized in ELK / Loki / CloudWatch
- **Tracing**: distributed tracing with OpenTelemetry
- **SLOs**: target uptime, latency percentile, error budget

### 9. Rollback Strategy

- **Trigger**: error rate > X%, latency > Yms, failed health checks
- **Rollback procedure**:
  1. Stop traffic to new version
  2. Revert database migrations (if any)
  3. Re-deploy previous version
  4. Verify health of rolled-back version
  5. Notify stakeholders
- **Rollback time target**: < 30 minutes
- **Post-rollback**: incident postmortem scheduled

### 10. Post-Deployment Verification

- [ ] Smoke tests pass on production
- [ ] Health endpoints return 200
- [ ] Key user flows work end-to-end
- [ ] Error rates are within baseline
- [ ] Latency is within SLO
- [ ] Logs show no unexpected errors
- [ ] Stakeholders confirmed success

### 11. Communication Plan

- **Pre-deployment notification**: sent to [channels] at [time]
- **During deployment**: status updates every X minutes in [channel]
- **Post-deployment success**: announcement in [channel]
- **Rollback notification**: immediate alert to [channel]

### 12. Post-Release Tasks

- [ ] Tag release in version control
- [ ] Update changelog
- [ ] Close release milestone in issue tracker
- [ ] Schedule retrospective
- [ ] Review and update runbooks
