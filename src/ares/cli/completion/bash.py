BASH_COMPLETION = """
# ARES CLI bash completion
_ares_completion() {
    local cur prev words cword
    _init_completion || return

    local commands="version info doctor status plugin trace benchmark profile metrics stats config memory pipeline serve shell"
    local plugin_commands="list install uninstall enable disable inspect search"
    local trace_commands="run inspect export replay"
    local benchmark_commands="run list compare"
    local metrics_commands="show export"
    local stats_commands="show export"
    local config_commands="show edit validate export"
    local memory_commands="list search stats clean"
    local pipeline_commands="inspect graph run"

    if [[ $cword -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$commands" -- "$cur"))
        return
    fi

    case "${words[1]}" in
        plugin)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$plugin_commands" -- "$cur"))
            fi
            ;;
        trace)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$trace_commands" -- "$cur"))
            fi
            ;;
        benchmark)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$benchmark_commands" -- "$cur"))
            fi
            ;;
        metrics|stats)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "show export" -- "$cur"))
            fi
            ;;
        config)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$config_commands" -- "$cur"))
            fi
            ;;
        memory)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$memory_commands" -- "$cur"))
            fi
            ;;
        pipeline)
            if [[ $cword -eq 2 ]]; then
                COMPREPLY=($(compgen -W "$pipeline_commands" -- "$cur"))
            fi
            ;;
    esac
} &&
complete -F _ares_completion ares
"""


def generate() -> str:
    return BASH_COMPLETION.strip() + "\n"
