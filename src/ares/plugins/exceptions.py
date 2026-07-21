from __future__ import annotations


class PluginError(Exception):
    """Base exception for all plugin system errors."""


class PluginLoadError(PluginError):
    """Raised when a plugin cannot be loaded."""


class PluginValidationError(PluginError):
    """Raised when plugin metadata validation fails."""


class PluginDependencyError(PluginError):
    """Raised when a dependency resolution fails."""


class PluginExecutionError(PluginError):
    """Raised when a plugin hook raises during execution."""


class PluginConfigurationError(PluginError):
    """Raised when plugin configuration is invalid."""


class PluginNotFoundError(PluginError):
    """Raised when a plugin ID is not found in the registry."""


class PluginCycleError(PluginDependencyError):
    """Raised when a cyclic dependency is detected."""


class PluginIncompatibleError(PluginError):
    """Raised when plugin SDK version is incompatible."""
