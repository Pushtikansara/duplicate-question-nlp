# ARES CLI

ARES (Adaptive Reasoning Engine for Semantic Understanding) ships with a
production-grade command-line interface built on **Typer** and **Rich**.

## Entry Point

```bash
ares [OPTIONS] COMMAND [ARGS]...
```

## Global Options

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Enable verbose output |
| `-d, --debug` | Enable debug mode |
| `-q, --quiet` | Suppress non-essential output |
| `-o, --output text\|json\|yaml` | Output format |
| `--help, -h` | Show help message |

## Architecture

The CLI follows a strict **presentation-layer** pattern:

- Every command delegates to existing framework services
- No business logic is duplicated in the CLI layer
- Commands reuse APIs from `duplicate_question_app.*` and `ares.plugins.*`
- Rich formatting is applied to all terminal output
- JSON and YAML output are supported via `--output`

## Shell Completions

Generate completion scripts for your shell:

```bash
# Bash
ares --install-completion bash

# Zsh
ares --install-completion zsh

# Fish
ares --install-completion fish
```

Completion scripts are also available in `src/ares/cli/completion/`:

| Shell | File |
|-------|------|
| Bash | `src/ares/cli/completion/bash.py` |
| Zsh | `src/ares/cli/completion/zsh.py` |
| Fish | `src/ares/cli/completion/fish.py` |

## Framework Integration

### Configuration Layering

Configuration is resolved with the following priority (highest first):

1. CLI flags and options
2. Environment variables (`ARES_*`)
3. Project config (`.ares.toml`)
4. Global config (`~/.ares/config.toml`)
5. System YAML files (`configs/*.yaml`)
6. Built-in defaults

### Doctor Diagnostics

The `ares doctor` command runs 12+ production diagnostics:

- Python version (requires >= 3.10)
- Operating system detection
- CPU core count and model
- Memory usage (via psutil)
- GPU availability and CUDA version
- PyTorch version
- All core dependencies (torch, transformers, pandas, numpy, etc.)
- Configuration file loading
- Application path integrity
- Model selection and availability (Week 3, Week 4)
- Cache status (embedding cache hit rate)
- Disk space
- Plugin health
- Observability status (verbose mode)

### Output Formats

All commands support three output formats via `--output`:

- `text` (default) — Rich-formatted terminal output
- `json` — Machine-parseable JSON
- `yaml` — YAML structured output

### Error Handling

- Errors are displayed with Rich formatting (red, bold)
- Exit codes follow conventions: 0 = success, 1 = error, 2 = usage error
- Confirmation prompts protect destructive operations
- The `handle_cli_error` decorator catches and formats exceptions
