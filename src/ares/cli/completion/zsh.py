ZSH_COMPLETION = """
#compdef ares
# ARES CLI zsh completion

_ares() {
    local context state state_descr line
    typeset -A opt_args

    _arguments -C \
        '(-v --verbose)'{-v,--verbose}'[Enable verbose output]' \
        '(-d --debug)'{-d,--debug}'[Enable debug mode]' \
        '(-q --quiet)'{-q,--quiet}'[Suppress non-essential output]' \
        '(-o --output)'{-o,--output}'[Output format (text|json|yaml)]:format:(text json yaml)' \
        '(-h --help)'{-h,--help}'[Show help]' \
        '1: :->command' \
        '*:: :->args'

    case "$state" in
        command)
            local commands
            commands=(
                'version:Show version'
                'info:Show system information'
                'doctor:Run system diagnostics'
                'status:Show system status'
                'plugin:Manage plugins'
                'trace:Manage traces'
                'benchmark:Run benchmarks'
                'profile:Generate profile'
                'metrics:View metrics'
                'stats:View statistics'
                'config:Manage configuration'
                'memory:Manage memory'
                'pipeline:Manage pipelines'
                'serve:Start server'
                'shell:Start interactive shell'
            )
            _describe 'command' commands
            ;;
        args)
            case "$words[1]" in
                plugin)
                    _plugin_commands
                    ;;
                trace)
                    _trace_commands
                    ;;
                benchmark)
                    _benchmark_commands
                    ;;
                config)
                    _config_commands
                    ;;
                memory)
                    _memory_commands
                    ;;
                pipeline)
                    _pipeline_commands
                    ;;
                metrics|stats)
                    _describe 'command' '(
                        "show:Show data"
                        "export:Export data"
                    )'
                    ;;
            esac
            ;;
    esac
}

_plugin_commands() {
    _describe 'plugin command' '(
        "list:List installed plugins"
        "install:Install a plugin"
        "uninstall:Uninstall a plugin"
        "enable:Enable a plugin"
        "disable:Disable a plugin"
        "inspect:Inspect a plugin"
        "search:Search plugins"
    )'
}

_trace_commands() {
    _describe 'trace command' '(
        "run:Run a trace"
        "inspect:Inspect a trace"
        "export:Export a trace"
        "replay:Replay a trace"
    )'
}

_benchmark_commands() {
    _describe 'benchmark command' '(
        "run:Run a benchmark"
        "list:List benchmarks"
        "compare:Compare benchmarks"
    )'
}

_config_commands() {
    _describe 'config command' '(
        "show:Show configuration"
        "edit:Edit configuration"
        "validate:Validate configuration"
        "export:Export configuration"
    )'
}

_memory_commands() {
    _describe 'memory command' '(
        "list:List memory entries"
        "search:Search memory"
        "stats:Show memory statistics"
        "clean:Clean memory"
    )'
}

_pipeline_commands() {
    _describe 'pipeline command' '(
        "inspect:Inspect pipeline"
        "graph:Generate pipeline graph"
        "run:Run pipeline"
    )'
}

_ares "$@"
"""


def generate() -> str:
    return ZSH_COMPLETION.strip() + "\n"
