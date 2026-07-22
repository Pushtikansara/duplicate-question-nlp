from __future__ import annotations

from ares.cli.completion import generate_bash, generate_fish, generate_zsh
from ares.cli.completion.bash import BASH_COMPLETION
from ares.cli.completion.bash import generate as bash_generate
from ares.cli.completion.fish import FISH_COMPLETION
from ares.cli.completion.fish import generate as fish_generate
from ares.cli.completion.zsh import ZSH_COMPLETION
from ares.cli.completion.zsh import generate as zsh_generate


class TestBashCompletion:
    def test_bash_generate_returns_string(self):
        result = bash_generate()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_bash_completion_contains_ares(self):
        assert "ares" in BASH_COMPLETION

    def test_bash_completion_contains_commands(self):
        assert "version" in BASH_COMPLETION
        assert "doctor" in BASH_COMPLETION
        assert "plugin" in BASH_COMPLETION
        assert "trace" in BASH_COMPLETION
        assert "benchmark" in BASH_COMPLETION
        assert "config" in BASH_COMPLETION
        assert "memory" in BASH_COMPLETION
        assert "pipeline" in BASH_COMPLETION

    def test_bash_completion_has_function(self):
        assert "_ares_completion" in BASH_COMPLETION

    def test_bash_completion_trailing_newline(self):
        result = bash_generate()
        assert result.endswith("\n")

    def test_bash_export_function(self):
        result = generate_bash()
        assert isinstance(result, str)


class TestZshCompletion:
    def test_zsh_generate_returns_string(self):
        result = zsh_generate()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_zsh_completion_contains_ares(self):
        assert "ares" in ZSH_COMPLETION

    def test_zsh_completion_has_compdef(self):
        assert "#compdef ares" in ZSH_COMPLETION

    def test_zsh_completion_has_commands(self):
        assert "version" in ZSH_COMPLETION
        assert "doctor" in ZSH_COMPLETION
        assert "plugin" in ZSH_COMPLETION
        assert "trace" in ZSH_COMPLETION

    def test_zsh_completion_has_functions(self):
        assert "_ares" in ZSH_COMPLETION
        assert "_plugin_commands" in ZSH_COMPLETION
        assert "_trace_commands" in ZSH_COMPLETION
        assert "_benchmark_commands" in ZSH_COMPLETION
        assert "_config_commands" in ZSH_COMPLETION
        assert "_memory_commands" in ZSH_COMPLETION
        assert "_pipeline_commands" in ZSH_COMPLETION

    def test_zsh_export_function(self):
        result = generate_zsh()
        assert isinstance(result, str)


class TestFishCompletion:
    def test_fish_generate_returns_string(self):
        result = fish_generate()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_fish_completion_contains_ares(self):
        assert "ares" in FISH_COMPLETION

    def test_fish_completion_has_commands(self):
        assert "version" in FISH_COMPLETION
        assert "doctor" in FISH_COMPLETION
        assert "plugin" in FISH_COMPLETION
        assert "trace" in FISH_COMPLETION
        assert "config" in FISH_COMPLETION

    def test_fish_completion_has_flags(self):
        assert "verbose" in FISH_COMPLETION
        assert "debug" in FISH_COMPLETION
        assert "quiet" in FISH_COMPLETION
        assert "output" in FISH_COMPLETION

    def test_fish_completion_subcommands(self):
        assert "list" in FISH_COMPLETION
        assert "install" in FISH_COMPLETION
        assert "enable" in FISH_COMPLETION
        assert "disable" in FISH_COMPLETION
        assert "inspect" in FISH_COMPLETION
        assert "search" in FISH_COMPLETION

    def test_fish_export_function(self):
        result = generate_fish()
        assert isinstance(result, str)

    def test_fish_completion_predict(self):
        assert "predict" in FISH_COMPLETION

    def test_fish_completion_export(self):
        assert "export" in FISH_COMPLETION
