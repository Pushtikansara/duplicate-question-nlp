# ARES CLI Commands

## System Commands

### `ares version`

Show ARES version and Python/platform information.

```bash
ares version
```

### `ares info`

Display system information including Python version, platform, CPU cores, memory, and project root.

```bash
ares info
```

### `ares status`

Alias for `ares info`.

```bash
ares status
```

### `ares doctor`

Run comprehensive system diagnostics with pass/warning/fail results.

```bash
ares doctor
ares doctor --verbose     # Include observability checks
ares doctor --models      # Check all model availability
```

## Plugin Management

### `ares plugin list`

List all installed plugins.

```bash
ares plugin list
ares plugin list --status ACTIVE   # Filter by status
ares plugin list --verbose          # Show capabilities
```

### `ares plugin install`

Install a plugin from a path.

```bash
ares plugin install /path/to/plugin
```

### `ares plugin uninstall`

Uninstall a plugin by ID.

```bash
ares plugin uninstall my_plugin
ares plugin uninstall my_plugin --force   # Skip confirmation
```

### `ares plugin enable`

Enable a disabled plugin.

```bash
ares plugin enable my_plugin
```

### `ares plugin disable`

Disable an active plugin.

```bash
ares plugin disable my_plugin
```

### `ares plugin inspect`

View detailed plugin metadata.

```bash
ares plugin inspect my_plugin
```

### `ares plugin search`

Search plugins by name, ID, or description.

```bash
ares plugin search query
```

## Trace Management

### `ares trace run`

Run a decision trace for a question pair.

```bash
ares trace run "question1" "question2"
ares trace run "q1" "q2" --output trace.json
```

### `ares trace inspect`

Inspect a saved trace file.

```bash
ares trace inspect trace.json
```

### `ares trace export`

Export a trace in JSON or Chrome trace format.

```bash
ares trace export trace.json output.json
ares trace export trace.json chrome.json --format chrome
```

### `ares trace replay`

Replay a saved trace.

```bash
ares trace replay trace.json
```

## Benchmarking

### `ares benchmark run`

Run benchmark suite.

```bash
ares benchmark run
ares benchmark run --config fast           # Use specific config
ares benchmark run --output results.json   # Save results
ares benchmark run --epochs 3              # Multiple epochs
```

### `ares benchmark list`

List available benchmark results.

```bash
ares benchmark list
```

### `ares benchmark compare`

Compare two benchmark results.

```bash
ares benchmark compare bench_a bench_b
```

## Profiling & Metrics

### `ares profile`

Generate a profiling report.

```bash
ares profile
ares profile --output profile.json
ares profile --output chrome.json --format chrome   # Chrome trace format
```

### `ares metrics show`

Show profiled function metrics.

```bash
ares metrics show
```

### `ares metrics export`

Export metrics to file.

```bash
ares metrics export metrics.json
```

### `ares stats show`

Show runtime statistics.

```bash
ares stats show
```

### `ares stats export`

Export statistics to file.

```bash
ares stats export stats.json
```

## Configuration

### `ares config show`

Display current configuration.

```bash
ares config show              # Show default sections
ares config show app          # Show specific section
ares config show --verbose    # Show all sections
```

### `ares config edit`

Edit project configuration in your editor.

```bash
ares config edit   # Opens $EDITOR or vi
```

### `ares config validate`

Validate configuration files.

```bash
ares config validate
```

### `ares config export`

Export configuration to file.

```bash
ares config export config.json
ares config export config.yaml --format yaml
```

## Memory Management

### `ares memory list`

List memory entries.

```bash
ares memory list
ares memory list --type semantic    # Filter by type
ares memory list --limit 50         # Limit results
```

### `ares memory search`

Search memory entries.

```bash
ares memory search "query"
ares memory search "query" --limit 5
```

### `ares memory stats`

Show memory statistics.

```bash
ares memory stats
```

### `ares memory clean`

Consolidate and clean memory.

```bash
ares memory clean              # With confirmation
ares memory clean --force       # Skip confirmation
ares memory clean --type episodic   # Clean specific type
```

## Pipeline

### `ares pipeline inspect`

Show pipeline module status.

```bash
ares pipeline inspect
```

### `ares pipeline graph`

Generate pipeline dependency graph.

```bash
ares pipeline graph
ares pipeline graph --output graph.json
```

### `ares pipeline run`

Run the full cognitive pipeline.

```bash
ares pipeline run "question1" "question2"
ares pipeline run "q1" "q2" --output result.json
```

## Server

### `ares serve`

Start the ARES Streamlit server.

```bash
ares serve                          # Uses run_app.py
ares serve --app app/app.py         # Custom app path
ares serve --host 0.0.0.0 --port 8501
ares serve --app app/app.py --dev   # Dev mode with hot reload
```

## Shell

### `ares shell`

Start an interactive Python shell with ARES pre-loaded.

```bash
ares shell
```

The shell provides `ARES` and `PredictionResult` in the namespace.

## Predict

### `ares predict`

Make a prediction (backward-compatible entry point).

```bash
ares predict "question1" "question2"
ares predict "q1" "q2" --model "Improved DistilBERT (Week 4)"
ares predict "q1" "q2" --threshold 0.7
ares predict "q1" "q2" --reflect
ares predict "q1" "q2" --json
```

## Export

### `ares export`

Export system data.

```bash
ares export export.json
ares export export.yaml --format yaml
ares export partial.json --sections version,config
```
