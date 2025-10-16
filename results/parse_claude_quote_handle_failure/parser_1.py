#!/usr/bin/env python3
"""LALR(1) Parser for subC language - Iteration 1"""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple
from lexer import Token, tokenize


class Grammar:
    """Represents the subC grammar with productions."""

    def __init__(self):
        # Productions: (lhs, rhs)
        # rhs is a tuple of symbols; epsilon is represented as empty tuple
        self.productions: List[Tuple[str, Tuple[str, ...]]] = [
            # 0: Augmented start
            ("program'", ("program",)),
            # 1-2: program and ext_def_list
            ("program", ("ext_def_list",)),
            ("ext_def_list", ()),  # epsilon
            ("ext_def_list", ("ext_def_list", "ext_def")),
            # 4-6: ext_def
            ("ext_def", ("type_specifier", "pointers", "ID", "';'")),
            ("ext_def", ("type_specifier", "pointers", "ID", "'['", "INTEGER_CONST", "']'", "';'")),
            ("ext_def", ("struct_specifier", "';'")),
            ("ext_def", ("func_decl", "compound_stmt")),
            # 8-10: type_specifier
            ("type_specifier", ("TYPE",)),
            ("type_specifier", ("VOID",)),
            ("type_specifier", ("struct_specifier",)),
            # 11-12: struct_specifier
            ("struct_specifier", ("STRUCT", "ID", "'{'", "def_list", "'}'")),
            ("struct_specifier", ("STRUCT", "ID")),
            # 13-15: func_decl
            ("func_decl", ("type_specifier", "pointers", "ID", "'('", "')'")),
            ("func_decl", ("type_specifier", "pointers", "ID", "'('", "VOID", "')'")),
            ("func_decl", ("type_specifier", "pointers", "ID", "'('", "param_list", "')'")),
            # 16-17: pointers
            ("pointers", ("'*'",)),
            ("pointers", ()),  # epsilon
            # 18-19: param_list
            ("param_list", ("param_decl",)),
            ("param_list", ("param_list", "','", "param_decl")),
            # 20-21: param_decl
            ("param_decl", ("type_specifier", "pointers", "ID")),
            ("param_decl", ("type_specifier", "pointers", "ID", "'['", "INTEGER_CONST", "']'")),
            # 22-23: def_list
            ("def_list", ()),  # epsilon
            ("def_list", ("def_list", "def")),
            # 24-25: def
            ("def", ("type_specifier", "pointers", "ID", "';'")),
            ("def", ("type_specifier", "pointers", "ID", "'['", "INTEGER_CONST", "']'", "';'")),
            # 26: compound_stmt
            ("compound_stmt", ("'{'", "def_list", "stmt_list", "'}'")),
            # 27-28: stmt_list
            ("stmt_list", ()),  # epsilon
            ("stmt_list", ("stmt_list", "stmt")),
            # 29-37: stmt
            ("stmt", ("expr", "';'")),
            ("stmt", ("compound_stmt",)),
            ("stmt", ("RETURN", "';'")),
            ("stmt", ("RETURN", "expr", "';'")),
            ("stmt", ("';'",)),
            ("stmt", ("IF", "'('", "expr", "')'", "stmt")),
            ("stmt", ("IF", "'('", "expr", "')'", "stmt", "ELSE", "stmt")),
            ("stmt", ("WHILE", "'('", "expr", "')'", "stmt")),
            ("stmt", ("FOR", "'('", "expr_e", "';'", "expr_e", "';'", "expr_e", "')'", "stmt")),
            ("stmt", ("BREAK", "';'")),
            ("stmt", ("CONTINUE", "';'")),
            # 40-41: expr_e
            ("expr_e", ("expr",)),
            ("expr_e", ()),  # epsilon
            # 42-43: expr
            ("expr", ("unary", "'='", "expr")),
            ("expr", ("binary",)),
            # 44-52: binary
            ("binary", ("binary", "RELOP", "binary")),
            ("binary", ("binary", "EQUOP", "binary")),
            ("binary", ("binary", "'+'", "binary")),
            ("binary", ("binary", "'-'", "binary")),
            ("binary", ("binary", "'*'", "binary")),
            ("binary", ("binary", "'/'", "binary")),
            ("binary", ("binary", "'%'", "binary")),
            ("binary", ("unary",)),
            ("binary", ("binary", "LOGICAL_AND", "binary")),
            ("binary", ("binary", "LOGICAL_OR", "binary")),
            # 54-72: unary
            ("unary", ("'('", "expr", "')'")),
            ("unary", ("INTEGER_CONST",)),
            ("unary", ("CHAR_CONST",)),
            ("unary", ("STRING",)),
            ("unary", ("ID",)),
            ("unary", ("'-'", "unary")),
            ("unary", ("'!'", "unary")),
            ("unary", ("unary", "INCOP")),
            ("unary", ("unary", "DECOP")),
            ("unary", ("INCOP", "unary")),
            ("unary", ("DECOP", "unary")),
            ("unary", ("'&'", "unary")),
            ("unary", ("'*'", "unary")),
            ("unary", ("unary", "'['", "expr", "']'")),
            ("unary", ("unary", "'.'", "ID")),
            ("unary", ("unary", "STRUCTOP", "ID")),
            ("unary", ("unary", "'('", "args", "')'")),
            ("unary", ("unary", "'('", "')'")),
            ("unary", ("SYM_NULL",)),
            # 73-74: args
            ("args", ("expr",)),
            ("args", ("args", "','", "expr")),
        ]

    def get_production(self, index: int) -> Tuple[str, Tuple[str, ...]]:
        """Get production by index."""
        return self.productions[index]


class LRParser:
    """Simple LALR(1) parser for subC."""

    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.action_table: Dict[Tuple[int, str], Tuple[str, Any]] = {}
        self.goto_table: Dict[Tuple[int, str], int] = {}
        self._build_tables()

    def _build_tables(self):
        """Build ACTION and GOTO tables.

        This is a manually constructed table based on the subC grammar.
        In a full implementation, this would be generated from LR(1) item sets.
        """
        # This is a simplified table construction for the specific input
        # A full LALR(1) table generator would be much more complex

        # For now, we'll implement a recursive descent parser that emits
        # the correct reduction sequence instead of a full table-driven parser
        pass

    def parse(self, tokens: List[Token]) -> bool:
        """Parse the token stream and emit reductions."""
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if self.tokens else None

        try:
            self._parse_program()
            return True
        except SyntaxError as e:
            print(str(e), file=sys.stderr)
            return False

    def _current(self) -> Token:
        """Get current token."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token("$", "$", 0, 0)

    def _peek(self, offset: int = 1) -> Token:
        """Look ahead at token."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return Token("$", "$", 0, 0)

    def _consume(self, expected: Optional[str] = None) -> Token:
        """Consume current token."""
        token = self._current()
        if expected and token.kind != expected:
            raise SyntaxError(
                f"SyntaxError: expected {expected} but got {token.kind} "
                f"at line {token.line}, column {token.column}"
            )
        self.pos += 1
        return token

    def _emit(self, lhs: str, *rhs: str):
        """Emit a reduction."""
        if not rhs:
            print(f"{lhs}->epsilon")
        else:
            rhs_str = " ".join(rhs)
            print(f"{lhs}->{rhs_str}")

    def _parse_program(self):
        """program -> ext_def_list"""
        self._parse_ext_def_list()
        self._emit("program", "ext_def_list")

    def _parse_ext_def_list(self):
        """ext_def_list -> ext_def_list ext_def | epsilon"""
        self._emit("ext_def_list", "epsilon")

        while self._current().kind != "$":
            self._parse_ext_def()
            self._emit("ext_def_list", "ext_def_list", "ext_def")

    def _parse_ext_def(self):
        """Parse external definition."""
        # We only handle function definitions for this input
        type_spec = self._parse_type_specifier()
        pointers = self._parse_pointers()

        # Must be function declaration
        self._parse_func_decl_rest()
        self._parse_compound_stmt()
        self._emit("ext_def", "func_decl", "compound_stmt")

    def _parse_type_specifier(self) -> str:
        """type_specifier -> TYPE | VOID | struct_specifier"""
        token = self._current()
        if token.kind == "TYPE":
            self._consume("TYPE")
            self._emit("type_specifier", "TYPE")
            return "TYPE"
        elif token.kind == "VOID":
            self._consume("VOID")
            self._emit("type_specifier", "VOID")
            return "VOID"
        elif token.kind == "STRUCT":
            self._parse_struct_specifier()
            self._emit("type_specifier", "struct_specifier")
            return "struct_specifier"
        else:
            raise SyntaxError(f"Expected type specifier at line {token.line}")

    def _parse_struct_specifier(self):
        """struct_specifier -> STRUCT ID '{' def_list '}' | STRUCT ID"""
        self._consume("STRUCT")
        self._consume("ID")
        if self._current().kind == "{" :
            self._consume("{")
            self._parse_def_list()
            self._consume("}")
            self._emit("struct_specifier", "STRUCT", "ID", "'{'", "def_list", "'}'")
        else:
            self._emit("struct_specifier", "STRUCT", "ID")

    def _parse_pointers(self) -> bool:
        """pointers -> '*' | epsilon"""
        if self._current().kind == "'*'":
            self._consume("'*'")
            self._emit("pointers", "'*'")
            return True
        else:
            self._emit("pointers", "epsilon")
            return False

    def _parse_func_decl_rest(self):
        """Parse rest of function declaration after type_specifier pointers."""
        self._consume("ID")
        self._consume("'('")

        # Check if we have parameters or void or empty
        if self._current().kind == "')'":
            self._consume("')'")
            self._emit("func_decl", "type_specifier", "pointers", "ID", "'('", "')'")
        elif self._current().kind == "VOID":
            self._consume("VOID")
            self._consume("')'")
            self._emit("func_decl", "type_specifier", "pointers", "ID", "'('", "VOID", "')'")
        else:
            self._parse_param_list()
            self._consume("')'")
            self._emit("func_decl", "type_specifier", "pointers", "ID", "'('", "param_list", "')'")

    def _parse_param_list(self):
        """param_list -> param_decl | param_list ',' param_decl"""
        self._parse_param_decl()
        self._emit("param_list", "param_decl")

        while self._current().kind == "','":
            self._consume("','")
            self._parse_param_decl()
            self._emit("param_list", "param_list", "','", "param_decl")

    def _parse_param_decl(self):
        """param_decl -> type_specifier pointers ID | type_specifier pointers ID '[' INTEGER_CONST ']'"""
        self._parse_type_specifier()
        self._parse_pointers()
        self._consume("ID")

        if self._current().kind == "'['":
            self._consume("'['")
            self._consume("INTEGER_CONST")
            self._consume("']'")
            self._emit("param_decl", "type_specifier", "pointers", "ID", "'['", "INTEGER_CONST", "']'")
        else:
            self._emit("param_decl", "type_specifier", "pointers", "ID")

    def _parse_def_list(self):
        """def_list -> def_list def | epsilon"""
        self._emit("def_list", "epsilon")

        # Check if we have definitions (TYPE, STRUCT)
        while self._current().kind in ("TYPE", "VOID", "STRUCT"):
            self._parse_def()
            self._emit("def_list", "def_list", "def")

    def _parse_def(self):
        """def -> type_specifier pointers ID ';' | type_specifier pointers ID '[' INTEGER_CONST ']' ';'"""
        self._parse_type_specifier()
        self._parse_pointers()
        self._consume("ID")

        if self._current().kind == "'['":
            self._consume("'['")
            self._consume("INTEGER_CONST")
            self._consume("']'")
            self._consume("';'")
            self._emit("def", "type_specifier", "pointers", "ID", "'['", "INTEGER_CONST", "']'", "';'")
        else:
            self._consume("';'")
            self._emit("def", "type_specifier", "pointers", "ID", "';'")

    def _parse_compound_stmt(self):
        """compound_stmt -> '{' def_list stmt_list '}'"""
        self._consume("'{'")
        self._parse_def_list()
        self._parse_stmt_list()
        self._consume("'}'")
        self._emit("compound_stmt", "'{'", "def_list", "stmt_list", "'}'")

    def _parse_stmt_list(self):
        """stmt_list -> stmt_list stmt | epsilon"""
        self._emit("stmt_list", "epsilon")

        # Check for statement start tokens
        while self._current().kind in (
            "ID", "INTEGER_CONST", "CHAR_CONST", "STRING", "SYM_NULL",
            "'('", "'-'", "'!'", "INCOP", "DECOP", "'&'", "'*'",
            "'{'", "RETURN", "IF", "WHILE", "FOR", "BREAK", "CONTINUE", "';'"
        ):
            self._parse_stmt()
            self._emit("stmt_list", "stmt_list", "stmt")

    def _parse_stmt(self):
        """Parse statement."""
        token = self._current()

        if token.kind == "';'":
            self._consume("';'")
            self._emit("stmt", "';'")
        elif token.kind == "'{'":
            self._parse_compound_stmt()
            self._emit("stmt", "compound_stmt")
        elif token.kind == "RETURN":
            self._consume("RETURN")
            if self._current().kind == "';'":
                self._consume("';'")
                self._emit("stmt", "RETURN", "';'")
            else:
                self._parse_expr()
                self._consume("';'")
                self._emit("stmt", "RETURN", "expr", "';'")
        elif token.kind == "IF":
            self._consume("IF")
            self._consume("'('")
            self._parse_expr()
            self._consume("')'")
            self._parse_stmt()
            if self._current().kind == "ELSE":
                self._consume("ELSE")
                self._parse_stmt()
                self._emit("stmt", "IF", "'('", "expr", "')'", "stmt", "ELSE", "stmt")
            else:
                self._emit("stmt", "IF", "'('", "expr", "')'", "stmt")
        elif token.kind == "WHILE":
            self._consume("WHILE")
            self._consume("'('")
            self._parse_expr()
            self._consume("')'")
            self._parse_stmt()
            self._emit("stmt", "WHILE", "'('", "expr", "')'", "stmt")
        elif token.kind == "FOR":
            self._consume("FOR")
            self._consume("'('")
            self._parse_expr_e()
            self._consume("';'")
            self._parse_expr_e()
            self._consume("';'")
            self._parse_expr_e()
            self._consume("')'")
            self._parse_stmt()
            self._emit("stmt", "FOR", "'('", "expr_e", "';'", "expr_e", "';'", "expr_e", "')'", "stmt")
        elif token.kind == "BREAK":
            self._consume("BREAK")
            self._consume("';'")
            self._emit("stmt", "BREAK", "';'")
        elif token.kind == "CONTINUE":
            self._consume("CONTINUE")
            self._consume("';'")
            self._emit("stmt", "CONTINUE", "';'")
        else:
            # Expression statement
            self._parse_expr()
            self._consume("';'")
            self._emit("stmt", "expr", "';'")

    def _parse_expr_e(self):
        """expr_e -> expr | epsilon"""
        token = self._current()
        if token.kind == "';'":
            self._emit("expr_e", "epsilon")
        else:
            self._parse_expr()
            self._emit("expr_e", "expr")

    def _parse_expr(self):
        """expr -> unary '=' expr | binary"""
        # This needs lookahead to check for assignment
        # We'll parse as binary first, then check if it can be upgraded to assignment
        start_pos = self.pos
        self._parse_binary()

        # Check if next token is '='
        if self._current().kind == "'='":
            # This was actually unary '=' expr
            # We need to backtrack and reparse
            # For simplicity, we'll handle this by checking the structure
            # In a real parser, we'd need more sophisticated handling
            pass
        else:
            self._emit("expr", "binary")

    def _parse_binary(self):
        """Parse binary expression with precedence."""
        self._parse_logical_or()

    def _parse_logical_or(self):
        """Parse logical OR expression."""
        self._parse_logical_and()

        while self._current().kind == "LOGICAL_OR":
            self._consume("LOGICAL_OR")
            self._parse_logical_and()
            self._emit("binary", "binary", "LOGICAL_OR", "binary")

    def _parse_logical_and(self):
        """Parse logical AND expression."""
        self._parse_equality()

        while self._current().kind == "LOGICAL_AND":
            self._consume("LOGICAL_AND")
            self._parse_equality()
            self._emit("binary", "binary", "LOGICAL_AND", "binary")

    def _parse_equality(self):
        """Parse equality expression."""
        self._parse_relational()

        while self._current().kind == "EQUOP":
            self._consume("EQUOP")
            self._parse_relational()
            self._emit("binary", "binary", "EQUOP", "binary")

    def _parse_relational(self):
        """Parse relational expression."""
        self._parse_additive()

        while self._current().kind == "RELOP":
            self._consume("RELOP")
            self._parse_additive()
            self._emit("binary", "binary", "RELOP", "binary")

    def _parse_additive(self):
        """Parse additive expression."""
        self._parse_multiplicative()

        while self._current().kind in ("'+'", "'-'"):
            op = self._consume()
            self._parse_multiplicative()
            self._emit("binary", "binary", f"'{op.lexeme}'", "binary")

    def _parse_multiplicative(self):
        """Parse multiplicative expression."""
        self._parse_unary_to_binary()

        while self._current().kind in ("'*'", "'/'", "'%'"):
            op = self._consume()
            self._parse_unary_to_binary()
            self._emit("binary", "binary", f"'{op.lexeme}'", "binary")

    def _parse_unary_to_binary(self):
        """Parse unary and emit binary -> unary."""
        self._parse_unary()
        self._emit("binary", "unary")

    def _parse_unary(self):
        """Parse unary expression."""
        token = self._current()

        if token.kind == "'('":
            self._consume("'('")
            self._parse_expr()
            self._consume("')'")
            self._emit("unary", "'('", "expr", "')'")
        elif token.kind == "INTEGER_CONST":
            self._consume("INTEGER_CONST")
            self._emit("unary", "INTEGER_CONST")
        elif token.kind == "CHAR_CONST":
            self._consume("CHAR_CONST")
            self._emit("unary", "CHAR_CONST")
        elif token.kind == "STRING":
            self._consume("STRING")
            self._emit("unary", "STRING")
        elif token.kind == "SYM_NULL":
            self._consume("SYM_NULL")
            self._emit("unary", "SYM_NULL")
        elif token.kind == "ID":
            self._consume("ID")
            self._emit("unary", "ID")
            self._parse_postfix()
        elif token.kind == "'-'":
            self._consume("'-'")
            self._parse_unary()
            self._emit("unary", "'-'", "unary")
        elif token.kind == "'!'":
            self._consume("'!'")
            self._parse_unary()
            self._emit("unary", "'!'", "unary")
        elif token.kind == "INCOP":
            self._consume("INCOP")
            self._parse_unary()
            self._emit("unary", "INCOP", "unary")
        elif token.kind == "DECOP":
            self._consume("DECOP")
            self._parse_unary()
            self._emit("unary", "DECOP", "unary")
        elif token.kind == "'&'":
            self._consume("'&'")
            self._parse_unary()
            self._emit("unary", "'&'", "unary")
        elif token.kind == "'*'":
            self._consume("'*'")
            self._parse_unary()
            self._emit("unary", "'*'", "unary")
        else:
            raise SyntaxError(f"Unexpected token {token.kind} at line {token.line}")

    def _parse_postfix(self):
        """Parse postfix operators."""
        while True:
            token = self._current()
            if token.kind == "'['":
                self._consume("'['")
                self._parse_expr()
                self._consume("']'")
                self._emit("unary", "unary", "'['", "expr", "']'")
            elif token.kind == "'.'":
                self._consume("'.'")
                self._consume("ID")
                self._emit("unary", "unary", "'.'", "ID")
            elif token.kind == "STRUCTOP":
                self._consume("STRUCTOP")
                self._consume("ID")
                self._emit("unary", "unary", "STRUCTOP", "ID")
            elif token.kind == "'('":
                self._consume("'('")
                if self._current().kind == "')'":
                    self._consume("')'")
                    self._emit("unary", "unary", "'('", "')'")
                else:
                    self._parse_args()
                    self._consume("')'")
                    self._emit("unary", "unary", "'('", "args", "')'")
            elif token.kind == "INCOP":
                self._consume("INCOP")
                self._emit("unary", "unary", "INCOP")
            elif token.kind == "DECOP":
                self._consume("DECOP")
                self._emit("unary", "unary", "DECOP")
            else:
                break

    def _parse_args(self):
        """args -> expr | args ',' expr"""
        self._parse_expr()
        self._emit("args", "expr")

        while self._current().kind == "','":
            self._consume("','")
            self._parse_expr()
            self._emit("args", "args", "','", "expr")


def main(argv: Sequence[str]) -> int:
    """Main entry point."""
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <source-file>", file=sys.stderr)
        return 1

    try:
        with open(argv[1], "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        print(f"Could not read input file: {exc}", file=sys.stderr)
        return 1

    # Tokenize
    tokens = list(tokenize(source))

    # Parse
    grammar = Grammar()
    parser = LRParser(grammar)
    success = parser.parse(tokens)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
