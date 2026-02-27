#!/usr/bin/env python3
"""Remove Claude Code metrics env vars from ~/.claude/settings.json.

Removes only the env vars defined in this directory's settings.json
template — all other settings are preserved.
"""

import json
import sys
from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent / "settings.json"
TARGET_PATH = Path.home() / ".claude" / "settings.json"


def main():
    if not TARGET_PATH.exists():
        print(f"{TARGET_PATH} does not exist, nothing to do.")
        return

    template = json.loads(TEMPLATE_PATH.read_text())
    keys_to_remove = set(template["env"].keys())

    target = json.loads(TARGET_PATH.read_text())
    env = target.get("env", {})

    removed = [key for key in keys_to_remove if key in env]
    for key in removed:
        del env[key]

    if not env:
        del target["env"]

    TARGET_PATH.write_text(json.dumps(target, indent=2) + "\n")

    if removed:
        print(f"Removed {len(removed)} env vars from {TARGET_PATH}:")
        for key in removed:
            print(f"  {key}")
    else:
        print("No matching env vars found, nothing removed.")


if __name__ == "__main__":
    main()
