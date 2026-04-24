#!/usr/bin/env python3
"""Load .codeguidelines.toml defaults and merge with CLI flags.

Output format (KEY=value, one per line, shell-eval safe):
    LANGUAGES=go,typescript
    EXCLUDE_RULES=STYLE-002
    RULES=
    EXCLUDE_PATHS=vendor/**,**/*.gen.go
    FAIL_ON_WARNING=false

Precedence: CLI flag > TOML > built-in default.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:
    tomllib = None  # type: ignore


def main() -> int:
    args = _parse_args()
    config = _load_toml(Path(args.config))
    run_section = config.get("run", {})
    print(f"LANGUAGES={_pick_csv(args.languages, run_section.get('languages'))}")
    print(f"RULES={_pick_csv(args.rules, run_section.get('rules'))}")
    print(f"EXCLUDE_RULES={_pick_csv(args.exclude_rules, run_section.get('exclude-rules'))}")
    print(f"EXCLUDE_PATHS={_pick_csv(args.exclude_paths, run_section.get('exclude-paths'))}")
    print(f"FAIL_ON_WARNING={_pick_bool(args.fail_on_warning, run_section.get('fail-on-warning'))}")
    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--languages", default="")
    p.add_argument("--rules", default="")
    p.add_argument("--exclude-rules", default="")
    p.add_argument("--exclude-paths", default="")
    p.add_argument("--fail-on-warning", default="")
    return p.parse_args()


def _load_toml(path: Path) -> dict:
    if not path.exists() or tomllib is None:
        return {}
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _pick_csv(cli_value: str, toml_value) -> str:
    if cli_value:
        return cli_value
    if isinstance(toml_value, list):
        return ",".join(str(v) for v in toml_value)
    return ""


def _pick_bool(cli_value: str, toml_value) -> str:
    if cli_value:
        return cli_value.lower()
    if isinstance(toml_value, bool):
        return "true" if toml_value else "false"
    return "false"


if __name__ == "__main__":
    sys.exit(main())
