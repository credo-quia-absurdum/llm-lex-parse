#!/usr/bin/env python3
"""Parser for subC."""

from __future__ import annotations

import sys
from typing import List, Tuple

from lexer import Token, tokenize

# 1: program -> ext_def_list
# 2: ext_def_list -> ext_def_list ext_def
# 3: ext_def_list ->
# 4: ext_def -> func_decl compound_stmt
# 5: func_decl -> type_specifier pointers ID '(' ')'
# 6: type_specifier -> TYPE
# 7: pointers ->
# 8: compound_stmt -> '{' def_list stmt_list '}'
# 9: def_list -> def_list def
# 10: def_list ->
# 11: def -> type_specifier pointers ID ';'
# 12: stmt_list -> stmt_list stmt
# 13: stmt_list ->
# 14: stmt -> expr ';'
# 15: expr -> unary '=' expr
# 16: expr -> binary
# 17: binary -> unary
# 18: unary -> ID
# 19: unary -> INTEGER_CONST

GRAMMAR = [
    None,  # 0
    ("program", ["ext_def_list"]),  # 1
    ("ext_def_list", ["ext_def_list", "ext_def"]),  # 2
    ("ext_def_list", []),  # 3
    ("ext_def", ["func_decl", "compound_stmt"]),  # 4
    ("func_decl", ["type_specifier", "pointers", "ID", "'('", "')'"]),  # 5
    ("type_specifier", ["TYPE"]),  # 6
    ("pointers", []),  # 7
    ("compound_stmt", ["'{'", "def_list", "stmt_list", "'}'"]),  # 8
    ("def_list", ["def_list", "def"]),  # 9
    ("def_list", []),  # 10
    ("def", ["type_specifier", "pointers", "ID", "';'"]),  # 11
    ("stmt_list", ["stmt_list", "stmt"]),  # 12
    ("stmt_list", []),  # 13
    ("stmt", ["expr", "';'"]),  # 14
    ("expr", ["unary", "'='", "expr"]),  # 15
    ("expr", ["binary"]),  # 16
    ("binary", ["unary"]),  # 17
    ("unary", ["ID"]),  # 18
    ("unary", ["INTEGER_CONST"]),  # 19
]

ACTION = {
    0: {"TYPE": "s2", "$": "r3"},
    1: {"$": "acc"},
    2: {"ID": "r7"},
    3: {"ID": "s6"},
    4: {"TYPE": "s2", "$": "r2"},
    5: {"'{'": "s8"},
    6: {"'('": "s9"},
    7: {"ID": "r6"},
    8: {"TYPE": "s15", "ID": "s24", "INTEGER_CONST": "s25", "'}'": "r10"},
    9: {"')'": "s11"},
    10: {"ID": "s24", "INTEGER_CONST": "s25", "'}'": "r13"},
    11: {"'{'": "r5"},
    12: {"TYPE": "s2", "$": "r4"},
    13: {"'}'": "s26"},
    14: {"TYPE": "s15", "ID": "s24", "INTEGER_CONST": "s25", "'}'": "r9"},
    15: {"ID": "r7"},
    16: {"ID": "s20"},
    17: {"';'": "s27"},
    18: {"';'": "r16"},
    19: {"';'": "r17"},
    20: {"';'": "s21"},
    21: {"TYPE": "s15", "ID": "s24", "INTEGER_CONST": "s25", "'}'": "r11"},
    22: {"'='": "s28", "';'": "r18"},
    23: {"';'": "r19"},
    24: {"'='": "r18", "';'": "r18"},
    25: {"'='": "r19", "';'": "r19"},
    26: {"TYPE": "s2", "$": "r8"},
    27: {"ID": "s24", "INTEGER_CONST": "s25", "'}'": "r12"},
    28: {"ID": "s24", "INTEGER_CONST": "s25"},
    29: {"';'": "r15"},
}

GOTO = {
    0: {"ext_def_list": 1, "ext_def": 4, "func_decl": 5, "type_specifier": 7},
    2: {"pointers": 3},
    4: {"ext_def": 12},
    8: {"def_list": 13, "def": 14, "type_specifier": 19, "stmt_list": 10, "stmt": 27, "expr": 17, "binary": 18, "unary": 22},
    10: {"stmt": 27, "expr": 17, "binary": 18, "unary": 22},
    14: {"def": 14},
    15: {"pointers": 16},
    17: {"expr": 29},
    19: {"pointers": 16},
    21: {"type_specifier": 19, "unary": 22, "binary": 18, "expr": 17, "stmt": 27},
    28: {"expr": 29, "binary": 18, "unary": 22},
}


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <source-file>", file=sys.stderr)
        return 1

    try:
        with open(argv[1], "r", encoding="utf-8") as handle:
            source = handle.read()
    except OSError as exc:
        print(f"Could not read input file: {exc}", file=sys.stderr)
        return 1

    tokens = list(tokenize(source))
    tokens.append(Token("$", "$", -1, -1))  # End of input token
    
    stack: List[Tuple[int, str]] = [(0, "")]
    token_idx = 0

    while True:
        state = stack[-1][0]
        token = tokens[token_idx]
        action = ACTION.get(state, {}).get(token.kind)

        if token.kind in ["(", ")", "{", "}", ";", ",", "="]:
            action = ACTION.get(state, {}).get(f"'{token.kind}'")

        if action is None:
            print(f"SyntaxError: Unexpected token {token.lexeme} in state {state}", file=sys.stderr)
            return 1

        if action.startswith("s"):
            # Shift
            new_state = int(action[1:])
            stack.append((new_state, token.lexeme))
            token_idx += 1
        elif action.startswith("r"):
            # Reduce
            rule_num = int(action[1:])
            lhs, rhs = GRAMMAR[rule_num]
            
            if rhs:
                stack = stack[: -len(rhs)]
            
            print(f"{lhs}->{' '.join(rhs) if rhs else 'epsilon'}")

            state = stack[-1][0]
            goto_state = GOTO.get(state, {}).get(lhs)
            if goto_state is None:
                print(f"Error: No GOTO for state {state} and non-terminal {lhs}", file=sys.stderr)
                return 1
            stack.append((goto_state, lhs))
        elif action == "acc":
            print("program->ext_def_list")
            return 0
        else:
            print(f"Unknown action: {action}", file=sys.stderr)
            return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
