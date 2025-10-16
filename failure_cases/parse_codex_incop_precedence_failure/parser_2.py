#!/usr/bin/env python3
"""Iteration 2: table-driven LALR(1) parser for the subC language."""

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple


def _ensure_project_root() -> None:
    project_root = Path(__file__).resolve().parents[2]
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


_ensure_project_root()

from llm_parse.exp_codex.lexer import Token as LexToken  # pylint: disable=wrong-import-position
from llm_parse.exp_codex.lexer import tokenize  # pylint: disable=wrong-import-position


END_SYMBOL = "$"
EPSILON = object()


def _quoted(char: str) -> str:
    return f"'{char}'"


KEYWORD_SYMBOL_MAP: Dict[str, str] = {
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

MULTI_CHAR_OPERATOR_SYMBOL: Dict[str, str] = {
    "->": "STRUCTOP",
    "++": "INCOP",
    "--": "DECOP",
    "<=": "RELOP",
    ">=": "RELOP",
    "==": "EQUOP",
    "!=": "EQUOP",
    "&&": "LOGICAL_AND",
    "||": "LOGICAL_OR",
}

SINGLE_CHAR_OPERATOR_SYMBOL: Dict[str, str] = {
    "(": _quoted("("),
    ")": _quoted(")"),
    "{": _quoted("{"),
    "}": _quoted("}"),
    "[": _quoted("["),
    "]": _quoted("]"),
    ",": _quoted(","),
    ";": _quoted(";"),
    "=": _quoted("="),
    "+": _quoted("+"),
    "-": _quoted("-"),
    "*": _quoted("*"),
    "/": _quoted("/"),
    "%": _quoted("%"),
    "!": _quoted("!"),
    ".": _quoted("."),
    "&": _quoted("&"),
}

RELOP_SIGNS = {"<", ">"}


@dataclass(frozen=True)
class ParserToken:
    symbol: str
    lexeme: str
    line: int
    column: int


@dataclass(frozen=True)
class Production:
    index: int
    lhs: str
    rhs: Tuple[str, ...]
    precedence_symbol: Optional[str]


@dataclass(frozen=True)
class LR1Item:
    production: int
    position: int
    lookahead: str


class ParserError(Exception):
    """Raised when parsing fails due to a syntax or internal error."""


PRODUCTION_SPECS: List[Tuple[str, Tuple[str, ...], Optional[str]]] = [
    ("program'", ("program",), None),
    ("program", ("ext_def_list",), None),
    ("ext_def_list", ("ext_def_list", "ext_def"), None),
    ("ext_def_list", tuple(), None),
    ("ext_def", ("type_specifier", "pointers", "ID", _quoted(";")), None),
    ("ext_def", ("type_specifier", "pointers", "ID", _quoted("["), "INTEGER_CONST", _quoted("]"), _quoted(";")), None),
    ("ext_def", ("struct_specifier", _quoted(";")), None),
    ("ext_def", ("func_decl", "compound_stmt"), None),
    ("type_specifier", ("TYPE",), None),
    ("type_specifier", ("VOID",), None),
    ("type_specifier", ("struct_specifier",), None),
    ("struct_specifier", ("STRUCT", "ID", _quoted("{"), "def_list", _quoted("}")), None),
    ("struct_specifier", ("STRUCT", "ID"), None),
    ("func_decl", ("type_specifier", "pointers", "ID", _quoted("("), _quoted(")")), None),
    ("func_decl", ("type_specifier", "pointers", "ID", _quoted("("), "VOID", _quoted(")")), None),
    ("func_decl", ("type_specifier", "pointers", "ID", _quoted("("), "param_list", _quoted(")")), None),
    ("pointers", (_quoted("*"),), None),
    ("pointers", tuple(), None),
    ("param_list", ("param_decl",), None),
    ("param_list", ("param_list", _quoted(","), "param_decl"), None),
    ("param_decl", ("type_specifier", "pointers", "ID"), None),
    ("param_decl", ("type_specifier", "pointers", "ID", _quoted("["), "INTEGER_CONST", _quoted("]")), None),
    ("def_list", ("def_list", "def"), None),
    ("def_list", tuple(), None),
    ("def", ("type_specifier", "pointers", "ID", _quoted(";")), None),
    ("def", ("type_specifier", "pointers", "ID", _quoted("["), "INTEGER_CONST", _quoted("]"), _quoted(";")), None),
    ("compound_stmt", (_quoted("{"), "def_list", "stmt_list", _quoted("}")), None),
    ("stmt_list", ("stmt_list", "stmt"), None),
    ("stmt_list", tuple(), None),
    ("stmt", ("expr", _quoted(";")), None),
    ("stmt", ("compound_stmt",), None),
    ("stmt", ("RETURN", _quoted(";")), None),
    ("stmt", ("RETURN", "expr", _quoted(";")), None),
    ("stmt", (_quoted(";"),), None),
    ("stmt", ("IF", _quoted("("), "expr", _quoted(")"), "stmt"), None),
    ("stmt", ("IF", _quoted("("), "expr", _quoted(")"), "stmt", "ELSE", "stmt"), None),
    ("stmt", ("WHILE", _quoted("("), "expr", _quoted(")"), "stmt"), None),
    ("stmt", ("FOR", _quoted("("), "expr_e", _quoted(";"), "expr_e", _quoted(";"), "expr_e", _quoted(")"), "stmt"), None),
    ("stmt", ("BREAK", _quoted(";")), None),
    ("stmt", ("CONTINUE", _quoted(";")), None),
    ("expr_e", ("expr",), None),
    ("expr_e", tuple(), None),
    ("expr", ("unary", _quoted("="), "expr"), None),
    ("expr", ("binary",), None),
    ("binary", ("binary", "RELOP", "binary"), None),
    ("binary", ("binary", "EQUOP", "binary"), None),
    ("binary", ("binary", _quoted("+"), "binary"), None),
    ("binary", ("binary", _quoted("-"), "binary"), None),
    ("binary", ("binary", _quoted("*"), "binary"), None),
    ("binary", ("binary", _quoted("/"), "binary"), None),
    ("binary", ("binary", _quoted("%"), "binary"), None),
    ("binary", ("unary",), _quoted("=")),
    ("binary", ("binary", "LOGICAL_AND", "binary"), None),
    ("binary", ("binary", "LOGICAL_OR", "binary"), None),
    ("unary", (_quoted("("), "expr", _quoted(")")), None),
    ("unary", ("INTEGER_CONST",), None),
    ("unary", ("CHAR_CONST",), None),
    ("unary", ("STRING",), None),
    ("unary", ("ID",), None),
    ("unary", (_quoted("-"), "unary"), _quoted("!")),
    ("unary", (_quoted("!"), "unary"), None),
    ("unary", ("unary", "INCOP"), None),
    ("unary", ("unary", "DECOP"), None),
    ("unary", ("INCOP", "unary"), None),
    ("unary", ("DECOP", "unary"), None),
    ("unary", (_quoted("&"), "unary"), None),
    ("unary", (_quoted("*"), "unary"), _quoted("!")),
    ("unary", ("unary", _quoted("["), "expr", _quoted("]")), None),
    ("unary", ("unary", _quoted("."), "ID"), None),
    ("unary", ("unary", "STRUCTOP", "ID"), None),
    ("unary", ("unary", _quoted("("), "args", _quoted(")")), None),
    ("unary", ("unary", _quoted("("), _quoted(")")), None),
    ("unary", ("SYM_NULL",), None),
    ("args", ("expr",), None),
    ("args", ("args", _quoted(","), "expr"), None),
]


PRECEDENCE: Dict[str, Tuple[int, str]] = {
    "INCOP": (1, "left"),
    "DECOP": (1, "left"),
    _quoted("("): (1, "left"),
    _quoted(")"): (1, "left"),
    _quoted("["): (1, "left"),
    _quoted("]"): (1, "left"),
    _quoted("."): (1, "left"),
    "STRUCTOP": (1, "left"),
    _quoted("!"): (2, "right"),
    _quoted("&"): (2, "right"),
    _quoted("*"): (3, "left"),
    _quoted("/"): (3, "left"),
    _quoted("%"): (3, "left"),
    _quoted("+"): (4, "left"),
    _quoted("-"): (4, "left"),
    "RELOP": (5, "left"),
    "EQUOP": (6, "left"),
    "LOGICAL_AND": (7, "left"),
    "LOGICAL_OR": (8, "left"),
    _quoted("="): (9, "right"),
    _quoted(","): (10, "left"),
}


PRODUCTIONS: List[Production] = [
    Production(index=i, lhs=lhs, rhs=rhs, precedence_symbol=prec)
    for i, (lhs, rhs, prec) in enumerate(PRODUCTION_SPECS)
]

NONTERMINALS: Set[str] = {prod.lhs for prod in PRODUCTIONS}

PRODUCTIONS_BY_LHS: Dict[str, List[int]] = defaultdict(list)
for production in PRODUCTIONS:
    PRODUCTIONS_BY_LHS[production.lhs].append(production.index)

FIRST_SETS: Dict[str, Set[str]] = {}
PRODUCTION_PRECEDENCE: Dict[int, Optional[Tuple[int, str]]] = {}


def is_nonterminal(symbol: str) -> bool:
    return symbol in NONTERMINALS


def compute_first_sets() -> Dict[str, Set[str]]:
    first: Dict[str, Set[str]] = {nt: set() for nt in NONTERMINALS}
    changed = True
    while changed:
        changed = False
        for production in PRODUCTIONS:
            if not production.rhs:
                if EPSILON not in first[production.lhs]:
                    first[production.lhs].add(EPSILON)  # type: ignore[arg-type]
                    changed = True
                continue
            nullable_prefix = True
            for symbol in production.rhs:
                if is_nonterminal(symbol):
                    sym_first = first[symbol]
                    for terminal in sym_first:
                        if terminal is EPSILON:
                            continue
                        if terminal not in first[production.lhs]:
                            first[production.lhs].add(terminal)
                            changed = True
                    if EPSILON not in sym_first:
                        nullable_prefix = False
                        break
                else:
                    if symbol not in first[production.lhs]:
                        first[production.lhs].add(symbol)
                        changed = True
                    nullable_prefix = False
                    break
            if nullable_prefix:
                if EPSILON not in first[production.lhs]:
                    first[production.lhs].add(EPSILON)  # type: ignore[arg-type]
                    changed = True
    return first


def first_sequence(symbols: Tuple[str, ...], lookahead: str) -> Set[str]:
    if not symbols:
        return {lookahead}
    result: Set[str] = set()
    for symbol in symbols:
        if is_nonterminal(symbol):
            sym_first = FIRST_SETS[symbol]
            result.update(terminal for terminal in sym_first if terminal is not EPSILON)
            if EPSILON not in sym_first:
                return result
        else:
            result.add(symbol)
            return result
    result.add(lookahead)
    return result


def closure(items: Iterable[LR1Item]) -> frozenset:
    closure_set = set(items)
    queue = list(items)
    while queue:
        item = queue.pop()
        production = PRODUCTIONS[item.production]
        if item.position >= len(production.rhs):
            continue
        next_symbol = production.rhs[item.position]
        if not is_nonterminal(next_symbol):
            continue
        beta = production.rhs[item.position + 1 :]
        lookahead_symbols = first_sequence(beta, item.lookahead)
        for prod_index in PRODUCTIONS_BY_LHS[next_symbol]:
            for la in lookahead_symbols:
                new_item = LR1Item(prod_index, 0, la)
                if new_item not in closure_set:
                    closure_set.add(new_item)
                    queue.append(new_item)
    return frozenset(closure_set)


def goto(items: frozenset, symbol: str) -> frozenset:
    shifted = [
        LR1Item(item.production, item.position + 1, item.lookahead)
        for item in items
        if item.position < len(PRODUCTIONS[item.production].rhs)
        and PRODUCTIONS[item.production].rhs[item.position] == symbol
    ]
    if not shifted:
        return frozenset()
    return closure(shifted)


def build_canonical_collection() -> Tuple[List[frozenset], Dict[Tuple[int, str], int]]:
    start_item = closure({LR1Item(0, 0, END_SYMBOL)})
    states: List[frozenset] = [start_item]
    transitions: Dict[Tuple[int, str], int] = {}
    state_index: Dict[frozenset, int] = {start_item: 0}
    queue: List[frozenset] = [start_item]

    while queue:
        state = queue.pop(0)
        state_id = state_index[state]
        symbols: Set[str] = set()
        for item in state:
            production = PRODUCTIONS[item.production]
            if item.position < len(production.rhs):
                symbols.add(production.rhs[item.position])
        for symbol in symbols:
            target = goto(state, symbol)
            if not target:
                continue
            if target not in state_index:
                state_index[target] = len(states)
                states.append(target)
                queue.append(target)
            transitions[(state_id, symbol)] = state_index[target]
    return states, transitions


def merge_to_lalr(
    states: List[frozenset], transitions: Dict[Tuple[int, str], int]
) -> Tuple[List[frozenset], Dict[Tuple[int, str], int]]:
    core_to_items: Dict[Tuple[Tuple[int, int], ...], Dict[Tuple[int, int], Set[str]]] = {}
    core_order: List[Tuple[Tuple[int, int], ...]] = []

    for state in states:
        core = tuple(sorted((item.production, item.position) for item in state))
        if core not in core_to_items:
            core_to_items[core] = {}
            core_order.append(core)
        lookahead_map = core_to_items[core]
        for item in state:
            key = (item.production, item.position)
            lookahead_map.setdefault(key, set()).add(item.lookahead)

    merged_states: List[frozenset] = []
    core_to_index: Dict[Tuple[Tuple[int, int], ...], int] = {}
    for core in core_order:
        lookahead_map = core_to_items[core]
        merged_items = []
        for (prod, pos), lookaheads in lookahead_map.items():
            for lookahead in sorted(lookaheads):
                merged_items.append(LR1Item(prod, pos, lookahead))
        state_items = frozenset(merged_items)
        core_to_index[core] = len(merged_states)
        merged_states.append(state_items)

    old_to_new: Dict[int, int] = {}
    for idx, state in enumerate(states):
        core = tuple(sorted((item.production, item.position) for item in state))
        old_to_new[idx] = core_to_index[core]

    merged_transitions: Dict[Tuple[int, str], int] = {}
    for (old_state, symbol), target_state in transitions.items():
        merged_transitions[(old_to_new[old_state], symbol)] = old_to_new[target_state]

    return merged_states, merged_transitions


def compute_production_precedence() -> Dict[int, Optional[Tuple[int, str]]]:
    result: Dict[int, Optional[Tuple[int, str]]] = {}
    for production in PRODUCTIONS:
        symbol = production.precedence_symbol
        if symbol is None:
            for candidate in reversed(production.rhs):
                if is_nonterminal(candidate):
                    continue
                if candidate in PRECEDENCE:
                    symbol = candidate
                    break
        result[production.index] = PRECEDENCE.get(symbol) if symbol is not None else None
    return result


def resolve_shift_reduce(
    terminal: str,
    shift_action: Tuple[str, int],
    reduce_action: Tuple[str, int],
) -> Tuple[str, int]:
    reduce_prod = reduce_action[1]
    token_prec = PRECEDENCE.get(terminal)
    prod_prec = PRODUCTION_PRECEDENCE.get(reduce_prod)

    if token_prec is None and prod_prec is None:
        if terminal == "ELSE":
            return shift_action
        raise ParserError(f"Shift/reduce conflict with no precedence for terminal {terminal}")

    if token_prec is None:
        return reduce_action
    if prod_prec is None:
        return shift_action

    token_level, assoc = token_prec
    prod_level, _ = prod_prec
    if token_level < prod_level:
        return shift_action
    if token_level > prod_level:
        return reduce_action
    if assoc == "left":
        return reduce_action
    if assoc == "right":
        return shift_action
    raise ParserError(f"Non-associative conflict on terminal {terminal}")


def build_action_goto_tables(
    states: List[frozenset], transitions: Dict[Tuple[int, str], int]
) -> Tuple[Dict[int, Dict[str, Tuple[str, int]]], Dict[int, Dict[str, int]]]:
    action_table: Dict[int, Dict[str, Tuple[str, int]]] = defaultdict(dict)
    goto_table: Dict[int, Dict[str, int]] = defaultdict(dict)

    for state_index, state in enumerate(states):
        for item in state:
            production = PRODUCTIONS[item.production]
            if item.position < len(production.rhs):
                symbol = production.rhs[item.position]
                target = transitions.get((state_index, symbol))
                if target is None:
                    continue
                if is_nonterminal(symbol):
                    goto_table[state_index][symbol] = target
                else:
                    existing = action_table[state_index].get(symbol)
                    new_action = ("shift", target)
                    if existing is None:
                        action_table[state_index][symbol] = new_action
                    elif existing[0] == "shift":
                        if existing != new_action:
                            raise ParserError(f"Shift/shift conflict on state {state_index} symbol {symbol}")
                    elif existing[0] == "reduce":
                        action_table[state_index][symbol] = resolve_shift_reduce(symbol, new_action, existing)
                    else:
                        raise ParserError("Unexpected parser action kind")
            else:
                if production.lhs == "program'" and item.lookahead == END_SYMBOL:
                    action_table[state_index][END_SYMBOL] = ("accept", -1)
                    continue
                existing = action_table[state_index].get(item.lookahead)
                new_action = ("reduce", production.index)
                if existing is None:
                    action_table[state_index][item.lookahead] = new_action
                elif existing[0] == "shift":
                    action_table[state_index][item.lookahead] = resolve_shift_reduce(item.lookahead, existing, new_action)
                elif existing == new_action:
                    continue
                else:
                    raise ParserError(
                        f"Reduce/reduce conflict in state {state_index} on lookahead {item.lookahead}"
                    )

    return dict(action_table), dict(goto_table)


def build_parser_tables() -> Tuple[Dict[int, Dict[str, Tuple[str, int]]], Dict[int, Dict[str, int]]]:
    global FIRST_SETS, PRODUCTION_PRECEDENCE
    FIRST_SETS = compute_first_sets()
    PRODUCTION_PRECEDENCE = compute_production_precedence()
    canonical_states, canonical_transitions = build_canonical_collection()
    lalr_states, lalr_transitions = merge_to_lalr(canonical_states, canonical_transitions)
    return build_action_goto_tables(lalr_states, lalr_transitions)


ACTION_TABLE, GOTO_TABLE = build_parser_tables()


def lex_to_parser_symbol(token: LexToken) -> ParserToken:
    if token.kind == "KEY":
        symbol = KEYWORD_SYMBOL_MAP.get(token.lexeme)
        if symbol is None:
            raise ParserError(f"Unsupported keyword '{token.lexeme}' at line {token.line}, column {token.column}")
        return ParserToken(symbol, token.lexeme, token.line, token.column)
    if token.kind == "ID":
        return ParserToken("ID", token.lexeme, token.line, token.column)
    if token.kind == "INT":
        return ParserToken("INTEGER_CONST", token.lexeme, token.line, token.column)
    if token.kind == "F":
        raise ParserError(f"Float constants are not supported at line {token.line}, column {token.column}")
    if token.kind == "OP":
        lexeme = token.lexeme
        if lexeme in MULTI_CHAR_OPERATOR_SYMBOL:
            return ParserToken(MULTI_CHAR_OPERATOR_SYMBOL[lexeme], lexeme, token.line, token.column)
        if lexeme in RELOP_SIGNS:
            return ParserToken("RELOP", lexeme, token.line, token.column)
        symbol = SINGLE_CHAR_OPERATOR_SYMBOL.get(lexeme)
        if symbol is None:
            raise ParserError(f"Unrecognized operator '{lexeme}' at line {token.line}, column {token.column}")
        return ParserToken(symbol, lexeme, token.line, token.column)
    raise ParserError(f"Unsupported token kind '{token.kind}' at line {token.line}, column {token.column}")


def tokenize_source(path: Path) -> List[ParserToken]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ParserError(f"Could not read input file '{path}': {exc}") from exc

    tokens = [lex_to_parser_symbol(token) for token in tokenize(source)]
    if tokens:
        last = tokens[-1]
        end_line = last.line
        end_column = last.column + len(last.lexeme)
    else:
        end_line = 1
        end_column = 1
    tokens.append(ParserToken(END_SYMBOL, "<eof>", end_line, end_column))
    return tokens


def parse(tokens: Sequence[ParserToken]) -> List[str]:
    stack: List[int] = [0]
    output: List[str] = []
    index = 0

    while True:
        state = stack[-1]
        lookahead = tokens[index]
        action = ACTION_TABLE.get(state, {}).get(lookahead.symbol)
        if action is None:
            expected = sorted(ACTION_TABLE.get(state, {}).keys())
            expected_desc = ", ".join(expected) if expected else "end of input"
            raise ParserError(
                f"SyntaxError: expected {expected_desc} before {lookahead.lexeme!r} at line {lookahead.line}, column {lookahead.column}"
            )
        kind, value = action
        if kind == "shift":
            stack.append(value)
            index += 1
        elif kind == "reduce":
            production = PRODUCTIONS[value]
            rhs_len = len(production.rhs)
            for _ in range(rhs_len):
                stack.pop()
            goto_state = GOTO_TABLE.get(stack[-1], {}).get(production.lhs)
            if goto_state is None:
                raise ParserError(f"Internal parser error: missing goto for symbol {production.lhs}")
            stack.append(goto_state)
            rhs_text = "epsilon" if rhs_len == 0 else " ".join(production.rhs)
            output.append(f"{production.lhs}->{rhs_text}")
        elif kind == "accept":
            return output
        else:  # pragma: no cover - defensive
            raise ParserError(f"Unknown parser action {kind}")


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <source-file>", file=sys.stderr)
        return 1
    input_path = Path(argv[1])
    try:
        tokens = tokenize_source(input_path)
        reductions = parse(tokens)
    except ParserError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for line in reductions:
        print(line)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv))
