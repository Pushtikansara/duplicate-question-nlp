# Contributing to Duplicate Question Detection

Thank you for your interest in contributing! We welcome contributions from everyone.

## Code of Conduct

This project adheres to the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Development Workflow

1. **Fork** the repository and create your branch from `develop`.
2. **Set up** your local environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev,test]"
   pre-commit install
   ```
3. **Make changes** on your feature branch.
4. **Run quality checks** before committing:
   ```bash
   black src/ app/
   ruff check src/ app/
   isort --check src/ app/
   mypy src/duplicate_question_app/
   pytest
   ```
5. **Commit** using clear commit messages following [Conventional Commits](https://www.conventionalcommits.org/):
   ```
   feat: add new model ensemble strategy
   fix: correct threshold calibration for cross-encoder
   chore: update dependencies
   docs: add API reference for inference module
   refactor: extract path resolution into config loader
   ```
6. **Push** and open a Pull Request against the `develop` branch.

## Pull Request Guidelines

- Keep PRs focused on a single concern.
- Update the CHANGELOG.md if the change is user-facing.
- Add or update tests for any new functionality.
- Ensure all CI checks pass.
- Request review from at least one maintainer.

## Project Structure

```
duplicate-question-detection/
├── src/duplicate_question_app/   # Main Python package
│   ├── _config/                  # Configuration, logging, exceptions
│   ├── _models/                  # Model loading and inference
│   ├── _inference/               # Inference services
│   ├── _training/                # Training utilities
│   ├── _evaluation/              # Evaluation metrics
│   ├── _dataset/                 # Data loading
│   ├── _preprocessing/           # Text preprocessing
│   ├── _calibration/             # Probability calibration
│   ├── _ensemble/                # Ensemble strategies
│   ├── _explainability/          # Model explanations
│   ├── _linguistics/             # Linguistic analysis
│   ├── _artifacts/               # Model artifacts
│   ├── _visualization/           # Visualization utilities
│   ├── _logging/                 # Error-driven learning logging
│   ├── _testing/                 # Hard test generation
│   └── utils/                    # Shared utilities
├── app/                          # Streamlit dashboard
├── configs/                      # YAML configuration files
├── tools/                        # CLI utility scripts
└── tests/                        # Test suite
```

## Coding Standards

- **Python**: 3.10+
- **Formatter**: Black (line-length 120)
- **Linter**: Ruff
- **Imports**: isort (compatible with Black)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google-style for public APIs

## Configuration

All configuration lives in `configs/*.yaml`. Environment overrides use the `DQD_` prefix:

```bash
DQD_DEVICE=cuda DQD_LOG_LEVEL=DEBUG dqd-app
```

See `.env.example` for the full list of available overrides.

## Testing

Run the test suite with:

```bash
pytest
```

Tests are located in `tests/` and mirror the `src/` package structure.

## Questions?

Open a [GitHub Discussion](https://github.com/your-org/duplicate-question-detection/discussions) for general questions or the [Issue Tracker](https://github.com/your-org/duplicate-question-detection/issues) for bugs and feature requests.
