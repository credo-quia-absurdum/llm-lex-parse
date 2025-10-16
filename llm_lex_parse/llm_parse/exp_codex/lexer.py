#!/usr/bin/env python3
"""Experimental lexer for the subC language used by parser iterations.

This module mirrors the behaviour of ``llm_parse/lexer.py`` while extending the
token model so the parser can consume a structured token stream.  Tokens carry
their kind, original lexeme, and 1-based line/column locations.  The lexer
recognises the terminals required by ``parser_spec.md`` including logical
operators, structure member access, and character / string literals.
"""

from __future__ import annotations

from dataclasses import dataclass
import sys
from typing import Iterable, Iterator, List, Sequence


class LexerError(Exception):
    """Raised when the lexer encounters an invalid or unterminated token."""

    def __init__(self, message: str, line: int, column: int) -> None:
        super().__init__(message)
        self.line = line
        self.column = column

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{super().__str__()} at line {self.line}, column {self.column}"


@dataclass(frozen=True)
class Token:
    """SubC token with source location metadata."""

    kind: str
    lexeme: str
    line: int
    column: int

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            f"Token(kind={self.kind!r}, lexeme={self.lexeme!r}, "
            f"line={self.line}, column={self.column})"
        )


KEYWORD_KINDS = {
    "int": "TYPE",
    "char": "TYPE",
    "void": "VOID",
    "struct": "STRUCT",
    "return": "RETURN",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "break": "BREAK",
    "continue": "CONTINUE",
    "NULL": "SYM_NULL",
}

MULTI_CHAR_TOKENS = [
    ("->", "STRUCTOP"),
    ("++", "INCOP"),
    ("--", "DECOP"),
    ("<=", "RELOP"),
    (">=", "RELOP"),
    ("==", "EQUOP"),
    ("!=", "EQUOP"),
    ("&&", "LOGICAL_AND"),
    ("||", "LOGICAL_OR"),
    ("..", ".."),  # Retained for completeness; not referenced by the grammar.
]

SINGLE_CHAR_TOKEN_KINDS = {
    "(": "(",
    ")": ")",
    "[": "[",
    "]": "]",
    "{": "{",
    "}": "}",
    ",": ",",
    ";": ";",
    ".": ".",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "/",
    "%": "%",
    "=": "=",
    "<": "RELOP",
    ">": "RELOP",
    "!": "!",
    "&": "&",
    "|": "|",
}


class _Lexer:
    """Stateful scanner implementing ``tokenize``."""

    def __init__(self, source: str) -> None:
        self._source = source
        self._length = len(source)
        self._index = 0
        self._line = 1
        self._column = 1

    def _peek(self, offset: int = 0) -> str:
        position = self._index + offset
        if position >= self._length:
            return ""
        return self._source[position]

    def _advance(self) -> str:
        if self._index >= self._length:
            return ""

        ch = self._source[self._index]
        self._index += 1

        if ch == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1

        return ch

    def _consume_sequence(self, text: str) -> None:
        for expected in text:
            actual = self._advance()
            if actual != expected:
                raise AssertionError("consume_sequence used with mismatched text")

    def _skip_whitespace(self) -> None:
        while True:
            ch = self._peek()
            if ch in {" ", "\t", "\r", "\n"}:
                self._advance()
                continue

            # Block comments with nesting.
            if ch == "/" and self._peek(1) == "*":
                self._advance()
                self._advance()
                depth = 1
                while depth > 0:
                    if self._index >= self._length:
                        raise LexerError("Unterminated block comment", self._line, self._column)
                    if self._peek() == "/" and self._peek(1) == "*":
                        self._advance()
                        self._advance()
                        depth += 1
                    elif self._peek() == "*" and self._peek(1) == "/":
                        self._advance()
                        self._advance()
                        depth -= 1
                    else:
                        self._advance()
                continue

            # Single line comments.
            if ch == "/" and self._peek(1) == "/":
                self._advance()
                self._advance()
                while self._peek() not in {"", "\n"}:
                    self._advance()
                continue

            break

    def _consume_identifier(self) -> Token:
        start_index = self._index
        start_line = self._line
        start_column = self._column

        self._advance()  # First character already known to be a letter/underscore.
        while True:
            ch = self._peek()
            if ch.isalnum() or ch == "_":
                self._advance()
                continue
            break

        lexeme = self._source[start_index:self._index]
        kind = KEYWORD_KINDS.get(lexeme, "ID")
        return Token(kind, lexeme, start_line, start_column)

    def _consume_number(self) -> Token:
        start_index = self._index
        start_line = self._line
        start_column = self._column

        def consume_digits() -> None:
            while self._peek().isdigit():
                self._advance()

        consume_digits()
        is_float = False

        if self._peek() == "." and self._peek(1) != ".":
            is_float = True
            self._advance()  # Consume '.'
            consume_digits()

        if is_float and self._peek() in {"e", "E"}:
            lookahead_index = self._index + 1
            sign = self._peek(1)
            if sign in {"+", "-"}:
                lookahead_index += 1
            if lookahead_index < self._length and self._source[lookahead_index].isdigit():
                self._advance()  # 'e' or 'E'
                if sign in {"+", "-"}:
                    self._advance()
                consume_digits()
            else:
                # Invalid exponent part; treat as integer/float without exponent.
                pass

        lexeme = self._source[start_index:self._index]
        kind = "FLOAT_CONST" if is_float else "INTEGER_CONST"
        return Token(kind, lexeme, start_line, start_column)

    def _consume_char(self) -> Token:
        start_index = self._index
        start_line = self._line
        start_column = self._column

        self._advance()  # Opening quote.
        ch = self._peek()
        if ch == "":
            raise LexerError("Unterminated character literal", start_line, start_column)
        if ch == "\n":
            raise LexerError("Newline in character literal", start_line, start_column)

        if ch == "\\":
            self._advance()
            if self._peek() == "":
                raise LexerError("Unterminated escape in character literal", start_line, start_column)
            self._advance()
        else:
            self._advance()

        if self._peek() != "'":
            raise LexerError("Invalid character literal", start_line, start_column)
        self._advance()  # Closing quote.

        lexeme = self._source[start_index:self._index]
        return Token("CHAR_CONST", lexeme, start_line, start_column)

    def _consume_string(self) -> Token:
        start_index = self._index
        start_line = self._line
        start_column = self._column

        self._advance()  # Opening quote.
        while True:
            ch = self._peek()
            if ch == "":
                raise LexerError("Unterminated string literal", start_line, start_column)
            if ch == "\n":
                raise LexerError("Newline in string literal", start_line, start_column)
            if ch == "\\":
                self._advance()
                if self._peek() == "":
                    raise LexerError("Unterminated escape in string literal", start_line, start_column)
                self._advance()
                continue
            if ch == '"':
                self._advance()
                break
            self._advance()

        lexeme = self._source[start_index:self._index]
        return Token("STRING", lexeme, start_line, start_column)

    def tokens(self) -> Iterator[Token]:
        while True:
            self._skip_whitespace()
            if self._index >= self._length:
                break

            ch = self._peek()
            start_line = self._line
            start_column = self._column

            if ch.isalpha() or ch == "_":
                yield self._consume_identifier()
                continue

            if ch.isdigit():
                yield self._consume_number()
                continue

            if ch == "'":
                yield self._consume_char()
                continue

            if ch == '"':
                yield self._consume_string()
                continue

            matched = False
            for lexeme, kind in MULTI_CHAR_TOKENS:
                if self._source.startswith(lexeme, self._index):
                    self._consume_sequence(lexeme)
                    yield Token(kind, lexeme, start_line, start_column)
                    matched = True
                    break
            if matched:
                continue

            if ch in SINGLE_CHAR_TOKEN_KINDS:
                kind = SINGLE_CHAR_TOKEN_KINDS[ch]
                lexeme = self._advance()
                yield Token(kind, lexeme, start_line, start_column)
                continue

            raise LexerError(f"Unexpected character {ch!r}", start_line, start_column)

        yield Token("EOF", "", self._line, self._column)


def tokenize(source: str) -> List[Token]:
    """Tokenise ``source`` and return the complete token stream."""
    return list(_Lexer(source).tokens())


def lex_file(path: str) -> List[Token]:
    """Convenience helper to tokenise a file path."""
    with open(path, "r", encoding="utf-8") as handle:
        return tokenize(handle.read())


def _emit(tokens: Iterable[Token]) -> None:
    """Debug helper: emit tokens with locations."""
    for token in tokens:
        location = f"{token.line}:{token.column}"
        print(f"{token.kind}\t{token.lexeme}\t{location}")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <source-file>", file=sys.stderr)
        return 1

    try:
        tokens = lex_file(argv[1])
    except OSError as exc:
        print(f"Could not read input file: {exc}", file=sys.stderr)
        return 1
    except LexerError as exc:
        print(f"LexerError: {exc}", file=sys.stderr)
        return 2

    _emit(tokens)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main(sys.argv))
