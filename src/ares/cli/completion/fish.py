FISH_COMPLETION = """
# ARES CLI fish completion
complete -c ares -f

# Global options
complete -c ares -s v -l verbose -d "Enable verbose output"
complete -c ares -s d -l debug -d "Enable debug mode"
complete -c ares -s q -l quiet -d "Suppress non-essential output"
complete -c ares -s o -l output -d "Output format" -xa "text json yaml"
complete -c ares -s h -l help -d "Show help"

# Top-level commands
complete -c ares -n "__fish_use_subcommand" -xa "version" -d "Show version"
complete -c ares -n "__fish_use_subcommand" -xa "info" -d "Show system information"
complete -c ares -n "__fish_use_subcommand" -xa "doctor" -d "Run system diagnostics"
complete -c ares -n "__fish_use_subcommand" -xa "status" -d "Alias for info"
complete -c ares -n "__fish_use_subcommand" -xa "plugin" -d "Manage plugins"
complete -c ares -n "__fish_use_subcommand" -xa "trace" -d "Manage traces"
complete -c ares -n "__fish_use_subcommand" -xa "benchmark" -d "Run benchmarks"
complete -c ares -n "__fish_use_subcommand" -xa "profile" -d "Generate profile"
complete -c ares -n "__fish_use_subcommand" -xa "metrics" -d "View metrics"
complete -c ares -n "__fish_use_subcommand" -xa "stats" -d "View statistics"
complete -c ares -n "__fish_use_subcommand" -xa "config" -d "Manage configuration"
complete -c ares -n "__fish_use_subcommand" -xa "memory" -d "Manage memory"
complete -c ares -n "__fish_use_subcommand" -xa "pipeline" -d "Manage pipelines"
complete -c ares -n "__fish_use_subcommand" -xa "serve" -d "Start server"
complete -c ares -n "__fish_use_subcommand" -xa "shell" -d "Start interactive shell"
complete -c ares -n "__fish_use_subcommand" -xa "predict" -d "Make a prediction"
complete -c ares -n "__fish_use_subcommand" -xa "export" -d "Export system data"

# Plugin subcommands
complete -c ares -n "__fish_seen_subcommand_from plugin" -xa "list" -d "List installed plugins"
complete -c ares -n "__fish_seen_subcommand_from plugin" -xa "install" -d "Install a plugin"
complete -c ares -n "__fish_seen_subcommand_from plugin" -xa "uninstall" -d "Uninstall a plugin"
complete -c ares -n "__fish_seen_subcommand_from plugin" -xa "enable" -d "Enable a plugin"
complete -c ares -n "__fish_seen_subcommand_from plugin" -xa "disable" -d "Disable a plugin"
complete -c ares -n "__fish_seen_subcommand_from plugin" -xa "inspect" -d "Inspect a plugin"
complete -c ares -n "__fish_seen_subcommand_from plugin" -xa "search" -d "Search plugins"

# Trace subcommands
complete -c ares -n "__fish_seen_subcommand_from trace" -xa "run" -d "Run a trace"
complete -c ares -n "__fish_seen_subcommand_from trace" -xa "inspect" -d "Inspect a trace"
complete -c ares -n "__fish_seen_subcommand_from trace" -xa "export" -d "Export a trace"
complete -c ares -n "__fish_seen_subcommand_from trace" -xa "replay" -d "Replay a trace"

# Benchmark subcommands
complete -c ares -n "__fish_seen_subcommand_from benchmark" -xa "run" -d "Run a benchmark"
complete -c ares -n "__fish_seen_subcommand_from benchmark" -xa "list" -d "List benchmarks"
complete -c ares -n "__fish_seen_subcommand_from benchmark" -xa "compare" -d "Compare benchmarks"

# Metrics subcommands
complete -c ares -n "__fish_seen_subcommand_from metrics" -xa "show" -d "Show metrics"
complete -c ares -n "__fish_seen_subcommand_from metrics" -xa "export" -d "Export metrics"

# Stats subcommands
complete -c ares -n "__fish_seen_subcommand_from stats" -xa "show" -d "Show statistics"
complete -c ares -n "__fish_seen_subcommand_from stats" -xa "export" -d "Export statistics"

# Config subcommands
complete -c ares -n "__fish_seen_subcommand_from config" -xa "show" -d "Show configuration"
complete -c ares -n "__fish_seen_subcommand_from config" -xa "edit" -d "Edit configuration"
complete -c ares -n "__fish_seen_subcommand_from config" -xa "validate" -d "Validate configuration"
complete -c ares -n "__fish_seen_subcommand_from config" -xa "export" -d "Export configuration"

# Memory subcommands
complete -c ares -n "__fish_seen_subcommand_from memory" -xa "list" -d "List memory entries"
complete -c ares -n "__fish_seen_subcommand_from memory" -xa "search" -d "Search memory"
complete -c ares -n "__fish_seen_subcommand_from memory" -xa "stats" -d "Show memory statistics"
complete -c ares -n "__fish_seen_subcommand_from memory" -xa "clean" -d "Clean memory"

# Pipeline subcommands
complete -c ares -n "__fish_seen_subcommand_from pipeline" -xa "inspect" -d "Inspect pipeline"
complete -c ares -n "__fish_seen_subcommand_from pipeline" -xa "graph" -d "Generate pipeline graph"
complete -c ares -n "__fish_seen_subcommand_from pipeline" -xa "run" -d "Run pipeline"
"""


def generate() -> str:
    return FISH_COMPLETION.strip() + "\n"
