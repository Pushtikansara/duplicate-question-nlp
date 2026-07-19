---
name: github-actions
description: Use when creating CI/CD pipelines with GitHub Actions. Covers workflows, jobs, steps, actions, secrets, and matrix builds.
---

# GitHub Actions Skill

## Instructions

GitHub Actions is a continuous integration and continuous delivery (CI/CD) platform that automates build, test, and deployment workflows directly from GitHub repositories. This skill covers workflow design, job orchestration, custom actions, secrets management, and advanced patterns like matrix builds and environment deployments.

### Core Concepts

**Workflows**: YAML files in `.github/workflows/` that define automated processes. Each workflow is triggered by events (push, pull_request, schedule, etc.).

**Jobs**: Units of work within a workflow that run on a runner. Jobs can run in parallel or sequentially with dependencies.

**Steps**: Individual tasks within a job that execute commands or actions.

**Actions**: Reusable units of code (JavaScript, Docker container, or composite) for common tasks.

**Runners**: Virtual machines or self-hosted machines that execute workflow jobs.

### Workflow Structure

```yaml
name: CI Pipeline
run-name: CI ${{ github.sha }}

on:
  push:
    branches: [main, develop]
    paths-ignore:
      - '**.md'
      - 'docs/**'
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

env:
  NODE_VERSION: '20'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
      - run: npm ci
      - run: npm run lint

  test:
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [18, 20, 22]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test

  deploy:
    needs: [lint, test]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build
      - uses: some/deploy-action@v1
        with:
          api-token: ${{ secrets.DEPLOY_TOKEN }}
```

## Examples

### Example 1: Complete CI Pipeline for Node.js

```yaml
name: Node.js CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  NODE_VERSION: '20'
  PNPM_VERSION: '8'

jobs:
  validate:
    name: Validate Code
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Required for SonarQube or lint-staged

      - uses: pnpm/action-setup@v2
        with:
          version: ${{ env.PNPM_VERSION }}

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile

      - name: Lint
        run: pnpm lint

      - name: Type Check
        run: pnpm typecheck

      - name: Check Formatting
        run: pnpm format:check

  test:
    name: Run Tests
    needs: validate
    runs-on: ubuntu-latest
    timeout-minutes: 15
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    strategy:
      matrix:
        node-version: [18, 20, 22]
        include:
          - node-version: 20
            coverage: true

    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: ${{ env.PNPM_VERSION }}
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile

      - name: Run Tests
        run: pnpm test:ci
        env:
          DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379

      - name: Upload Coverage
        if: matrix.coverage
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info
          fail_ci_if_error: true

      - name: Test Summary
        run: |
          echo "## Test Results for Node ${{ matrix.node-version }}" >> $GITHUB_STEP_SUMMARY
          echo "Tests completed successfully" >> $GITHUB_STEP_SUMMARY

  build:
    name: Build Artifacts
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
        with:
          version: ${{ env.PNPM_VERSION }}
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'pnpm'

      - run: pnpm install --frozen-lockfile

      - name: Build
        run: pnpm build

      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/
          retention-days: 7
```

### Example 2: Docker Build and Push

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]
    tags:
      - 'v*'

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    name: Build and Push Docker Image
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      attestations: write
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,format=short
            type=ref,event=branch
            type=raw,value=latest,enable={{is_default_branch}}

      - name: Build and push Docker image
        id: push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            BUILD_VERSION=${{ github.sha }}
            BUILD_DATE=${{ github.event.repository.updated_at }}

      - name: Generate artifact attestation
        uses: actions/attest-build-provenance@v1
        with:
          subject-name: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          subject-digest: ${{ steps.push.outputs.digest }}
          push-to-registry: true
```

### Example 3: Multi-Environment Deployment

```yaml
name: Deploy to Environments

on:
  push:
    branches: [main, staging, develop]

jobs:
  deploy:
    name: Deploy to ${{ github.ref_name }}
    runs-on: ubuntu-latest
    environment:
      name: ${{ github.ref_name }}
      url: ${{ steps.deploy.outputs.url }}

    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ vars.AWS_REGION }}

      - name: Deploy to ECS
        id: deploy
        run: |
          aws ecs update-service \
            --cluster ${{ vars.ECS_CLUSTER }} \
            --service ${{ vars.ECS_SERVICE }} \
            --force-new-deployment

      - name: Run Smoke Tests
        run: |
          curl -f -s -o /dev/null \
            --retry 10 \
            --retry-delay 5 \
            ${{ steps.deploy.outputs.url }}/health

      - name: Notify Slack
        if: always()
        uses: slackapi/slack-github-action@v1.24.0
        with:
          payload: |
            {
              "text": "${{ job.status == 'success' && '✅' || '❌' }} Deployment to ${{ github.ref_name }} ${{ job.status }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Deployment ${{ job.status }}*"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

### Example 4: Reusable Workflow

```yaml
# .github/workflows/reusable-ci.yml
name: Reusable CI Workflow

on:
  workflow_call:
    inputs:
      node-version:
        required: false
        type: string
        default: '20'
      run-lint:
        required: false
        type: boolean
        default: true
    secrets:
      CODECOV_TOKEN:
        required: false

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'

      - run: npm ci

      - if: inputs.run-lint
        run: npm run lint

      - run: npm test

      - if: secrets.CODECOV_TOKEN
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

---
# .github/workflows/ci.yml (caller)
name: CI
on: [push]

jobs:
  ci-call:
    uses: ./.github/workflows/reusable-ci.yml
    with:
      node-version: '20'
      run-lint: true
    secrets:
      CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

### Example 5: Matrix Build with Strategy

```yaml
name: Matrix Build

on: [push]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node-version: [18, 20, 22]
        exclude:
          - os: windows-latest
            node-version: 22
        include:
          - os: ubuntu-latest
            node-version: 20
            coverage: true
      fail-fast: false  # Continue other matrix jobs on failure

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
      - if: matrix.coverage
        run: npm run coverage
```

### Example 6: Scheduled Workflow with Reporting

```yaml
name: Daily Security Scan

on:
  schedule:
    - cron: '0 6 * * 1-5'  # Weekdays at 6 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  security-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: npm audit
        continue-on-error: true
        run: |
          npm audit --audit-level=high > audit-report.txt
          cat audit-report.txt

      - name: Dependency Review
        uses: actions/dependency-review-action@v3
        with:
          fail-on-severity: high

      - name: SARIF upload
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: results.sarif

      - name: Create Issue on Failure
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Security audit failed',
              body: 'The daily security audit found vulnerabilities. Check the workflow run for details.'
            })
```

### Example 7: Custom Composite Action

```yaml
# .github/actions/hello/action.yml
name: 'Hello World'
description: 'Greet someone'
inputs:
  who-to-greet:
    description: 'Who to greet'
    required: true
    default: 'World'
outputs:
  time:
    description: 'The time we greeted you'
    value: ${{ steps.time.outputs.time }}

runs:
  using: 'composite'
  steps:
    - name: Set Greeting
      run: echo "Hello ${{ inputs.who-to-greet }}!"
      shell: bash

    - name: Set Time
      id: time
      run: echo "time=$(date)" >> $GITHUB_OUTPUT
      shell: bash
```

## Best Practices

### Workflow Design

- Keep workflows focused on a single purpose (CI, CD, security, etc.)
- Use `concurrency` to cancel redundant runs on the same branch
- Set appropriate `timeout-minutes` to prevent runaway jobs
- Use `paths` and `paths-ignore` to avoid unnecessary runs
- Use `workflow_dispatch` for manual trigger capability
- Leverage reusable workflows for shared CI/CD patterns
- Use GitHub Environments for deployment approvals and variables
- Validate workflow syntax with `act` or `nektos/act` locally

### Security Practices

- Use `${{ secrets.* }}` for all sensitive values; never hardcode credentials
- Use `GITHUB_TOKEN` with minimal permissions
- Pin action versions to full commit SHAs for supply chain security
- Use `actions/attest-build-provenance` for artifact verification
- Avoid using `pull_request_target` without careful review
- Sanitize user-controlled data in workflow expressions
- Use OpenID Connect (OIDC) for cloud provider authentication
- Review third-party actions before use

### Performance Practices

- Cache dependencies with `actions/cache` or language-specific cache actions
- Use matrix strategy to parallelize test runs across configurations
- Limit artifact upload/download to only what is necessary
- Use self-hosted runners for faster execution when needed
- Minimize the number of jobs and steps where possible
- Use `actions/checkout` with `fetch-depth: 1` for shallow clones

### Monitoring and Maintenance

- Set up notifications for workflow failures (Slack, email, etc.)
- Review and clean up unused workflows
- Archive old workflow runs to reduce storage costs
- Monitor runner usage and queue times
- Keep workflows and actions up to date with Dependabot
- Document workflow purpose and expected behavior

## Common Mistakes

- **Hardcoding secrets in workflow files**: Never put secrets directly in YAML. Always use GitHub Secrets or Environments.
- **Not pinning action versions**: Using `@main` or `@v1` (mutable tags) can introduce breaking changes unexpectedly. Pin to SHA or strict semver.
- **Oversized matrix builds**: Testing every combination of OS, language version, and dependency can be wasteful. Use `exclude` and `include` judiciously.
- **Long-running workflows without timeouts**: Default timeouts can be very long. Always set appropriate `timeout-minutes`.
- **Not caching dependencies**: Without caching, every run installs from scratch. Use caching to reduce run time significantly.
- **Running untrusted third-party actions**: Third-party actions can access secrets. Review action source code before using.
- **Using `pull_request_target` incorrectly**: This event runs in the context of the base branch and can leak secrets to PR code.
- **Ignoring workflow failures**: Failed workflows should alert the team. Set up notification integrations.
- **Not separating CI and CD**: Mixing build, test, and deploy in one job makes debugging difficult. Use separate jobs with `needs`.
- **Committing broken workflow files**: Invalid YAML syntax causes the entire workflow to fail. Validate locally before pushing.

## Libraries

### Official GitHub Actions

| Action | Purpose |
|--------|---------|
| actions/checkout | Check out repository code |
| actions/setup-node | Set up Node.js environment |
| actions/setup-python | Set up Python environment |
| actions/setup-java | Set up Java environment |
| actions/cache | Cache dependencies and build outputs |
| actions/upload-artifact | Upload workflow artifacts |
| actions/download-artifact | Download workflow artifacts |
| actions/dependency-review-action | Dependency vulnerability scanning |
| actions/github-script | Execute JavaScript in workflows |
| actions/starter-workflows | Template workflows |

### Third-Party Actions

| Action | Purpose |
|--------|---------|
| docker/login-action | Log in to container registries |
| docker/build-push-action | Build and push Docker images |
| docker/metadata-action | Extract Docker metadata |
| aws-actions/configure-aws-credentials | Configure AWS credentials |
| azure/login | Authenticate to Azure |
| google-github-actions/auth | Authenticate to GCP |
| slackapi/slack-github-action | Send Slack notifications |
| codecov/codecov-action | Upload coverage reports |
| sonarsource/sonarcloud-github-action | SonarCloud analysis |

## Design Principles

### Separation of Concerns

Each workflow should have a single responsibility: CI, CD, security scanning, or maintenance. Workflow logic should be split into distinct jobs with clear dependencies. Composite actions encapsulate reusable logic.

### Idempotent Pipelines

Workflows should produce the same results when re-run with the same inputs. Avoid operations that depend on external mutable state. Use deterministic build processes with lockfiles and pinned dependencies.

### Security by Default

Assume that code running in a workflow may be compromised. Use fine-grained tokens, minimize permissions, isolate jobs, and never run untrusted code with access to production secrets.

### Observability

Workflows should produce clear, actionable output. Use step summaries, annotations, and workflow run names to communicate results. Failed workflows should include enough context for debugging without requiring a re-run.

## Coding Standards

### Workflow File Organization

```
.github/
  workflows/
    ci.yml            # Continuous integration
    cd.yml            # Continuous deployment
    security.yml      # Security scanning
    release.yml       # Release management
    dependabot.yml    # Dependabot configuration
  actions/
    deploy/           # Custom composite actions
      action.yml
    notify/
      action.yml
```

### Naming Conventions

- Workflow files: `kebab-case` (e.g., `ci-pipeline.yml`, `deploy-production.yml`)
- Job names: Verb phrases (e.g., `Run Tests`, `Build Docker Image`, `Deploy to Production`)
- Step names: Descriptive phrases (e.g., `Check out repository`, `Install dependencies`)
- Custom actions: Descriptive names (e.g., `deploy-to-ecs`, `notify-slack`)
- Environment names: Match Git branch names (e.g., `develop`, `staging`, `main`)

### Workflow Formatting

```yaml
name: Descriptive Workflow Name
run-name: "${{ github.actor }} triggered ${{ github.workflow }}"

on:
  push:
    branches: [main]

env:
  # Global environment variables
  NODE_VERSION: '20'

jobs:
  job-name:
    name: Human Readable Job Name
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    timeout-minutes: 30
    steps:
      # Step definition
      - name: Step Name
        id: step-id
        uses: some/action@v1
        with:
          param: value
```
