from __future__ import annotations

from dataclasses import dataclass, field

import streamlit as st

from duplicate_question_app._config.settings import AppPaths

# ---------------------------------------------------------------------------
# Custom exceptions  (Phase E — defensive validation)
# ---------------------------------------------------------------------------


class ApplicationBootstrapError(RuntimeError):
    """Base class for all application startup failures.

    Every exception raised during bootstrap inherits from this class so
    that the entry point can catch a single type and display a structured
    report instead of letting raw ``AttributeError`` / ``TypeError``
    propagate to the user.
    """


class ProjectPathsInitializationError(ApplicationBootstrapError):
    """Raised when ``AppPaths`` cannot be constructed."""


class ModelRegistryNotLoaded(ApplicationBootstrapError):
    """Raised when the model registry is unavailable."""


class InferenceDispatcherMissing(ApplicationBootstrapError):
    """Raised when the ARES inference dispatcher cannot be imported."""


# ---------------------------------------------------------------------------
# ApplicationContext  — single source of truth for shared application state
# ---------------------------------------------------------------------------


@dataclass
class ApplicationContext:
    paths: AppPaths
    initialized: bool = True
    startup_errors: list[str] = field(default_factory=list)

    def has_errors(self) -> bool:
        return len(self.startup_errors) > 0

    def add_error(self, message: str) -> None:
        self.startup_errors.append(message)


# Module-level singleton (used outside Streamlit or before session state)
_context: ApplicationContext | None = None


def set_context(ctx: ApplicationContext) -> None:
    global _context
    _context = ctx


def get_context() -> ApplicationContext | None:
    """Return the active context, preferring the Streamlit session."""
    try:
        if "app_context" in st.session_state:
            return st.session_state["app_context"]
    except Exception:
        pass
    return _context


def get_paths() -> AppPaths:
    """Return the single ``AppPaths`` instance from the active context."""
    ctx = get_context()
    if ctx is not None:
        return ctx.paths
    from duplicate_question_app._config.settings import get_app_paths

    return get_app_paths()


def initialize_context(
    paths: AppPaths | None = None,
    validate: bool = True,
) -> ApplicationContext:
    """Create and register the application-wide context.

    Parameters
    ----------
    paths:
        Pre-built ``AppPaths``.  When ``None``, paths are auto-detected
        from the project root.
    validate:
        When ``True``, run startup validators immediately.
    """
    if paths is None:
        from duplicate_question_app._config.settings import get_app_paths

        paths = get_app_paths()

    ctx = ApplicationContext(paths=paths)

    if validate:
        _run_startup_validation(ctx)

    set_context(ctx)
    st.session_state["app_context"] = ctx
    return ctx


# ---------------------------------------------------------------------------
# Startup validation  (Phase F)
# ---------------------------------------------------------------------------


def _run_startup_validation(ctx: ApplicationContext) -> None:
    """Verify critical paths and dependencies are available."""
    p = ctx.paths

    # 1. Project root
    if not p.project_root.exists():
        ctx.add_error(f"Project root does not exist: {p.project_root}")

    # 2. Models directory
    if not p.models_dir.exists():
        ctx.add_error(f"Models directory not found: {p.models_dir}")

    # 3. Data directory
    if not p.data_dir.exists():
        ctx.add_error(f"Data directory not found: {p.data_dir}")

    # 4. Week 3 / Week 4 model directories
    for name, d in [("Week 3", p.week3_model_dir), ("Week 4", p.week4_model_dir)]:
        if not d.exists():
            ctx.add_error(f"{name} model directory not found: {d}")
        elif not (d / "config.json").exists():
            ctx.add_error(f"{name} config.json missing: {d / 'config.json'}")


def render_startup_report(ctx: ApplicationContext) -> None:
    """Display a structured startup report inside a Streamlit app."""
    import streamlit as st

    if not ctx.has_errors():
        return

    st.error("## Application Startup Report")
    st.markdown("The following issues were detected during startup:")

    for i, err in enumerate(ctx.startup_errors, 1):
        st.markdown(f"{i}. {err}")

    st.markdown("---")
    st.info(
        "Some features may be unavailable until the issues above are resolved. "
        "Check that all model artifacts are downloaded and paths are correct."
    )
