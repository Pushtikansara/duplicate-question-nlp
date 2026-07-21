from __future__ import annotations

from dataclasses import dataclass, field

from ares.plugins.types import PluginCapability, PluginDependency


@dataclass
class PluginMetadata:
    """Declared metadata every plugin must provide."""

    name: str
    author: str
    version: str
    description: str = ""
    license: str = "MIT"
    homepage: str = ""
    repository: str = ""
    compatible_sdk: str = ">=0.2.0"
    priority: int = 100
    enabled_by_default: bool = True
    tags: list[str] = field(default_factory=list)
    category: str = "generic"
    capabilities: list[PluginCapability] = field(default_factory=list)
    dependencies: list[PluginDependency] = field(default_factory=list)

    def validate(self) -> None:
        """Basic self-validation; raises PluginValidationError on failure."""
        from ares.plugins.exceptions import PluginValidationError

        if not self.name or not self.name.strip():
            raise PluginValidationError("Plugin name is required")
        if not self.author or not self.author.strip():
            raise PluginValidationError("Plugin author is required")
        if not self.version or not self.version.strip():
            raise PluginValidationError("Plugin version is required")
        import re

        if not re.match(r"^[\w\-\.]+$", self.name):
            raise PluginValidationError(f"Invalid plugin name: {self.name!r}")
