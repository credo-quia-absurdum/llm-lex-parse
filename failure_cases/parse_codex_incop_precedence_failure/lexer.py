#!/usr/bin/env python3
"""Lexer for the subC language with reusable tokenize() API."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, Iterable, Iterator, Optional, Sequence


KEYWORDS = {
    "break",
    "char",
    "continue",
    "else",
    "float",
    "for",
    "if",
    "int",
    "void",
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


@dataclass(frozen=True)
class Token:
    """Single lexical token produced by the subC lexer."""

    kind: str
    lexeme: str
    line: int
    column: int
    aux: Optional[str] = None


def is_letter(char: str) -> bool:
    return char.isalpha() or char == "_"


def is_digit(char: str) -> bool:
    return char.isdigit()


def tokenize(source: str) -> Iterator[Token]:
    position = 0
    length = len(source)
    keyword_counts: Dict[str, int] = {}
    identifier_counts: Dict[str, int] = {}
    line = 1
    column = 1

    def advance_to(new_position: int) -> None:
        nonlocal position, line, column
        if new_position <= position:
            return
        segment = source[position:new_position]
        newline_count = segment.count("\n")
        if newline_count:
            line += newline_count
            column = len(segment.rsplit("\n", 1)[-1]) + 1
        else:
            column += len(segment)
        position = new_position

    while position < length:
        char = source[position]

        # Skip whitespace, including newlines.
        if char in " \t\r\n":
            advance_to(position + 1)
            continue

        # Handle nested block comments.
        if char == "/" and position + 1 < length and source[position + 1] == "*":
            advance_to(position + 2)
            depth = 1
            while position < length and depth > 0:
                ahead_two = source[position : position + 2]
                if ahead_two == "/*":
                    depth += 1
                    advance_to(position + 2)
                elif ahead_two == "*/":
                    depth -= 1
                    advance_to(position + 2)
                else:
                    advance_to(position + 1)
            continue

        # Keywords and identifiers.
        if is_letter(char):
            start = position
            start_line = line
            start_column = column
            advance_to(position + 1)
            while (
                position < length
                and (is_letter(source[position]) or is_digit(source[position]))
            ):
                advance_to(position + 1)
            lexeme = source[start:position]
            if lexeme in KEYWORDS:
                keyword_counts[lexeme] = keyword_counts.get(lexeme, 0) + 1
                yield Token("KEY", lexeme, start_line, start_column, str(keyword_counts[lexeme]))
            else:
                identifier_counts[lexeme] = identifier_counts.get(lexeme, 0) + 1
                yield Token("ID", lexeme, start_line, start_column, str(identifier_counts[lexeme]))
            continue

        # Numeric literals (integer or float constants).
        if is_digit(char):
            start = position
            start_line = line
            start_column = column
            while position < length and is_digit(source[position]):
                advance_to(position + 1)

            is_float = False
            if (
                position < length
                and source[position] == "."
                and not (
                    position + 1 < length and source[position + 1] == "."
                )
            ):
                is_float = True
                advance_to(position + 1)
                while position < length and is_digit(source[position]):
                    advance_to(position + 1)

                if position < length and source[position] in "eE":
                    lookahead = position + 1
                    if lookahead < length and source[lookahead] in "+-":
                        lookahead += 1
                    if lookahead < length and is_digit(source[lookahead]):
                        advance_to(lookahead + 1)
                        while position < length and is_digit(source[position]):
                            advance_to(position + 1)
                    else:
                        # Invalid exponent specifier: do not consume the exponent part.
                        pass

            lexeme = source[start:position]
            if is_float:
                yield Token("F", lexeme, start_line, start_column)
            else:
                yield Token("INT", lexeme, start_line, start_column)
            continue

        # Multi-character operators.
        if position + 1 < length:
            potential = source[position : position + 2]
            if potential in MULTI_CHAR_OPERATORS:
                start_line = line
                start_column = column
                advance_to(position + 2)
                yield Token("OP", potential, start_line, start_column)
                continue

        # Single-character operators.
        if char in SINGLE_CHAR_OPERATORS:
            start_line = line
            start_column = column
            advance_to(position + 1)
            yield Token("OP", char, start_line, start_column)
            continue

        # If we reach this point, the character is unrecognized; skip it.
        advance_to(position + 1)


def emit(tokens: Iterable[Token]) -> None:
    for token in tokens:
        if token.kind in {"KEY", "ID"} and token.aux is not None:
            print("\t".join((token.kind, token.lexeme, token.aux)))
        else:
            print("\t".join((token.kind, token.lexeme)))


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
