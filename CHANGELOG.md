# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-19

### Added

- Phase 5: Professional packaging and developer tooling
  - `pyproject.toml` with full project metadata
  - CLI entry points: `dqd`, `dqd-app`, `dqd-predict`, `dqd-benchmark`
  - Split requirements: `requirements-dev.txt`, `requirements-test.txt`, `requirements-docs.txt`
  - `.pre-commit-config.yaml` with 10 professional hooks
  - `.editorconfig` for cross-editor consistency
  - `LICENSE` (Apache 2.0)
  - `CHANGELOG.md` (this file)
  - `CONTRIBUTING.md` with development workflow guide
  - `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1)
  - `MANIFEST.in` for sdist packaging
  - `__version__` attribute and version tracking
  - Code quality tooling: Black, Ruff, isort, mypy

- Phase 4: Configuration, logging, and error handling
  - 8 YAML configuration files under `configs/`
  - Centralized configuration loader with `DQD_*` environment overrides
  - Structured logging system (console + rotating file handlers)
  - Exception hierarchy with 10 standardized exception types
  - `.env.example` for local development
  - Print-to-logging migration in `src/duplicate_question_app/`

## [0.1.0] - 2026-07-19

### Added

- Phase 3: Layered architecture with 15 subpackages
- Phase 2: Modular Streamlit dashboard (5 packages, 41 files)
- Phase 1: Baseline research project with notebooks and monolithic app

v0.9.3

Added Enterprise Plugin System

Plugin Lifecycle

Plugin Discovery

Plugin Registry

Dependency Resolution

Plugin Configuration

77 Tests

Zero Ruff Violations
