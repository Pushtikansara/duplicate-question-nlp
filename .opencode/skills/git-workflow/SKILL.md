---
name: git-workflow
description: Use when establishing Git workflows for teams. Covers GitFlow, GitHub Flow, trunk-based development, code review, and release management.
---

# Git Workflow Skill

## Instructions

Git workflows define how teams use Git for collaboration, code review, and release management. A well-defined workflow improves team productivity, reduces integration problems, and ensures reliable releases. This skill covers the most common Git workflows: GitHub Flow, GitFlow, Trunk-Based Development, and GitLab Flow, along with code review practices and release management.

### Workflow Comparison

| Aspect | GitHub Flow | GitFlow | Trunk-Based | GitLab Flow |
|--------|-------------|---------|-------------|-------------|
| Complexity | Low | High | Low | Medium |
| Main branch | Production | Production + Develop | Production | Production + Pre-Prod |
| Feature branches | Short-lived | Long-lived | Very short (hours) | Short-lived |
| Releases | Continuous | Scheduled | Continuous | Scheduled |
| Hotfixes | Via PR | Dedicated branch | Feature flags | Cherry-pick |
| Best for | Web apps, SaaS | Versioned software | Experienced teams | Enterprise |

### GitHub Flow

GitHub Flow is the simplest workflow, ideal for continuous deployment:

1. Create a branch from `main` for any work
2. Commit changes to the branch
3. Open a pull request early for feedback
4. Discuss and review the code
5. Merge to `main` after approval
6. Deploy immediately after merging

### GitFlow

GitFlow is more structured, suitable for versioned releases:

- `main`: Always reflects production-ready state
- `develop`: Integration branch for features
- `feature/*`: Branches from `develop`, merges back to `develop`
- `release/*`: Branches from `develop`, merges to `main` and `develop`
- `hotfix/*`: Branches from `main`, merges to `main` and `develop`

### Trunk-Based Development

Trunk-Based Development (TBD) emphasizes short-lived branches and continuous integration:

- All developers work on short-lived feature branches (less than a day)
- Branches are merged to `main` (trunk) frequently
- Feature flags control incomplete features
- No long-running branches
- Releases are created from `main` at any time

## Examples

### Example 1: GitHub Flow Implementation

```bash
# Create feature branch
git checkout -b feat/user-authentication

# Work and commit
git add .
git commit -m "feat(auth): add login form component"
git commit -m "feat(auth): implement JWT token handling"
git commit -m "feat(auth): add password reset flow"

# Keep branch updated with main
git fetch origin
git rebase origin/main

# Push branch
git push -u origin feat/user-authentication

# Open pull request on GitHub
# Add description, reviewers, and labels

# After PR approval and merge:
git checkout main
git pull origin main
git branch -d feat/user-authentication
```

### Example 2: GitFlow Implementation

```bash
# Initialize repository with GitFlow
git flow init

# Start a new feature
git flow feature start add-search

# Work on the feature
git commit -m "feat(search): add search bar component"
git commit -m "feat(search): implement search API integration"
git commit -m "feat(search): add search results page"

# Finish the feature (merges to develop)
git flow feature finish add-search

# Start a release
git flow release start v1.2.0

# Finalize release (merge to main and develop, tag)
git flow release finish v1.2.0

# Create a hotfix from main
git flow hotfix start security-patch-1.2.1
git commit -m "fix(security): patch XSS vulnerability"

# Finish hotfix (merges to main and develop)
git flow hotfix finish security-patch-1.2.1
```

### Example 3: Trunk-Based Development

```bash
# Developer workflow:
# 1. Pull latest main
git checkout main
git pull origin main

# 2. Create short-lived branch
git checkout -b f/analytics-dashboard

# 3. Work (small changes, frequent commits)
git add .
git commit -m "Add analytics metrics queries"
git push -u origin f/analytics-dashboard

# 4. Open small PR (under 200 lines)
# 5. Quick review (same day)
# 6. Merge to main

# 7. Deploy from main
# Feature flags control the actual release

# Enable feature via flag
# Flag: analytics_dashboard.enabled=true
```

### Example 4: GitLab Flow with Environments

```yaml
# .gitlab-ci.yml example for environment-based workflow
stages:
  - build
  - test
  - deploy:staging
  - deploy:production

variables:
  NODE_VERSION: '20'

before_script:
  - npm ci

build:
  stage: build
  script: npm run build
  artifacts:
    paths:
      - dist/

test:
  stage: test
  script: npm test

deploy_staging:
  stage: deploy:staging
  script: deploy-to-staging.sh
  only:
    - main

deploy_production:
  stage: deploy:production
  script: deploy-to-production.sh
  only:
    - tags
  when: manual
```

### Example 5: Automated Release Management

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Determine version
        id: version
        run: |
          # Extract version from conventional commits
          # Using semantic-release or commitlint
          echo "version=$(node -e "
            const commits = '${{ toJson(github.event.commits) }}'
            // version calculation logic
          ")" >> $GITHUB_OUTPUT

      - name: Create tag
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git tag -a "v${{ steps.version.outputs.version }}" -m "Release v${{ steps.version.outputs.version }}"
          git push origin "v${{ steps.version.outputs.version }}"

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          tag_name: v${{ steps.version.outputs.version }}
          generate_release_notes: true
```

### Example 6: Conventional Commits Enforcement

```yaml
# commitlint.config.js
module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [2, 'always', [
      'feat',     # New feature
      'fix',      # Bug fix
      'docs',     # Documentation
      'style',    # Formatting
      'refactor', # Code refactoring
      'perf',     # Performance
      'test',     # Testing
      'chore',    # Maintenance
      'ci',       # CI/CD
      'revert'    # Revert
    ]],
    'scope-case': [2, 'always', 'kebab-case'],
    'subject-case': [2, 'never', ['sentence-case', 'start-case']],
    'subject-max-length': [2, 'always', 72],
    'body-max-line-length': [2, 'always', 100],
  },
}

# .github/workflows/commitlint.yml
name: PR Commit Lint
on:
  pull_request:
    types: [opened, edited, synchronize]

jobs:
  commitlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npx commitlint --from ${{ github.event.pull_request.base.sha }} --to ${{ github.event.pull_request.head.sha }}
```

### Example 7: Branch Protection Configuration

```yaml
# .github/settings.yml (with GitHub settings app)
branch_protection_rules:
  - pattern: main
    allows_force_pushes: false
    allows_deletions: false
    enforce_admins: true
    required_status_checks:
      strict: true
      contexts:
        - "Continuous Integration"
        - "Lint"
        - "Test (18.x)"
        - "Test (20.x)"
    required_pull_request_reviews:
      dismiss_stale_reviews: true
      require_code_owner_reviews: true
      required_approving_review_count: 1
    required_linear_history: true
    lock_branch: false

  - pattern: develop
    allows_force_pushes: false
    allows_deletions: false
    required_pull_request_reviews:
      required_approving_review_count: 1
    required_status_checks:
      contexts:
        - "Continuous Integration"
```

## Best Practices

### Branch Management

- Keep branches short-lived (ideally less than one day for trunk-based, a few days for GitHub Flow)
- Delete branches after merging to keep the repository clean
- Use consistent branch naming conventions across the team
- Protect main branches with branch rules (require PRs, status checks)
- Use `git fetch --prune` regularly to clean up stale remote references

### Code Review Practices

- Open pull requests early (even as drafts) for early feedback
- Keep pull requests small and focused (under 400 lines of changes)
- Review your own code first before requesting reviews
- Respond to review comments promptly
- Use status checks to automate quality gates
- Require at least one approval before merging

### Release Management

- Use semantic versioning (MAJOR.MINOR.PATCH)
- Tag releases with version numbers
- Maintain a changelog (generated from conventional commits)
- Deploy to staging environments before production
- Have rollback procedures documented and tested
- Use feature flags for gradual feature rollout

### Team Coordination

- Document the chosen workflow in a CONTRIBUTING.md file
- Onboard new team members on the workflow
- Automate as much as possible (CI, commit linting, auto-merge)
- Hold regular sync meetings to discuss integration issues
- Establish clear ownership for branches and releases

## Common Mistakes

- **Long-running feature branches**: Branches that live for weeks or months accumulate massive merge conflicts and increase integration risk. Merge to main frequently.
- **Not protecting main branch**: Without branch protection, anyone can push directly to main, bypassing review. Always protect main with status checks and review requirements.
- **Inconsistent naming conventions**: Random branch names like `fix`, `asdf`, or `my-changes` make it hard to understand the purpose. Use consistent prefixes.
- **Squashing during review**: Squashing commits during PR review makes it hard to see incremental changes. Squash only when merging to main.
- **Forgetting to sync with upstream**: Not pulling/rebasing regularly causes conflicts. Sync with main multiple times per day.
- **Merging without CI passing**: Disable the merge button until all required checks pass. Never merge with failing tests.
- **Not using draft PRs**: Opening complete PRs for work in progress creates noise for reviewers. Use draft PRs for early feedback.
- **Over-engineering the workflow**: Small teams do not need GitFlow. Choose the simplest workflow that meets your needs.
- **No release process**: Without tagged releases and a changelog, it is impossible to know what version is deployed or what changed.
- **Ignoring hotfix procedures**: Emergency fixes applied directly to production without going through the workflow cause technical debt and missed tests.

## Libraries

### Workflow Automation Tools

| Tool | Purpose |
|------|---------|
| commitlint | Enforce conventional commit format |
| semantic-release | Automated versioning and release |
| standard-version | Version bump and changelog generation |
| husky | Git hook management |
| lint-staged | Run linters on staged files |
| git-cz | Commitizen commit message helper |
| release-it | Automated release tooling |
| changesets | Changeset-based version management |
| gitflow-avh | Extended GitFlow implementation |

### CI/CD Platform Features

| Platform | Workflow Features |
|----------|-------------------|
| GitHub Actions | PR workflows, environment protection, auto-merge |
| GitLab CI/CD | Merge trains, environment management, MR approvals |
| Bitbucket Pipelines | Branch permissions, merge checks, deployments |
| Azure Pipelines | Multi-stage YAML, environment approvals |
| CircleCI | Workflow orchestration, context management |

## Design Principles

### Fit the Team, Not the Fashion

Choose a workflow that matches your team's size, release cadence, and risk tolerance. GitHub Flow is excellent for SaaS products with continuous deployment. GitFlow suits versioned software with scheduled releases. Trunk-based development works best for teams practicing continuous integration.

### Automation Over Process

Any process step that can be automated should be automated. Commit linting, CI checks, automatic deployments, and merge requirements reduce human error and free up mental energy for decision-making.

### Short Cycles, Small Batches

The most important factor in smooth collaboration is batch size. Small changes merged frequently reduce integration conflicts, speed up feedback loops, and make deployments safer. A feature should never take more than a few days to merge.

### Reversible Decisions

Design the workflow so that any change can be rolled back. Revert commits, feature flags, and backward-compatible releases ensure that mistakes can be corrected quickly without disrupting the team.

## Coding Standards

### Branch Naming

```
<prefix>/<scope>-<description>
Prefixes: feat, fix, hotfix, chore, docs, refactor, test, release
Examples:
  feat/auth-add-login
  fix/api-null-pointer
  hotfix/security-patch-xss
  chore/update-dependencies
  release/v2.1.0
```

### Commit Message Template

```
# .gitmessage template
# Commit format: <type>(<scope>): <subject>

# Types: feat, fix, docs, style, refactor, perf, test, chore, ci
# Subject: imperative mood, no period, max 50 chars
# Body: explain what and why, not how, max 72 chars per line
# Footer: breaking changes, issue references

# Example:
feat(auth): add OAuth2 login with Google provider

Implement Google OAuth2 integration for single sign-on.
Store refresh tokens in HTTP-only cookies for security.

Closes #123
BREAKING CHANGE: Removed legacy password-based login.
```

### Workflow Configuration Files

```
.github/
  workflows/
    ci.yml
    cd.yml
    release.yml
    lint-pr.yml
CONTRIBUTING.md     # Workflow documentation
commitlint.config.js
.releaserc.js      # semantic-release config
```
