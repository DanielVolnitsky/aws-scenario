#!/usr/bin/env python3
"""Merge Claude Code metrics env vars into ~/.claude/settings.json.

Preserves any existing settings — only adds/updates the env vars
defined in this directory's settings.json template.
"""

import json
import sys
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / "settings.json"
TARGET_PATH = Path.home() / ".claude" / "settings.json"


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <API_GATEWAY_ENDPOINT>")
        print("  e.g.: python install.py https://abc123.execute-api.us-east-1.amazonaws.com/prod")
        sys.exit(1)

    endpoint = sys.argv[1]

    template = json.loads(TEMPLATE_PATH.read_text())
    env_vars = template["env"]
    env_vars["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint

    if TARGET_PATH.exists():
        target = json.loads(TARGET_PATH.read_text())
    else:
        target = {}

    target.setdefault("env", {}).update(env_vars)

    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_text(json.dumps(target, indent=2) + "\n")

    print(f"Merged {len(env_vars)} env vars into {TARGET_PATH}:")
    for key, value in env_vars.items():
        print(f"  {key}={value}")


if __name__ == "__main__":
    main()
