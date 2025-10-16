#!/usr/bin/env python3
"""Iteration 1 lexer prototype for the subC language."""

from __future__ import annotations

import sys
from typing import Dict, Iterable, List, Sequence, Tuple


KEYWORDS = {
    "break",
    "char",
    "continue",
    "else",
    "float",
    "for",
    "if",
    "int",
    "return",
    "struct",
    "while",
    "NULL",
}

MULTI_CHAR_OPERATORS = {
    "->",
    "..",
    "++",
    "--",
    "<=",
    ">=",
    "==",
    "!=",
    "&&",
    "||",
}

SINGLE_CHAR_OPERATORS = {
    "(",
    ")",
    "[",
    "]",
    "{",
    "}",
    ".",
    ",",
    "!",
    "*",
    "/",
    "%",
    "+",
    "-",
    "<",
    ">",
    "&",
    "|",
    ";",
    "=",
}


def is_letter(char: str) -> bool:
    return char.isalpha() or char == "_"


def is_digit(char: str) -> bool:
    return char.isdigit()


def tokenize(source: str) -> Iterable[Tuple[str, ...]]:
    position = 0
    length = len(source)
    keyword_counts: Dict[str, int] = {}
    identifier_counts: Dict[str, int] = {}

    while position < length:
        char = source[position]

        # Skip whitespace, including newlines.
        if char in " \t\r\n":
            position += 1
            continue

        # Handle nested block comments.
        if char == "/" and position + 1 < length and source[position + 1] == "*":
            position += 2
            depth = 1
            while position < length and depth > 0:
                if (
                    source[position] == "/"
                    and position + 1 < length
                    and source[position + 1] == "*"
                ):
                    depth += 1
                    position += 2
                elif (
                    source[position] == "*"
                    and position + 1 < length
                    and source[position + 1] == "/"
                ):
                    depth -= 1
                    position += 2
                else:
                    position += 1
            continue

        # Keywords and identifiers.
        if is_letter(char):
            start = position
            position += 1
            while (
                position < length
                and (is_letter(source[position]) or is_digit(source[position]))
            ):
                position += 1
            lexeme = source[start:position]
            if lexeme in KEYWORDS:
                keyword_counts[lexeme] = keyword_counts.get(lexeme, 0) + 1
                yield ("KEY", lexeme, str(keyword_counts[lexeme]))
            else:
                identifier_counts[lexeme] = identifier_counts.get(lexeme, 0) + 1
                yield ("ID", lexeme, str(identifier_counts[lexeme]))
            continue

        # Numeric literals (integer or float constants).
        if is_digit(char):
            start = position
            while position < length and is_digit(source[position]):
                position += 1

            is_float = False
            if (
                position < length
                and source[position] == "."
                and not (
                    position + 1 < length and source[position + 1] == "."
                )
            ):
                is_float = True
                position += 1
                while position < length and is_digit(source[position]):
                    position += 1

                if position < length and source[position] in "eE":
                    lookahead = position + 1
                    if lookahead < length and source[lookahead] in "+-":
                        lookahead += 1
                    if lookahead < length and is_digit(source[lookahead]):
                        position = lookahead + 1
                        while position < length and is_digit(source[position]):
                            position += 1
                    else:
                        # Invalid exponent specifier: do not consume the exponent part.
                        position = position

            lexeme = source[start:position]
            if is_float:
                yield ("F", lexeme)
            else:
                yield ("INT", lexeme)
            continue

        # Multi-character operators.
        if position + 1 < length:
            potential = source[position : position + 2]
            if potential in MULTI_CHAR_OPERATORS:
                position += 2
                yield ("OP", potential)
                continue

        # Single-character operators.
        if char in SINGLE_CHAR_OPERATORS:
            position += 1
            yield ("OP", char)
            continue

        # If we reach this point, the character is unrecognized; skip it.
        position += 1


def emit(tokens: Iterable[Tuple[str, ...]]) -> None:
    for token in tokens:
        if token[0] in {"KEY", "ID"}:
            print("\t".join((token[0], token[1], token[2])))
        else:
            print("\t".join(token))


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <source-file>", file=sys.stderr)
        return 1

    try:
        with open(argv[1], "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        print(f"Could not read input file: {exc}", file=sys.stderr)
        return 1

    emit(tokenize(source))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
