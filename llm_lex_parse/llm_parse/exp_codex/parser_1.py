#!/usr/bin/env python3
"""Iteration 1 parser for the subC grammar using a table-driven LR(1) strategy."""

from __future__ import annotations

from dataclasses import dataclass
import pathlib
import sys
from typing import Dict, Iterable, Iterator, List, Mapping, MutableMapping, Sequence, Set, Tuple

try:
    from . import lexer  # type: ignore
except ImportError:  # pragma: no cover - fallback for script execution
    sys.path.append(str(pathlib.Path(__file__).resolve().parent))
    import lexer  # type: ignore


Token = lexer.Token
LexerError = lexer.LexerError

EPSILON = "epsilon"
EOF_SYMBOL = "EOF"
START_SYMBOL = "program'"


@dataclass(frozen=True)
class Production:
    index: int
    lhs: str
    rhs: Tuple[str, ...]


@dataclass(frozen=True)
class Item:
    production_index: int
    dot: int
    lookahead: str

    def next_symbol(self, productions: Sequence[Production]) -> str | None:
        production = productions[self.production_index]
        if self.dot < len(production.rhs):
            return production.rhs[self.dot]
        return None


RAW_PRODUCTIONS: List[Tuple[str, Tuple[str, ...]]] = [
    ("program", ("ext_def_list",)),
    ("ext_def_list", ("ext_def_list", "ext_def")),
    ("ext_def_list", ()),
    (
        "ext_def",
        ("type_specifier", "pointers", "ID", ";"),
    ),
    (
        "ext_def",
        ("type_specifier", "pointers", "ID", "[", "INTEGER_CONST", "]", ";"),
    ),
    ("ext_def", ("struct_specifier", ";")),
    ("ext_def", ("func_decl", "compound_stmt")),
    ("type_specifier", ("TYPE",)),
    ("type_specifier", ("VOID",)),
    ("type_specifier", ("struct_specifier",)),
    ("struct_specifier", ("STRUCT", "ID", "{", "def_list", "}",)),
    ("struct_specifier", ("STRUCT", "ID")),
    ("func_decl", ("type_specifier", "pointers", "ID", "(", ")",)),
    ("func_decl", ("type_specifier", "pointers", "ID", "(", "VOID", ")",)),
    ("func_decl", ("type_specifier", "pointers", "ID", "(", "param_list", ")",)),
    ("pointers", ("*",)),
    ("pointers", ()),
    ("param_list", ("param_decl",)),
    ("param_list", ("param_list", ",", "param_decl")),
    ("param_decl", ("type_specifier", "pointers", "ID")),
    ("param_decl", ("type_specifier", "pointers", "ID", "[", "INTEGER_CONST", "]")),
    ("def_list", ("def_list", "def")),
    ("def_list", ()),
    ("def", ("type_specifier", "pointers", "ID", ";")),
    ("def", ("type_specifier", "pointers", "ID", "[", "INTEGER_CONST", "]", ";")),
    ("compound_stmt", ("{", "def_list", "stmt_list", "}")),
    ("stmt_list", ("stmt_list", "stmt")),
    ("stmt_list", ()),
    ("stmt", ("expr", ";")),
    ("stmt", ("compound_stmt",)),
    ("stmt", ("RETURN", ";")),
    ("stmt", ("RETURN", "expr", ";")),
    ("stmt", (";",)),
    ("stmt", ("IF", "(", "expr", ")", "stmt")),
    ("stmt", ("IF", "(", "expr", ")", "stmt", "ELSE", "stmt")),
    ("stmt", ("WHILE", "(", "expr", ")", "stmt")),
    ("stmt", ("FOR", "(", "expr_e", ";", "expr_e", ";", "expr_e", ")", "stmt")),
    ("stmt", ("BREAK", ";")),
    ("stmt", ("CONTINUE", ";")),
    ("expr_e", ("expr",)),
    ("expr_e", ()),
    ("expr", ("unary", "=", "expr")),
    ("expr", ("binary",)),
    ("binary", ("binary", "RELOP", "binary")),
    ("binary", ("binary", "EQUOP", "binary")),
    ("binary", ("binary", "+", "binary")),
    ("binary", ("binary", "-", "binary")),
    ("binary", ("binary", "*", "binary")),
    ("binary", ("binary", "/", "binary")),
    ("binary", ("binary", "%", "binary")),
    ("binary", ("unary",)),
    ("binary", ("binary", "LOGICAL_AND", "binary")),
    ("binary", ("binary", "LOGICAL_OR", "binary")),
    ("unary", ("(", "expr", ")")),
    ("unary", ("INTEGER_CONST",)),
    ("unary", ("CHAR_CONST",)),
    ("unary", ("STRING",)),
    ("unary", ("ID",)),
    ("unary", ("-", "unary")),
    ("unary", ("!", "unary")),
    ("unary", ("unary", "INCOP")),
    ("unary", ("unary", "DECOP")),
    ("unary", ("INCOP", "unary")),
    ("unary", ("DECOP", "unary")),
    ("unary", ("&", "unary")),
    ("unary", ("*", "unary")),
    ("unary", ("unary", "[", "expr", "]")),
    ("unary", ("unary", ".", "ID")),
    ("unary", ("unary", "STRUCTOP", "ID")),
    ("unary", ("unary", "(", "args", ")")),
    ("unary", ("unary", "(", ")",)),
    ("unary", ("SYM_NULL",)),
    ("args", ("expr",)),
    ("args", ("args", ",", "expr")),
]


def _build_productions() -> List[Production]:
    productions: List[Production] = []
    productions.append(Production(0, START_SYMBOL, ("program",)))
    for lhs, rhs in RAW_PRODUCTIONS:
        productions.append(Production(len(productions), lhs, rhs))
    return productions


PRODUCTIONS: List[Production] = _build_productions()
NONTERMINALS: Set[str] = {production.lhs for production in PRODUCTIONS}
SYMBOLS_BY_LHS: Dict[str, List[int]] = {}
for production in PRODUCTIONS:
    SYMBOLS_BY_LHS.setdefault(production.lhs, []).append(production.index)

TERMINALS: Set[str] = {EOF_SYMBOL}
for production in PRODUCTIONS:
    for symbol in production.rhs:
        if symbol not in NONTERMINALS:
            TERMINALS.add(symbol)

ALL_SYMBOLS: Tuple[str, ...] = tuple(sorted(TERMINALS | NONTERMINALS))

TERMINAL_PRECEDENCE: Dict[str, Tuple[int, str]] = {
    "INCOP": (10, "left"),
    "DECOP": (10, "left"),
    "STRUCTOP": (10, "left"),
    "[": (10, "left"),
    "(": (10, "left"),
    ".": (10, "left"),
    "*": (8, "left"),
    "/": (8, "left"),
    "%": (8, "left"),
    "+": (7, "left"),
    "-": (7, "left"),
    "RELOP": (6, "left"),
    "EQUOP": (5, "left"),
    "LOGICAL_AND": (4, "left"),
    "LOGICAL_OR": (3, "left"),
    "=": (2, "right"),
    ",": (1, "left"),
    "!": (9, "right"),
    "&": (9, "right"),
}

PRODUCTION_PRECEDENCE_OVERRIDE: Dict[int, Tuple[int, str]] = {
    59: (9, "right"),  # unary -> '-' unary
    60: (9, "right"),  # unary -> '!' unary
    63: (9, "right"),  # unary -> INCOP unary
    64: (9, "right"),  # unary -> DECOP unary
    65: (9, "right"),  # unary -> '&' unary
    66: (9, "right"),  # unary -> '*' unary
}

PRODUCTION_PRECEDENCE: Dict[int, Tuple[int, str]] = {}
for production in PRODUCTIONS:
    precedence = PRODUCTION_PRECEDENCE_OVERRIDE.get(production.index)
    if precedence is None:
        for symbol in reversed(production.rhs):
            if symbol in TERMINAL_PRECEDENCE:
                precedence = TERMINAL_PRECEDENCE[symbol]
                break
    if precedence is not None:
        PRODUCTION_PRECEDENCE[production.index] = precedence


def _compute_first_sets() -> Dict[str, Set[str]]:
    first: Dict[str, Set[str]] = {symbol: set() for symbol in NONTERMINALS | TERMINALS}
    for terminal in TERMINALS:
        first[terminal].add(terminal)

    changed = True
    while changed:
        changed = False
        for production in PRODUCTIONS:
            lhs = production.lhs
            rhs = production.rhs
            if not rhs:
                if EPSILON not in first[lhs]:
                    first[lhs].add(EPSILON)
                    changed = True
                continue

            nullable_prefix = True
            for symbol in rhs:
                before = len(first[lhs])
                first[lhs].update(first[symbol] - {EPSILON})
                if len(first[lhs]) != before:
                    changed = True

                if EPSILON in first[symbol]:
                    continue
                nullable_prefix = False
                break

            if nullable_prefix:
                if EPSILON not in first[lhs]:
                    first[lhs].add(EPSILON)
                    changed = True

    return first


FIRST_SETS: Mapping[str, Set[str]] = _compute_first_sets()


def _first_sequence(symbols: Tuple[str, ...], lookahead: str) -> Set[str]:
    if not symbols:
        return {lookahead}

    result: Set[str] = set()
    nullable_prefix = True
    for symbol in symbols:
        symbol_first = FIRST_SETS[symbol]
        result.update(symbol_first - {EPSILON})
        if EPSILON in symbol_first:
            continue
        nullable_prefix = False
        break

    if nullable_prefix:
        result.add(lookahead)
    return result


def _closure(items: Iterable[Item]) -> frozenset[Item]:
    closure_set: Set[Item] = set(items)
    queue = list(items)

    while queue:
        item = queue.pop()
        next_symbol = item.next_symbol(PRODUCTIONS)
        if next_symbol is None or next_symbol not in NONTERMINALS:
            continue

        production = PRODUCTIONS[item.production_index]
        beta = production.rhs[item.dot + 1 :]
        lookahead_set = _first_sequence(beta, item.lookahead)

        for production_index in SYMBOLS_BY_LHS[next_symbol]:
            for lookahead in lookahead_set:
                new_item = Item(production_index, 0, lookahead)
                if new_item not in closure_set:
                    closure_set.add(new_item)
                    queue.append(new_item)

    return frozenset(closure_set)


def _goto(items: Iterable[Item], symbol: str) -> frozenset[Item]:
    moved: List[Item] = []
    for item in items:
        next_symbol = item.next_symbol(PRODUCTIONS)
        if next_symbol == symbol:
            moved.append(Item(item.production_index, item.dot + 1, item.lookahead))
    if not moved:
        return frozenset()
    return _closure(moved)


def _build_lr1_automaton() -> Tuple[List[frozenset[Item]], List[Dict[str, int]]]:
    start_item = Item(0, 0, EOF_SYMBOL)
    initial_state = _closure([start_item])

    states: List[frozenset[Item]] = [initial_state]
    transitions: List[Dict[str, int]] = [{}]
    state_index: Dict[frozenset[Item], int] = {initial_state: 0}

    for index, state in enumerate(states):
        transitions[index] = {}
        for symbol in ALL_SYMBOLS:
            next_state = _goto(state, symbol)
            if not next_state:
                continue
            if next_state not in state_index:
                state_index[next_state] = len(states)
                states.append(next_state)
                transitions.append({})
            transitions[index][symbol] = state_index[next_state]

    return states, transitions


STATES, TRANSITIONS = _build_lr1_automaton()


class ParserConstructionError(RuntimeError):
    pass


def _register_action(
    table: MutableMapping[int, Dict[str, Tuple[str, int | None]]],
    state: int,
    symbol: str,
    entry: Tuple[str, int | None],
) -> None:
    existing = table.setdefault(state, {}).get(symbol)
    if existing is not None and existing != entry:
        actions = {existing[0], entry[0]}
        if actions == {"shift", "reduce"}:
            shift_entry = entry if entry[0] == "shift" else existing
            reduce_entry = existing if existing[0] == "reduce" else entry
            token_prec = TERMINAL_PRECEDENCE.get(symbol)
            production_prec = (
                PRODUCTION_PRECEDENCE.get(reduce_entry[1]) if reduce_entry[1] is not None else None
            )

            if token_prec is not None and production_prec is not None:
                if token_prec[0] > production_prec[0]:
                    table[state][symbol] = shift_entry
                    return
                if token_prec[0] < production_prec[0]:
                    table[state][symbol] = reduce_entry
                    return
                # Equal precedence: use associativity.
                associativity = token_prec[1]
                if associativity == "left":
                    table[state][symbol] = reduce_entry
                    return
                if associativity == "right":
                    table[state][symbol] = shift_entry
                    return

            prefer_shift = {"INCOP", "DECOP", "STRUCTOP", "[", "(", ".", "ELSE"}
            if symbol in prefer_shift:
                table[state][symbol] = shift_entry
                return

        raise ParserConstructionError(
            f"Conflict at state {state} on symbol {symbol}: {existing} vs {entry}"
        )
    table[state][symbol] = entry


def _build_tables() -> Tuple[Dict[int, Dict[str, Tuple[str, int | None]]], Dict[int, Dict[str, int]]]:
    action: Dict[int, Dict[str, Tuple[str, int | None]]] = {}
    goto_table: Dict[int, Dict[str, int]] = {}

    for state_index, items in enumerate(STATES):
        goto_table[state_index] = {}
        for item in items:
            next_symbol = item.next_symbol(PRODUCTIONS)
            if next_symbol is None:
                production = PRODUCTIONS[item.production_index]
                if production.lhs == START_SYMBOL and item.lookahead == EOF_SYMBOL:
                    _register_action(action, state_index, EOF_SYMBOL, ("accept", None))
                else:
                    _register_action(
                        action, state_index, item.lookahead, ("reduce", item.production_index)
                    )
                continue

            if next_symbol in TERMINALS:
                target_state = TRANSITIONS[state_index].get(next_symbol)
                if target_state is None:
                    continue
                _register_action(action, state_index, next_symbol, ("shift", target_state))
            else:
                target_state = TRANSITIONS[state_index].get(next_symbol)
                if target_state is not None:
                    goto_table[state_index][next_symbol] = target_state

    return action, goto_table


ACTION_TABLE, GOTO_TABLE = _build_tables()


def _format_symbol(symbol: str) -> str:
    if symbol in NONTERMINALS:
        return symbol
    if symbol and symbol[0].isalpha():
        return symbol
    return f"'{symbol}'"


def _format_reduction(production: Production) -> str:
    if not production.rhs:
        return f"{production.lhs}->epsilon"
    rhs_text = " ".join(_format_symbol(symbol) for symbol in production.rhs)
    return f"{production.lhs}->{rhs_text}"


class ParseError(RuntimeError):
    def __init__(self, message: str, token: Token):
        super().__init__(message)
        self.token = token


def _expected_symbols(state: int) -> List[str]:
    entries = ACTION_TABLE.get(state, {})
    formatted = sorted(_format_symbol(symbol) for symbol in entries)
    return formatted


def parse(tokens: Sequence[Token]) -> None:
    stack: List[int] = [0]
    index = 0
    output = sys.stdout

    while True:
        state = stack[-1]
        token = tokens[index]
        action_entry = ACTION_TABLE.get(state, {}).get(token.kind)

        if action_entry is None:
            expected = _expected_symbols(state)
            expected_text = ", ".join(expected) if expected else "EOF"
            lexeme = token.lexeme or token.kind
            message = (
                f"SyntaxError: expected {expected_text} before {lexeme} "
                f"at line {token.line}, column {token.column}"
            )
            raise ParseError(message, token)

        action, value = action_entry

        if action == "shift":
            assert isinstance(value, int)
            stack.append(value)
            index += 1
            continue

        if action == "reduce":
            assert isinstance(value, int)
            production = PRODUCTIONS[value]
            print(_format_reduction(production), file=output)

            rhs_length = len(production.rhs)
            for _ in range(rhs_length):
                stack.pop()

            goto_state = GOTO_TABLE.get(stack[-1], {}).get(production.lhs)
            if goto_state is None:
                raise ParseError(
                    f"No GOTO transition for state {stack[-1]} on {production.lhs}",
                    token,
                )
            stack.append(goto_state)
            continue

        if action == "accept":
            return

        raise ParserConstructionError(f"Unknown parser action '{action}'")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <source-file>", file=sys.stderr)
        return 1

    try:
        tokens = lexer.lex_file(argv[1])
    except OSError as exc:
        print(f"Could not read input file: {exc}", file=sys.stderr)
        return 1
    except LexerError as exc:
        print(f"LexerError: {exc}", file=sys.stderr)
        return 2

    try:
        parse(tokens)
    except ParseError as exc:
        print(str(exc), file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    sys.exit(main(sys.argv))
