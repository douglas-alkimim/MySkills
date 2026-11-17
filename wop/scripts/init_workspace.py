#!/usr/bin/env python3
"""Create and validate a persistent WOP workspace without overwriting data."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wop_db import WopError, initialize


def run() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Project root")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()
    try:
        result = initialize(args.root)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            for key, value in result.items():
                print(f"{key}: {value}")
        return 0 if result["foreign_keys"] and result["integrity"] == "ok" else 2
    except (WopError, OSError) as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}), file=sys.stderr)
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(run())
