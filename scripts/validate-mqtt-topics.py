#!/usr/bin/env python3
"""
validate-mqtt-topics.py — Validate MQTT topic naming in HA configs.

Ensures all MQTT topics in home-assistant/packages/*.yaml follow the
aqua/<node>/<metric> contract defined in docs/handbook/13-interfaces.md:

  Telemetry:       aqua/<node>/<metric>
  Commands:        aqua/<node>/<actuator>/set
  Actuator state:  aqua/<node>/<actuator>/state
  LWT status:      aqua/<node>/status

Usage:
    python scripts/validate-mqtt-topics.py [path/to/home-assistant]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

# ── Topic patterns ────────────────────────────────────────────────────

# aqua/<node>/<metric>  — lowercase, kebab-case, no wildcards in published topics
# Also accepts /set (commands) and /state (actuator state feedback)
TOPIC_RE = re.compile(
    r"^aqua/"                    # prefix
    r"[a-z0-9]([a-z0-9-]*[a-z0-9])?"  # node (kebab-case)
    r"/"
    r"[a-z0-9_]+"                # metric or actuator
    r"(?:/(?:set|state))?$"      # optional /set or /state suffix
)

# Special: LWT status topic
STATUS_RE = re.compile(
    r"^aqua/[a-z0-9]([a-z0-9-]*[a-z0-9])?/status$"
)

# Keys in HA YAML that contain MQTT topics
TOPIC_KEYS = {
    "state_topic",
    "command_topic",
    "json_attributes_topic",
    "availability_topic",
    "topic",           # used in mqtt.publish service calls
    "will_topic",      # legacy
}

# ── Validator ─────────────────────────────────────────────────────────

def extract_topics(obj, path: str = "") -> list[tuple[str, str]]:
    """Recursively extract (key, topic) pairs from a nested dict/list."""
    results: list[tuple[str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in TOPIC_KEYS and isinstance(v, str):
                results.append((f"{path}.{k}", v))
            else:
                results.extend(extract_topics(v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(extract_topics(item, f"{path}[{i}]"))
    return results


def validate_topic(topic: str) -> tuple[bool, str]:
    """Return (is_valid, reason)."""
    if not topic.startswith("aqua/"):
        return False, f"does not start with 'aqua/'"

    if STATUS_RE.match(topic):
        return True, "LWT status"

    if not TOPIC_RE.match(topic):
        return False, "does not match aqua/<node>/<metric>(/set|/state)? pattern"

    return True, "OK"


def main():
    ha_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("home-assistant")
    packages_dir = ha_dir / "packages"

    if not packages_dir.exists():
        print(f"ERROR: {packages_dir} does not exist")
        sys.exit(1)

    errors: list[str] = []
    checked = 0

    for yml_file in sorted(packages_dir.glob("*.yaml")):
        with open(yml_file, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"{yml_file.name}: YAML parse error: {e}")
                continue

        topics = extract_topics(data, yml_file.stem)
        for key_path, topic in topics:
            checked += 1
            ok, reason = validate_topic(topic)
            if not ok:
                errors.append(
                    f"{yml_file.name}: {key_path} = '{topic}' — {reason}"
                )

    # Also check simulator topics if present
    sim_dir = Path("scripts/simulator")
    if sim_dir.exists():
        for py_file in sorted(sim_dir.rglob("*.py")):
            text = py_file.read_text(encoding="utf-8")
            # Find f-string topics like f"aqua/{node_id}/..."
            for m in re.finditer(r'"aqua/[^"]+"', text):
                topic = m.group(0).strip('"')
                # Skip format strings with { } — just check the literal prefix
                if not topic.startswith("aqua/"):
                    errors.append(
                        f"{py_file.name}: topic '{topic}' does not start with 'aqua/'"
                    )

    # ── Report ────────────────────────────────────────────────────────
    print(f"Checked {checked} MQTT topics in {packages_dir}/")
    if errors:
        print(f"\n❌ {len(errors)} violation(s):")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)
    else:
        print("✅ All MQTT topics conform to aqua/<node>/<metric> contract.")
        sys.exit(0)


if __name__ == "__main__":
    main()
