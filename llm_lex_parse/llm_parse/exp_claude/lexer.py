#!/usr/bin/env python3
"""Enhanced lexer for the subC language with parser token support."""

from __future__ import annotations

import sys
from typing import Dict, Iterable, List, NamedTuple, Sequence


class Token(NamedTuple):
    """Represents a token with its type, lexeme, line, and column."""
    kind: str
    lexeme: str
    line: int = 1
    column: int = 1


# Token type mappings for parser
TYPE_KEYWORDS = {"int", "char"}
VOID_KEYWORD = "void"
STRUCT_KEYWORD = "struct"
NULL_KEYWORD = "NULL"

CONTROL_KEYWORDS = {
    "return": "RETURN",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "break": "BREAK",
    "continue": "CONTINUE",
}

# All keywords
ALL_KEYWORDS = (
    TYPE_KEYWORDS
    | {VOID_KEYWORD, STRUCT_KEYWORD, NULL_KEYWORD}
    | set(CONTROL_KEYWORDS.keys())
    | {"float"}  # Keep for backward compatibility
)

# Multi-character operators
MULTI_CHAR_OPERATORS = {
    "->": "STRUCTOP",
    "++": "INCOP",
    "--": "DECOP",
    "<=": "RELOP",
    ">=": "RELOP",
    "==": "EQUOP",
    "!=": "EQUOP",
    "&&": "LOGICAL_AND",
    "||": "LOGICAL_OR",
    "..": "..",  # Keep for backward compatibility
}

# Single-character operators and punctuation
SINGLE_CHAR_TOKENS = {
    "(": "(",
    ")": ")",
    "[": "[",
    "]": "]",
    "{": "{",
    "}": "}",
    ".": ".",
    ",": ",",
    ";": ";",
    "=": "=",
    "<": "RELOP",
    ">": "RELOP",
    "!": "!",
    "*": "*",
    "/": "/",
    "%": "%",
    "+": "+",
    "-": "-",
    "&": "&",
}


def is_letter(char: str) -> bool:
    """Check if character is a letter or underscore."""
    return char.isalpha() or char == "_"


def is_digit(char: str) -> bool:
    """Check if character is a digit."""
    return char.isdigit()


def tokenize(source: str) -> Iterable[Token]:
    """
    Tokenize the source code and yield Token objects.

    This function provides tokens suitable for parser consumption.
    """
    position = 0
    length = len(source)
    line = 1
    column = 1
    keyword_counts: Dict[str, int] = {}
    identifier_counts: Dict[str, int] = {}

    def advance(n: int = 1) -> None:
        """Advance position and track line/column."""
        nonlocal position, line, column
        for _ in range(n):
            if position < length and source[position] == "\n":
                line += 1
                column = 1
            else:
                column += 1
            position += 1

    while position < length:
        char = source[position]
        start_line = line
        start_column = column

        # Skip whitespace
        if char in " \t\r\n":
            advance()
            continue

        # Handle nested block comments
        if char == "/" and position + 1 < length and source[position + 1] == "*":
            advance(2)
            depth = 1
            while position < length and depth > 0:
                if (
                    source[position] == "/"
                    and position + 1 < length
                    and source[position + 1] == "*"
                ):
                    depth += 1
                    advance(2)
                elif (
                    source[position] == "*"
                    and position + 1 < length
                    and source[position + 1] == "/"
                ):
                    depth -= 1
                    advance(2)
                else:
                    advance()
            continue

        # String literals
        if char == '"':
            start = position
            advance()  # skip opening quote
            while position < length and source[position] != '"':
                if source[position] == "\\":
                    advance(2)  # skip escape sequence
                else:
                    advance()
            if position < length:
                advance()  # skip closing quote
            lexeme = source[start:position]
            yield Token("STRING", lexeme, start_line, start_column)
            continue

        # Character literals
        if char == "'":
            start = position
            advance()  # skip opening quote
            if position < length and source[position] == "\\":
                advance(2)  # escape sequence
            elif position < length:
                advance()  # single character
            if position < length and source[position] == "'":
                advance()  # skip closing quote
            lexeme = source[start:position]
            yield Token("CHAR_CONST", lexeme, start_line, start_column)
            continue

        # Keywords and identifiers
        if is_letter(char):
            start = position
            advance()
            while position < length and (is_letter(source[position]) or is_digit(source[position])):
                advance()
            lexeme = source[start:position]

            # Determine token type
            if lexeme in TYPE_KEYWORDS:
                keyword_counts[lexeme] = keyword_counts.get(lexeme, 0) + 1
                yield Token("TYPE", lexeme, start_line, start_column)
            elif lexeme == VOID_KEYWORD:
                keyword_counts[lexeme] = keyword_counts.get(lexeme, 0) + 1
                yield Token("VOID", lexeme, start_line, start_column)
            elif lexeme == STRUCT_KEYWORD:
                keyword_counts[lexeme] = keyword_counts.get(lexeme, 0) + 1
                yield Token("STRUCT", lexeme, start_line, start_column)
            elif lexeme == NULL_KEYWORD:
                keyword_counts[lexeme] = keyword_counts.get(lexeme, 0) + 1
                yield Token("SYM_NULL", lexeme, start_line, start_column)
            elif lexeme in CONTROL_KEYWORDS:
                keyword_counts[lexeme] = keyword_counts.get(lexeme, 0) + 1
                yield Token(CONTROL_KEYWORDS[lexeme], lexeme, start_line, start_column)
            elif lexeme in ALL_KEYWORDS:
                # Other keywords like "float"
                keyword_counts[lexeme] = keyword_counts.get(lexeme, 0) + 1
                yield Token("KEY", lexeme, start_line, start_column)
            else:
                identifier_counts[lexeme] = identifier_counts.get(lexeme, 0) + 1
                yield Token("ID", lexeme, start_line, start_column)
            continue

        # Numeric literals (integer constants)
        if is_digit(char):
            start = position
            while position < length and is_digit(source[position]):
                advance()

            # Check for float (but we only support integers in this parser)
            is_float = False
            if (
                position < length
                and source[position] == "."
                and not (position + 1 < length and source[position + 1] == ".")
            ):
                is_float = True
                advance()
                while position < length and is_digit(source[position]):
                    advance()

                if position < length and source[position] in "eE":
                    lookahead = position + 1
                    if lookahead < length and source[lookahead] in "+-":
                        lookahead += 1
                    if lookahead < length and is_digit(source[lookahead]):
                        position = lookahead
                        while position < length and is_digit(source[position]):
                            advance()

            lexeme = source[start:position]
            if is_float:
                yield Token("F", lexeme, start_line, start_column)
            else:
                yield Token("INTEGER_CONST", lexeme, start_line, start_column)
            continue

        # Multi-character operators
        if position + 1 < length:
            potential = source[position : position + 2]
            if potential in MULTI_CHAR_OPERATORS:
                token_type = MULTI_CHAR_OPERATORS[potential]
                advance(2)
                yield Token(token_type, potential, start_line, start_column)
                continue

        # Single-character tokens
        if char in SINGLE_CHAR_TOKENS:
            token_type = SINGLE_CHAR_TOKENS[char]
            advance()
            yield Token(token_type, char, start_line, start_column)
            continue

        # Unknown character - skip it
        advance()

    # Emit EOF token
    yield Token("$", "$", line, column)


def emit_legacy(tokens: Iterable[Token]) -> None:
    """
    Emit tokens in the legacy format (for backward compatibility).
    This is used when the lexer is run standalone.
    """
    for token in tokens:
        if token.kind == "$":
            break
        # Legacy output format
        if token.kind in {"KEY", "ID"}:
            print(f"{token.kind}\t{token.lexeme}\t{token.line}")
        else:
            print(f"{token.kind}\t{token.lexeme}")


def main(argv: Sequence[str]) -> int:
    """Main entry point for standalone lexer execution."""
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <source-file>", file=sys.stderr)
        return 1

    try:
        with open(argv[1], "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        print(f"Could not read input file: {exc}", file=sys.stderr)
        return 1

    emit_legacy(tokenize(source))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
