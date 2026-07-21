from __future__ import annotations

import re


def parse_semver(version: str) -> tuple[int, int, int]:
    """Parse a semver string into a ``(major, minor, patch)`` tuple."""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version)
    if not match:
        raise ValueError(f"Invalid semver: {version!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def satisfies_spec(version: str, spec: str) -> bool:
    """Check if a version satisfies a specifier like ``>=1.0.0`` or ``>=0.2.0,<1.0``."""
    try:
        from packaging.specifiers import SpecifierSet

        return version in SpecifierSet(spec)
    except ImportError:
        return True


def normalize_plugin_id(name: str) -> str:
    """Normalize a plugin name to a canonical ID."""
    return re.sub(r"[^a-z0-9_]", "_", name.lower().strip())
