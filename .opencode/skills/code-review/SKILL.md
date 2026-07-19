---
name: code-review
description: Use when performing code reviews. Covers review process, what to look for, constructive feedback, and CI integration.
---

# Code Review Skill

## Instructions

Code review is a systematic examination of source code intended to find bugs, improve code quality, and share knowledge among team members. It is one of the most effective practices for preventing defects and improving software quality. This skill covers the code review process, what to look for during reviews, how to provide constructive feedback, and how to integrate reviews into CI/CD pipelines.

### The Purpose of Code Review

Code review serves multiple purposes:

- **Defect Detection**: Catch bugs, security vulnerabilities, and logic errors before they reach production
- **Knowledge Sharing**: Spread understanding of the codebase across team members
- **Consistency**: Enforce coding standards and architectural patterns
- **Mentoring**: Help junior developers improve through constructive feedback
- **Collective Ownership**: Multiple team members understand and can maintain the code
- **Quality Gate**: Ensure code meets team standards before merging

### The Code Review Process

1. **Author prepares the change**: Write code, add tests, self-review
2. **Author creates a pull request**: Write a clear description, add context
3. **Reviewers are assigned**: Based on expertise and availability
4. **Reviewers examine the code**: Look for issues, ask questions
5. **Reviewers provide feedback**: Comments, suggestions, approvals
6. **Author responds and updates**: Address feedback, push changes
7. **Approval and merge**: At least one approval, passing CI, merge
8. **Cleanup**: Delete branch, verify deployment

### Types of Code Review

| Type | Formality | Timing | Duration |
|------|-----------|--------|----------|
| Pair Programming | High | Real-time | Continuous |
| Over-the-shoulder | Low | Real-time | Minutes |
| Pull Request Review | Medium | Asynchronous | Hours |
| Formal Inspection | Very High | Scheduled | Hours |

## Examples

### Example 1: Code Review Checklist

```markdown
# Code Review Checklist

## Functionality
- [ ] Does the code do what it's supposed to do?
- [ ] Are all edge cases handled (empty, null, boundary values)?
- [ ] Are error conditions handled properly?
- [ ] Does the code handle concurrent access or race conditions?
- [ ] Are there any obvious logic errors?

## Security
- [ ] Is user input validated and sanitized?
- [ ] Are SQL queries parameterized (no string concatenation)?
- [ ] Are authentication and authorization checks in place?
- [ ] Is sensitive data properly protected (encryption, masking)?
- [ ] Are there any hardcoded secrets, tokens, or credentials?
- [ ] Is output properly encoded to prevent XSS?

## Performance
- [ ] Are there N+1 query problems?
- [ ] Are database queries indexed appropriately?
- [ ] Is caching used where appropriate?
- [ ] Are there any obvious memory leaks (unclosed connections, listeners)?
- [ ] Are large datasets processed efficiently (streaming, pagination)?
- [ ] Are there unnecessary database calls inside loops?

## Maintainability
- [ ] Is the code easy to understand?
- [ ] Are variable names, function names, and class names descriptive?
- [ ] Is the code following the project's coding style?
- [ ] Are there comments explaining "why" (not "what")?
- [ ] Is there duplicated code that should be extracted?
- [ ] Are functions and methods focused on a single responsibility?
- [ ] Is the code testable (dependency injection, separation of concerns)?

## Testing
- [ ] Are unit tests included for new code?
- [ ] Do tests cover edge cases, not just the happy path?
- [ ] Are integration tests included where appropriate?
- [ ] Do tests follow the AAA pattern (Arrange, Act, Assert)?
- [ ] Are test names descriptive?
- [ ] Is there adequate test coverage for the change?

## Architecture
- [ ] Does the code follow the project's architectural patterns?
- [ ] Are the right abstractions used?
- [ ] Does the change introduce unnecessary coupling?
- [ ] Are dependencies correctly inverted?
- [ ] Does the code fit cleanly into existing module structure?
- [ ] Have architectural decisions been documented (ADRs)?

## Documentation
- [ ] Are public APIs documented (JSDoc, docstrings, etc.)?
- [ ] Are configuration changes documented?
- [ ] Are breaking changes called out in the PR description?
- [ ] Is the README or relevant docs updated if needed?
- [ ] Is a changelog entry needed?

## DevOps
- [ ] Are there any infrastructure changes required?
- [ ] Are migration scripts included for database changes?
- [ ] Are environment variables documented?
- [ ] Does the change affect deployment or rollback procedures?
- [ ] Are monitoring and alerting changes included?
```

### Example 2: Pull Request Template

```markdown
---
name: Pull Request
about: Describe the change you're making
---

## Description

<!-- Provide a brief description of the change and why it's needed -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that changes existing behavior)
- [ ] Documentation update
- [ ] Refactoring (no functional change)
- [ ] Performance improvement
- [ ] Dependency update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] No new warnings or errors

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated (if needed)
- [ ] No hardcoded secrets or credentials
- [ ] Database migrations are backward-compatible
- [ ] Changes are backward-compatible or breaking changes are noted

## Screenshots (if UI changes)

<!-- Add screenshots before/after for UI changes -->

## Additional Context

<!-- Add any additional context, links to related issues, design docs, etc. -->

Closes #ISSUE_NUMBER
```

### Example 3: Review Response Guidelines

```python
"""
Guidelines for providing and responding to code review feedback.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class FeedbackType(Enum):
    MUST_FIX = "must_fix"       # Bug, security issue, incorrect behavior
    SHOULD_FIX = "should_fix"   # Best practice, performance, readability
    NITPICK = "nitpick"         # Style preference, minor improvement
    QUESTION = "question"       # Seek clarification
    PRAISE = "praise"           # Positive feedback


@dataclass
class ReviewComment:
    feedback_type: FeedbackType
    file_path: str
    line_number: Optional[int]
    subject: str
    body: str
    suggestion: Optional[str] = None


class ReviewResponse:
    """Model for a well-structured code review comment."""

    @staticmethod
    def bug_risk(file_path: str, line: int, issue: str,
                 impact: str, suggestion: str) -> ReviewComment:
        """Flag a potential bug or security issue."""
        return ReviewComment(
            feedback_type=FeedbackType.MUST_FIX,
            file_path=file_path,
            line_number=line,
            subject=f"Potential bug: {issue}",
            body=f"This could cause {impact}. Please review and address.",
            suggestion=suggestion,
        )

    @staticmethod
    def performance_concern(file_path: str, line: int,
                            issue: str, impact: str,
                            suggestion: str) -> ReviewComment:
        """Flag a performance concern."""
        return ReviewComment(
            feedback_type=FeedbackType.SHOULD_FIX,
            file_path=file_path,
            line_number=line,
            subject=f"Performance: {issue}",
            body=f"This could impact performance: {impact}. "
                 f"Consider alternative approach.",
            suggestion=suggestion,
        )

    @staticmethod
    def style_nitpick(file_path: str, line: int,
                      issue: str,
                      suggestion: str) -> ReviewComment:
        """Minor style or preference comment."""
        return ReviewComment(
            feedback_type=FeedbackType.NITPICK,
            file_path=file_path,
            line_number=line,
            subject=f"Style: {issue}",
            body=f"Minor suggestion to improve readability.",
            suggestion=suggestion,
        )

    @staticmethod
    def clarification_question(file_path: str, line: int,
                               question: str) -> ReviewComment:
        """Ask for clarification about the code."""
        return ReviewComment(
            feedback_type=FeedbackType.QUESTION,
            file_path=file_path,
            line_number=line,
            subject=f"Question: {question}",
            body="Could you help me understand this part of the code?",
        )

    @staticmethod
    def praise(file_path: str, aspect: str) -> ReviewComment:
        """Give positive feedback."""
        return ReviewComment(
            feedback_type=FeedbackType.PRAISE,
            file_path=file_path,
            line_number=None,
            subject=f"Great work: {aspect}",
            body=f"Nice work on {aspect}. This is well done!",
        )


class ReviewResponseGenerator:
    """Generate appropriate responses to review comments."""

    @staticmethod
    def accept_comment(comment_id: str) -> str:
        """Accept a review suggestion."""
        return f"Good catch! Fixed in {comment_id}."

    @staticmethod
    def partially_accept(comment_id: str, alternative: str) -> str:
        """Partially accept a suggestion with an alternative approach."""
        return f"Good point. I took a slightly different approach: {alternative}."

    @staticmethod
    def explain_rationale(comment_id: str, reason: str) -> str:
        """Explain why you chose a particular approach."""
        return f"I considered that, but chose this approach because {reason}."

    @staticmethod
    def defer_to_followup(comment_id: str, issue_link: str) -> str:
        """Acknowledge feedback and defer to a follow-up issue."""
        return (f"Valid point. I've created an issue to address this "
                f"separately: {issue_link}.")

    @staticmethod
    def thank_reviewer(comment_id: str) -> str:
        """Thank the reviewer for their feedback."""
        return f"Thanks for the thorough review! Applied your suggestion."


# Example usage
review_examples = [
    # Bug/security feedback
    ReviewResponse.bug_risk(
        file_path="src/auth/login.ts",
        line=45,
        issue="SQL injection risk in user lookup query",
        impact="An attacker could execute arbitrary SQL commands",
        suggestion="Use parameterized query: "
                   "`SELECT * FROM users WHERE email = $1`",
    ),

    # Performance feedback
    ReviewResponse.performance_concern(
        file_path="src/services/reports.ts",
        line=120,
        issue="N+1 query pattern in report generation",
        impact="Each report row triggers a separate database query",
        suggestion="Use a JOIN to fetch related data in a single query",
    ),

    # Style feedback (nitpick)
    ReviewResponse.style_nitpick(
        file_path="src/components/button.tsx",
        line=15,
        issue="Inconsistent naming convention",
        suggestion="Rename `handleClick` to `onClick` to match project conventions",
    ),

    # Clarification question
    ReviewResponse.clarification_question(
        file_path="src/utils/parser.ts",
        line=88,
        question="Why is the fallback value set to null here?",
    ),

    # Positive feedback
    ReviewResponse.praise(
        file_path="src/services/payment.ts",
        aspect="the comprehensive error handling and retry logic",
    ),
]
```

### Example 4: Automated Review Integration

```yaml
# .github/workflows/code-review.yml
name: Automated Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci

      - name: ESLint
        run: npm run lint
        continue-on-error: true

      - name: Prettier Check
        run: npm run format:check
        continue-on-error: true

  static-analysis:
    name: Static Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: SonarCloud Analysis
        uses: sonarsource/sonarcloud-github-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

      - name: CodeQL Analysis
        uses: github/codeql-action/analyze@v2

  security:
    name: Security Review
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Dependency Audit
        run: npm audit --audit-level=high

      - name: Secrets Check
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  test:
    name: Test Suite
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci

      - name: Unit Tests
        run: npm run test:ci

      - name: Coverage Report
        uses: davelosert/vitest-coverage-report-action@v2
        if: always()

  size:
    name: PR Size Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check PR Size
        uses: actions/github-script@v6
        with:
          script: |
            const { data: pr } = await github.rest.pulls.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              pull_number: context.issue.number,
            });

            const changes = pr.additions + pr.deletions;
            const MAX_CHANGES = 400;

            if (changes > MAX_CHANGES) {
              core.warning(`PR has ${changes} lines changed (max: ${MAX_CHANGES}). Consider splitting into smaller PRs.`);
            }
```

### Example 5: Common Code Issues and How to Flag Them

```python
"""
Common code review findings with how to communicate them effectively.
"""

class ReviewFindingLibrary:
    """Collection of common code review findings with suggested comments."""

    @staticmethod
    def magic_numbers():
        """Flag magic numbers."""
        return {
            'finding': 'Hardcoded magic number',
            'example_comment': (
                "Consider extracting this value as a named constant "
                "to make the code more self-documenting."
            ),
            'example_code': '# Bad\n'
                            'if retry_count > 3:\n'
                            '    raise TimeoutError()\n\n'
                            '# Better\n'
                            'MAX_RETRIES = 3\n'
                            'if retry_count > MAX_RETRIES:\n'
                            '    raise TimeoutError()',
        }

    @staticmethod
    def deep_nesting():
        """Flag deeply nested code."""
        return {
            'finding': 'Excessive nesting depth',
            'example_comment': (
                "This code has too many levels of nesting. "
                "Consider extracting inner blocks into separate methods "
                "or using early returns to flatten the structure."
            ),
            'example_code': '# Bad\n'
                            'def process(order):\n'
                            '    if order.is_active:\n'
                            '        if order.items:\n'
                            '            for item in order.items:\n'
                            '                if item.in_stock:\n'
                            '                    # ...\n\n'
                            '# Better\n'
                            'def process(order):\n'
                            '    if not order.is_active:\n'
                            '        return\n'
                            '    if not order.items:\n'
                            '        return\n'
                            '    for item in order.items:\n'
                            '        process_item(item)',
        }

    @staticmethod
    def large_functions():
        """Flag overly large functions."""
        return {
            'finding': 'Function too large',
            'example_comment': (
                "This function is doing too many things. "
                "Consider extracting distinct operations into "
                "separate, well-named functions. "
                "Aim for functions under 20-30 lines."
            ),
        }

    @staticmethod
    def mutable_default_args():
        """Flag mutable default arguments."""
        return {
            'finding': 'Mutable default argument',
            'example_comment': (
                "Using mutable objects as default arguments can lead "
                "to unexpected behavior because defaults are evaluated "
                "once at function definition time. "
                "Use None and create a new instance inside the function."
            ),
            'example_code': '# Bad\n'
                            'def process(items=[]):\n'
                            '    items.append("new")\n'
                            '    return items\n\n'
                            '# Better\n'
                            'def process(items=None):\n'
                            '    if items is None:\n'
                            '        items = []\n'
                            '    items.append("new")\n'
                            '    return items',
        }

    @staticmethod
    def untested_code():
        """Flag missing tests."""
        return {
            'finding': 'Missing test coverage',
            'example_comment': (
                "This new code doesn't have corresponding tests. "
                "Please add unit tests covering:\n"
                "- Success path\n"
                "- Error conditions\n"
                "- Edge cases (empty, null, boundary values)"
            ),
        }

    @staticmethod
    def error_swallowing():
        """Flag empty except blocks."""
        return {
            'finding': 'Bare except clause',
            'example_comment': (
                "Bare except clauses catch ALL exceptions including "
                "SystemExit and KeyboardInterrupt. "
                "Catch specific exceptions or at least use `except Exception`."
            ),
            'example_code': '# Bad\n'
                            'try:\n'
                            '    process_data()\n'
                            'except:\n'
                            '    pass\n\n'
                            '# Better\n'
                            'try:\n'
                            '    process_data()\n'
                            'except ValueError as e:\n'
                            '    logger.error("Invalid data: %s", e)',
        }

    @staticmethod
    def unnecessary_else():
        """Flag unnecessary else after return."""
        return {
            'finding': 'Unnecessary else clause',
            'example_comment': (
                "Since the if block returns, the else is unnecessary. "
                "Removing it flattens the code."
            ),
            'example_code': '# Bad\n'
                            'if condition:\n'
                            '    return value\n'
                            'else:\n'
                            '    return other_value\n\n'
                            '# Better\n'
                            'if condition:\n'
                            '    return value\n'
                            'return other_value',
        }
```

### Example 6: Code Review Automation Script

```python
#!/usr/bin/env python3
"""
Automated code review assistant that checks common issues.
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any


class AutomatedReview:
    """Run automated checks on code changes."""

    def __init__(self, target_branch: str = "main"):
        self.target_branch = target_branch
        self.issues: List[Dict[str, Any]] = []

    def get_changed_files(self) -> List[str]:
        """Get list of files changed compared to target branch."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only',
                 f'origin/{self.target_branch}...HEAD'],
                capture_output=True, text=True, check=True,
            )
            return [f for f in result.stdout.splitlines()
                    if f.endswith('.py')]
        except subprocess.CalledProcessError:
            print("Could not determine changed files")
            return []

    def check_import_length(self, file_path: str):
        """Flag files with too many imports."""
        with open(file_path) as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            imports = [node for node in ast.walk(tree)
                       if isinstance(node, (ast.Import, ast.ImportFrom))]

            if len(imports) > 20:
                self.issues.append({
                    'file': file_path,
                    'line': 1,
                    'severity': 'warning',
                    'message': f"File has {len(imports)} import statements. "
                               f"Consider if this module has too many dependencies.",
                })
        except SyntaxError:
            pass

    def check_function_length(self, file_path: str):
        """Flag functions that are too long."""
        with open(file_path) as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    # Count lines
                    start_line = node.lineno
                    end_line = max(
                        child.lineno for child in ast.walk(node)
                        if hasattr(child, 'lineno')
                    ) if hasattr(node, 'body') and node.body else start_line
                    line_count = end_line - start_line

                    if line_count > 50:
                        self.issues.append({
                            'file': file_path,
                            'line': start_line,
                            'severity': 'warning',
                            'message': (
                                f"Function '{node.name}' is {line_count} lines. "
                                f"Consider breaking it into smaller functions."
                            ),
                        })
        except SyntaxError:
            pass

    def check_todo_comments(self, file_path: str):
        """Flag TODO and FIXME comments."""
        with open(file_path) as f:
            for i, line in enumerate(f, 1):
                if 'TODO' in line or 'FIXME' in line:
                    self.issues.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'info',
                        'message': f"Contains TODO/FIXME: {line.strip()[:80]}",
                    })

    def check_print_statements(self, file_path: str):
        """Flag print statements in production code."""
        if 'test_' not in file_path:
            with open(file_path) as f:
                for i, line in enumerate(f, 1):
                    if 'print(' in line and 'logger' not in line:
                        self.issues.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'warning',
                            'message': (
                                "Print statement found in production code. "
                                "Use proper logging instead."
                            ),
                        })

    def check_empty_except(self, file_path: str):
        """Flag empty except blocks."""
        with open(file_path) as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    if not node.body or (
                        len(node.body) == 1 and
                        isinstance(node.body[0], ast.Pass)
                    ):
                        self.issues.append({
                            'file': file_path,
                            'line': node.lineno,
                            'severity': 'error',
                            'message': (
                                "Empty except block. Either handle the "
                                "exception or log it."
                            ),
                        })
        except SyntaxError:
            pass

    def check_mutable_defaults(self, file_path: str):
        """Flag mutable default arguments."""
        with open(file_path) as f:
            content = f.read()

        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.args.defaults:
                        for default in node.args.defaults:
                            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                                self.issues.append({
                                    'file': file_path,
                                    'line': default.lineno,
                                    'severity': 'error',
                                    'message': (
                                        f"Mutable default argument in "
                                        f"'{node.name}'. Use None instead."
                                    ),
                                })
        except SyntaxError:
            pass

    def run_all_checks(self):
        """Run all automated checks."""
        files = self.get_changed_files()

        if not files:
            print("No Python files changed.")
            return

        print(f"Reviewing {len(files)} changed files...")

        for file_path in files:
            if not Path(file_path).exists():
                continue

            self.check_import_length(file_path)
            self.check_function_length(file_path)
            self.check_todo_comments(file_path)
            self.check_print_statements(file_path)
            self.check_empty_except(file_path)
            self.check_mutable_defaults(file_path)

        # Print results
        if not self.issues:
            print("No issues found.")
            return

        # Group by severity
        for severity in ['error', 'warning', 'info']:
            level_issues = [i for i in self.issues if i['severity'] == severity]
            if level_issues:
                print(f"\n{severity.upper()} ({len(level_issues)}):")
                for issue in level_issues:
                    print(f"  {issue['file']}:{issue['line']} - {issue['message']}")

        # Exit with error if critical issues found
        errors = [i for i in self.issues if i['severity'] == 'error']
        if errors:
            sys.exit(1)


if __name__ == '__main__':
    reviewer = AutomatedReview()
    reviewer.run_all_checks()
```

### Example 7: Code Review Metrics and Analytics

```python
"""
Track and analyze code review metrics.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class PullRequest:
    id: str
    author: str
    title: str
    created_at: datetime
    merged_at: Optional[datetime]
    lines_changed: int
    files_changed: int
    review_count: int
    comment_count: int
    has_conflicts: bool
    ci_passes: bool
    approvers: List[str]


class CodeReviewAnalytics:
    """Analyze code review patterns and metrics."""

    def __init__(self, prs: List[PullRequest]):
        self.prs = prs

    @property
    def total_prs(self) -> int:
        return len(self.prs)

    @property
    def merged_prs(self) -> List[PullRequest]:
        return [pr for pr in self.prs if pr.merged_at]

    @property
    def merge_rate(self) -> float:
        if not self.prs:
            return 0.0
        return (len(self.merged_prs) / len(self.prs)) * 100

    @property
    def average_time_to_merge(self) -> timedelta:
        merged = self.merged_prs
        if not merged:
            return timedelta()
        times = [(pr.merged_at - pr.created_at) for pr in merged]
        return sum(times, timedelta()) / len(times)

    @property
    def average_reviews_per_pr(self) -> float:
        if not self.prs:
            return 0.0
        return sum(pr.review_count for pr in self.prs) / len(self.prs)

    @property
    def average_comments_per_pr(self) -> float:
        if not self.prs:
            return 0.0
        return sum(pr.comment_count for pr in self.prs) / len(self.prs)

    @property
    def average_lines_changed(self) -> float:
        if not self.prs:
            return 0.0
        return sum(pr.lines_changed for pr in self.prs) / len(self.prs)

    def top_reviewers(self, limit: int = 5) -> List[str]:
        """Get the most active reviewers."""
        reviewer_counts = defaultdict(int)
        for pr in self.prs:
            for approver in pr.approvers:
                reviewer_counts[approver] += 1
        return sorted(reviewer_counts, key=reviewer_counts.get,
                      reverse=True)[:limit]

    def pr_size_distribution(self) -> dict:
        """Analyze PR size distribution."""
        distribution = {
            'small': 0,      # < 100 lines
            'medium': 0,     # 100-400 lines
            'large': 0,      # 400-1000 lines
            'xlarge': 0,     # > 1000 lines
        }
        for pr in self.prs:
            if pr.lines_changed < 100:
                distribution['small'] += 1
            elif pr.lines_changed < 400:
                distribution['medium'] += 1
            elif pr.lines_changed < 1000:
                distribution['large'] += 1
            else:
                distribution['xlarge'] += 1
        return distribution

    def author_productivity(self) -> dict:
        """Analyze author productivity."""
        author_stats = defaultdict(lambda: {
            'total': 0, 'merged': 0, 'lines': 0,
        })
        for pr in self.prs:
            author_stats[pr.author]['total'] += 1
            author_stats[pr.author]['lines'] += pr.lines_changed
            if pr.merged_at:
                author_stats[pr.author]['merged'] += 1

        return dict(author_stats)

    def review_time_by_size(self) -> dict:
        """Analyze review time by PR size."""
        size_buckets = {
            'small': [], 'medium': [], 'large': [], 'xlarge': [],
        }

        for pr in self.merged_prs:
            duration = (pr.merged_at - pr.created_at).total_seconds() / 3600  # hours
            if pr.lines_changed < 100:
                size_buckets['small'].append(duration)
            elif pr.lines_changed < 400:
                size_buckets['medium'].append(duration)
            elif pr.lines_changed < 1000:
                size_buckets['large'].append(duration)
            else:
                size_buckets['xlarge'].append(duration)

        return {
            size: (sum(times) / len(times)) if times else 0
            for size, times in size_buckets.items()
        }

    def generate_report(self) -> str:
        """Generate comprehensive review analytics report."""
        size_dist = self.pr_size_distribution()
        time_by_size = self.review_time_by_size()

        report = [
            "Code Review Analytics Report",
            "=" * 60,
            f"Period: Last {len(self.prs)} Pull Requests",
            "",
            "Overview:",
            f"  Total PRs: {self.total_prs}",
            f"  Merged: {len(self.merged_prs)} ({self.merge_rate:.0f}%)",
            f"  Avg Time to Merge: {self.average_time_to_merge}",
            f"  Avg Reviews per PR: {self.average_reviews_per_pr:.1f}",
            f"  Avg Comments per PR: {self.average_comments_per_pr:.1f}",
            f"  Avg Lines Changed: {self.average_lines_changed:.0f}",
            "",
            "PR Size Distribution:",
            f"  Small (< 100): {size_dist['small']}",
            f"  Medium (100-400): {size_dist['medium']}",
            f"  Large (400-1000): {size_dist['large']}",
            f"  XLarge (> 1000): {size_dist['xlarge']}",
            "",
            "Review Time by Size (avg hours):",
            f"  Small: {time_by_size['small']:.1f}h",
            f"  Medium: {time_by_size['medium']:.1f}h",
            f"  Large: {time_by_size['large']:.1f}h",
            f"  XLarge: {time_by_size['xlarge']:.1f}h",
            "",
            "Top Reviewers:",
        ]

        for i, reviewer in enumerate(self.top_reviewers(), 1):
            report.append(f"  {i}. {reviewer}")

        report.extend([
            "",
            "Recommendations:",
        ])

        if size_dist['xlarge'] > self.total_prs * 0.1:
            report.append("  ⚠ High percentage of large PRs (>1000 lines). "
                          "Encourage smaller PRs for faster reviews.")

        if time_by_size['small'] > 24:
            report.append("  ⚠ Even small PRs take over 24 hours to review. "
                          "Consider assigning reviewers explicitly.")

        return "\n".join(report)
```

## Best Practices

### For Authors

- Review your own code before requesting reviews
- Keep pull requests small and focused (under 400 lines)
- Write clear PR descriptions explaining what and why
- Add context: screenshots, test results, performance data
- Respond to review comments promptly
- Don't take feedback personally; it's about the code, not you
- Explain your reasoning when you disagree with feedback

### For Reviewers

- Review promptly (within 24 hours for standard PRs)
- Be respectful and constructive in your comments
- Focus on the code, not the person
- Explain the why behind your suggestions, not just the what
- Distinguish between must-fix, should-fix, and nice-to-have
- Ask questions instead of making demands
- Provide specific examples and suggestions
- Approve when you're satisfied, don't leave PRs hanging

### For Teams

- Establish and document coding standards
- Use a PR template to ensure consistent information
- Set up automated checks (lint, test, security) in CI
- Define SLAs for review turnaround time
- Rotate reviewers to spread knowledge
- Hold retrospectives on review process
- Track review metrics to identify bottlenecks

## Common Mistakes

- **Reviewing too much code at once**: Large PRs are harder to review thoroughly. Split changes into smaller, logical units.
- **Nitpicking style over substance**: Spend review energy on logic, security, and correctness, not formatting preferences.
- **Rubber-stamping**: Approving without thorough review defeats the purpose. Every review deserves attention.
- **Bike-shedding**: Spending disproportionate time on trivial issues while ignoring significant problems.
- **Personal attacks**: "This is wrong" is better than "You're wrong." Focus on the code, not the developer.
- **Not reviewing tests**: Tests are as important as production code. Review them thoroughly.
- **Delayed reviews**: PRs that sit for days lose context and slow down the entire team.
- **Assuming the author's intent**: Ask clarifying questions instead of assuming you understand the context.
- **Not providing positive feedback**: Acknowledging good solutions reinforces good practices.
- **Forgetting security**: Security issues in code reviews are the most cost-effective time to find them.

## Libraries

### Code Review Tools

| Tool | Purpose |
|------|---------|
| GitHub | Pull request review platform |
| GitLab | Merge request review platform |
| Bitbucket | Pull request review platform |
| Gerrit | Code review for Git projects |
| Review Board | Web-based code review tool |
| Phabricator | Differential code review |
| Crucible | Enterprise code review tool |

### Automation Tools

| Tool | Purpose |
|------|---------|
| Danger | Automated PR checks (JS/TS/Ruby) |
| SonarQube | Code quality and security analysis |
| CodeClimate | Automated code review |
| ESLint | JavaScript linting |
| Pylint | Python linting |
| RuboCop | Ruby static analysis |
| Reviewdog | Automated review comment posting |

## Design Principles

### Review for Understanding, Not Just Correctness

The goal is not just to catch bugs but to ensure that the reviewer understands the code well enough to maintain it. If a reviewer cannot understand the code, the code needs improvement even if it is functionally correct.

### Small Changes, Fast Reviews

The optimal PR size is one that can be thoroughly reviewed in under 30 minutes. Small PRs get reviewed faster, have fewer defects, and reduce merge conflicts. Strive for PRs under 400 lines.

### Blameless Reviews

Code review is about improving code quality, not assigning blame. Feedback should be objective, specific, and focused on the code. Reviews should leave every participant feeling that they learned something.

### Automate the Obvious, Review the Subtle

Style issues, formatting, and simple lint rules should be automated. Human review time should be spent on logic, architecture, security, and design. Invest in CI automation to reduce cognitive load on reviewers.

## Coding Standards

### PR Description Template

```markdown
## Summary
<!-- One-sentence description of the change -->

## Motivation
<!-- Why is this change needed? What problem does it solve? -->

## Changes
<!-- Key changes in bullet points -->

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing done

## Risks
<!-- What could go wrong? Any rollback concerns? -->

## Checklist
- [ ] Self-review completed
- [ ] No new warnings
- [ ] Documentation updated
- [ ] Backward-compatible
```

### Review Comment Style

```
[Type] Short subject line

Detailed explanation of the concern or suggestion. Explain why
this change is needed and (optionally) how to fix it.

**Suggestion:**
```python
# Show the suggested alternative
```

Severity guide:
- MUST FIX: Bug, security, or correctness issue
- SHOULD FIX: Best practice, performance, maintainability
- NITPICK: Minor style preference
- QUESTION: Seeking clarification
```

### Response to Review Comments

| Scenario | Response |
|----------|----------|
| Agree with suggestion | "Good catch! Fixed." |
| Adopted alternative approach | "Good point. I used a slightly different approach..." |
| Explain rationale | "I considered that, but chose this because..." |
| Defer to follow-up | "Valid point. Created issue #123 to address separately." |
| Clarify misunderstanding | "The reason for this approach is..." |
| Thank reviewer | "Thanks for the thorough review!" |
