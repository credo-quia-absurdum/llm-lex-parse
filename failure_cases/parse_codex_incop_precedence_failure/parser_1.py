#!/usr/bin/env python3
"""Iteration 1: parser scaffold (token inspection only)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence


def _ensure_project_root() -> None:
    project_root = Path(__file__).resolve().parents[2]
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <source-file>", file=sys.stderr)
        return 1

    _ensure_project_root()
    try:
        from llm_parse.exp_codex.lexer import tokenize  # pylint: disable=import-error
    except ImportError as exc:  # pragma: no cover - defensive
        print(f"Failed to import shared lexer: {exc}", file=sys.stderr)
        return 1

    input_path = Path(argv[1])
    try:
        source = input_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Could not read input file '{input_path}': {exc}", file=sys.stderr)
        return 1

    tokens = list(tokenize(source))
    print(f"[iteration-1] collected {len(tokens)} tokens; parser not yet implemented", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
