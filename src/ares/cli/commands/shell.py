from __future__ import annotations

import code

from ares.cli.utils.console import console


def start_shell() -> None:
    console.print("[bold cyan]ARES Interactive Shell[/bold cyan]")
    console.print("  Available: [green]ARES[/green], [green]PredictionResult[/green]")
    console.print("  Usage: engine = ARES()")
    console.print("         result = engine.predict('question1', 'question2')")
    console.print()

    try:
        from ares import ARES, PredictionResult
    except ImportError:
        ARES = None  # type: ignore[assignment]
        PredictionResult = None  # type: ignore[assignment]

    namespace = {
        "ARES": ARES,
        "PredictionResult": PredictionResult,
    }

    try:
        import readline
        import rlcompleter

        readline.set_completer(rlcompleter.Completer(namespace).complete)
        readline.parse_and_bind("tab: complete")
    except ImportError:
        pass

    shell = code.InteractiveConsole(namespace)
    shell.interact(banner="")
