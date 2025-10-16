#!/usr/bin/env python3
"""Lexer for subC."""

from __future__ import annotations

import sys
from typing import Dict, Iterable, List, NamedTuple, Sequence


class Token(NamedTuple):
    kind: str
    lexeme: str
    line: int
    column: int


KEYWORDS = {
    "break": "BREAK",
    "char": "TYPE",
    "continue": "CONTINUE",
    "else": "ELSE",
    "float": "TYPE",
    "for": "FOR",
    "if": "IF",
    "int": "TYPE",
    "return": "RETURN",
    "struct": "STRUCT",
    "while": "WHILE",
    "void": "VOID",
    "NULL": "SYM_NULL",
}

OPERATORS = {
    "||": "LOGICAL_OR",
    "&&": "LOGICAL_AND",
    "<": "RELOP",
    "<=": "RELOP",
    ">": "RELOP",
    ">=": "RELOP",
    "==": "EQUOP",
    "!=": "EQUOP",
    "++": "INCOP",
    "--": "DECOP",
    "->": "STRUCTOP",
    "(": "(",
    ")": ")",
    "[": "[",
    "]": "]",
    "{": "{",
    "}": "}",
    ".": ".",
    ",": ",",
    "!": "!",
    "*": "*",
    "/": "/",
    "%": "%",
    "+": "+",
    "-": "-",
    "&": "&",
    "|": "|",
    ";": ";",
    "=": "=",
}


def is_letter(char: str) -> bool:
    return char.isalpha() or char == "_"


def is_digit(char: str) -> bool:
    return char.isdigit()


def tokenize(source: str) -> Iterable[Token]:
    position = 0
    length = len(source)
    line = 1
    line_start = 0

    while position < length:
        char = source[position]
        column = position - line_start + 1

        if char in " \t\r":
            position += 1
            continue

        if char == "\n":
            position += 1
            line += 1
            line_start = position
            continue

        if char == "/" and position + 1 < length and source[position + 1] == "*":
            position += 2
            depth = 1
            while position < length and depth > 0:
                if source[position] == "\n":
                    line += 1
                    line_start = position
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
                yield Token(KEYWORDS[lexeme], lexeme, line, column)
            else:
                yield Token("ID", lexeme, line, column)
            continue

        if is_digit(char):
            start = position
            while position < length and is_digit(source[position]):
                position += 1
            lexeme = source[start:position]
            yield Token("INTEGER_CONST", lexeme, line, column)
            continue

        if char == "'":
            start = position
            position += 1
            lexeme = ""
            if position < length:
                # if source[position] == '\\':
                #     position += 1
                #     if position < length:
                #         lexeme = "\\" + source[position]
                #         position += 1
                # else:
                lexeme = source[position]
                position += 1
            if position < length and source[position] == "'":
                position += 1
                yield Token("CHAR_CONST", "'" + lexeme + "'", line, column)
            else:
                # Unclosed char literal, treat as individual characters.
                position = start + 1
                yield Token(source[start], source[start], line, column)

            continue

        if char == '"':
            position += 1
            start = position
            while position < length and source[position] != '"':
                if source[position] == '\\':
                    position += 1
                position += 1
            lexeme = source[start:position]
            if position < length and source[position] == '"':
                position += 1
                yield Token("STRING", '"' + lexeme + '"', line, column)
            else:
                # Unclosed string literal
                position = start
            continue

        found_op = False
        for op_len in range(2, 0, -1):
            if position + op_len <= length:
                potential_op = source[position : position + op_len]
                if potential_op in OPERATORS:
                    yield Token(OPERATORS[potential_op], potential_op, line, column)
                    position += op_len
                    found_op = True
                    break
        if found_op:
            continue

        # Unrecognized character
        position += 1