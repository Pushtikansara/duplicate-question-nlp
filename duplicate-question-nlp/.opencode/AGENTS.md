# Project Instructions for AI Agents

## Coding Standards

- Follow PEP8 for Python; ESLint + Prettier for JavaScript/TypeScript
- Use meaningful, self-documenting variable and function names
- Keep functions small and focused (single responsibility)
- Maximum line length: 88 for Python, 100 for JS/TS
- Use type hints in Python, strict TypeScript mode
- Prefer functional composition over deep class hierarchies
- Write pure functions where possible; isolate side effects

## Folder Structure

```
.
├── .opencode/           # AI workspace configuration
│   ├── AGENTS.md        # This file
│   ├── opencode.json    # Main config
│   ├── agent/           # Custom agents
│   ├── command/         # Custom commands
│   ├── skills/          # Skill definitions
│   ├── prompts/         # Reusable prompt templates
│   └── templates/       # Code generation templates
├── src/                 # Application source
├── tests/               # Test suite
├── data/                # Data files
├── notebooks/           # Jupyter notebooks
├── scripts/             # Utility scripts
├── models/              # Trained/saved models
├── checkpoints/         # Training checkpoints
├── results/             # Experiment outputs
├── app.py               # Main application entry
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

## Commit Style

- Use conventional commits: `type(scope): description`
- Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `security`
- Keep commits small and atomic
- Write descriptions in imperative mood: "Add", "Fix", "Refactor"
- Include issue/PR references where applicable

## Naming Convention

- Python: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE` for constants
- JavaScript/TypeScript: `camelCase` for functions/variables, `PascalCase` for components/classes, `UPPER_SNAKE` for constants
- Files: `snake_case.py`, `kebab-case.js`, `kebab-case.tsx`
- Tests: `test_<module>.py` or `<module>.test.ts`
- Database: `snake_case` for tables/columns, plural for table names

## Testing Strategy

- Write tests before implementation (TDD where practical)
- Unit tests for business logic; integration tests for API/data layers
- Use pytest for Python, vitest for JS/TS
- Aim for 80%+ code coverage
- Mock external services; test edge cases and error paths
- Tests must be deterministic and isolated

## Documentation Strategy

- Docstrings on all public APIs (Google style for Python, JSDoc for JS/TS)
- README.md with setup, usage, and architecture overview
- Keep docs in sync with code; update on behavioral changes
- Use type hints as live documentation
- Document design decisions and tradeoffs in commit messages

## Architecture Principles

- Clean Architecture: separate concerns into layers (domain, application, infrastructure)
- SOLID principles: single responsibility, open/closed, Liskov substitution, interface segregation, dependency inversion
- DRY: avoid duplication through abstraction
- KISS: prefer simple solutions over clever ones
- YAGNI: don't add features until needed
- Dependency injection for testability
- Favor composition over inheritance

## Security Checklist

- [ ] Validate and sanitize all user inputs
- [ ] Use parameterized queries to prevent SQL injection
- [ ] Never hardcode secrets, API keys, or credentials
- [ ] Use environment variables for configuration
- [ ] Apply principle of least privilege
- [ ] Hash passwords with bcrypt/argon2
- [ ] Set secure HTTP headers (CSP, CORS)
- [ ] Rate-limit API endpoints
- [ ] Log security events (not secrets)
- [ ] Keep dependencies updated (Dependabot/Renovate)

## Performance Checklist

- [ ] Profile before optimizing; measure with benchmarks
- [ ] Use lazy loading and pagination for large datasets
- [ ] Cache expensive computations (Redis, functools.lru_cache)
- [ ] Optimize database queries (indexes, select only needed columns)
- [ ] Use async/await for I/O-bound operations
- [ ] Batch database operations where possible
- [ ] Compress responses (gzip/brotli)
- [ ] Use connection pooling for databases
- [ ] Implement background task queues for heavy work (Celery, RQ)
- [ ] Monitor memory usage; avoid leaks

## UI Principles

- Follow Material Design or Apple HIG consistently
- Maintain visual hierarchy: spacing, typography, color
- Design system-driven: use shared tokens (colors, spacing, typography)
- Mobile-first responsive design
- Consistent loading, empty, error, and edge-case states
- Smooth transitions and micro-interactions (200-300ms)
- Accessible by default (see accessibility principles)

## Accessibility Principles

- WCAG 2.2 AA minimum; AAA where possible
- Semantic HTML: use proper landmarks, headings, roles
- Keyboard navigation: all interactive elements reachable and operable
- Focus management: visible focus indicators, logical tab order
- ARIA attributes: use only when native semantics insufficient
- Color contrast: minimum 4.5:1 for normal text, 3:1 for large text
- Screen reader support: meaningful alt text, labels, announcements
- Touch targets: minimum 44x44px
- Support reduced motion preference
- Test with real assistive technologies

## AI Development Workflow

1. **Understand**: Read requirements, existing code, and relevant skills
2. **Plan**: Outline approach, identify risks, gather context
3. **Implement**: Write code following standards and patterns
4. **Test**: Run existing tests, write new tests for changes
5. **Review**: Self-review for quality, security, performance
6. **Document**: Update docs, add comments for non-obvious logic
7. **Commit**: Write conventional commit message
8. **Verify**: Run full test suite and linting before PR
