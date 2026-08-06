#!/usr/bin/env python3
"""
validate-yaml.py — Validate YAML syntax for all config files.

Checks that all .yaml/.yml files in the repo can be parsed without errors.
Intended for CI — exits non-zero on any parse failure.

Usage:
    python scripts/validate-yaml.py [path1] [path2] ...
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Windows GBK console can't encode emoji in stdout; force UTF-8.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ── Custom loader that ignores ESPHome/HA custom tags ─────────────────
# ESPHome uses !secret, !include, !extend, etc. We just want to verify
# the YAML *syntax* is valid, not resolve these tags.
class _PermissiveLoader(yaml.SafeLoader):
    pass


def _ignore_unknown(loader, tag_suffix, node):
    """Treat unknown tags (e.g. !secret, !include) as their scalar value."""
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    if isinstance(node, yaml.MappingNode):
        return loader.construct_mapping(node)
    return None


_PermissiveLoader.add_multi_constructor("!", _ignore_unknown)

# Directories to scan (relative to repo root)
DEFAULT_PATHS = [
    "home-assistant",
    "firmware/esphome",
    ".github/workflows",
    "scripts/simulator",
    "deploy",
]

# Files to skip (example/template files)
SKIP_PATTERNS = {
    "secrets.example.yaml",
    "config.example.yaml",
}


def main():
    repo_root = Path(__file__).resolve().parent.parent

    paths = []
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            paths.append(repo_root / arg)
    else:
        for p in DEFAULT_PATHS:
            paths.append(repo_root / p)

    errors: list[str] = []
    checked = 0

    for base in paths:
        if not base.exists():
            continue

        if base.is_file():
            yml_files = [base]
        else:
            yml_files = sorted(
                list(base.rglob("*.yaml")) + list(base.rglob("*.yml"))
            )

        for yml_file in yml_files:
            if yml_file.name in SKIP_PATTERNS:
                continue

            rel = yml_file.relative_to(repo_root)
            try:
                with open(yml_file, "r", encoding="utf-8") as f:
                    yaml.load(f, Loader=_PermissiveLoader)
                checked += 1
            except yaml.YAMLError as e:
                errors.append(f"{rel}: {e}")
            except Exception as e:
                errors.append(f"{rel}: {e}")

    print(f"Checked {checked} YAML files.")
    if errors:
        print(f"\n❌ {len(errors)} error(s):")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print("✅ All YAML files parse successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()
