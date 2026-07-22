# ARES CLI Configuration

## Configuration Layering

ARES resolves configuration from multiple sources with the following
priority (highest wins):

```
CLI Flags / Options          Highest priority
        ↓
Environment Variables
        ↓
Project Config (.ares.toml)
        ↓
Global Config (~/.ares/config.toml)
        ↓
YAML Config Files (configs/*.yaml)
        ↓
Built-in Defaults           Lowest priority
```

## Config File Locations

| Level | Path | Purpose |
|-------|------|---------|
| Global | `~/.ares/config.toml` | User-wide settings |
| Project | `.ares.toml` | Per-project settings |
| System | `configs/*.yaml` | Application defaults |

## Environment Variables

ARES respects standard environment variables:

- `EDITOR` — Editor used by `ares config edit` (default: `vi`)
- `ARES_*` — ARES-specific overrides (reserved for future use)

## CLI Output Format

All commands accept the `--output` / `-o` option:

| Value | Description |
|-------|-------------|
| `text` | Rich-formatted terminal output (default) |
| `json` | Machine-parseable JSON |
| `yaml` | YAML structured output |

## Verbosity Levels

| Flag | Effect |
|------|--------|
| `-v, --verbose` | Show additional detail where available |
| `-d, --debug` | Enable debug mode (future: debug-level logging) |
| `-q, --quiet` | Suppress all non-essential output |

## YAML Config Sections

The system configuration is stored in `configs/`:

| File | Section(s) | Contents |
|------|------------|----------|
| `app.yaml` | `app` | Default model, threshold, device |
| `inference.yaml` | `inference` | Model config, batch sizes, sigmoid params |
| `models.yaml` | `models` | Model registry, model choices |
| `paths.yaml` | `paths` | Directory paths for data, models, outputs |
| `logging.yaml` | `logging` | Log levels, formatters, file output |
| `training.yaml` | `training` | Training hyperparameters |
| `evaluation.yaml` | `evaluation` | Evaluation config |
| `dataset.yaml` | `dataset` | Dataset paths and metadata |

## Viewing Configuration

```bash
# Show default sections (app, paths, inference, logging)
ares config show

# Show all sections
ares config show --verbose

# Show specific section
ares config show app

# Validate configuration
ares config validate

# Export all config to file
ares config export config.json
```
