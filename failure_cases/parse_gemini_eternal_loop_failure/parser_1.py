#!/usr/bin/env python3
"""Parser for subC."""

from __future__ import annotations

import sys
from typing import List, Tuple

from lexer import Token, tokenize


# For this first iteration, we will use a simplified grammar
# and manually construct the parsing table.

# 1: program -> ext_def_list
# 2: ext_def_list -> ext_def_list ext_def
# 3: ext_def_list ->
# 4: ext_def -> func_decl compound_stmt
# 5: func_decl -> type_specifier pointers ID '(' ')'
# 6: type_specifier -> TYPE
# 7: pointers ->
# 8: compound_stmt -> '{' def_list stmt_list '}'
# 9: def_list ->
# 10: stmt_list ->

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
    ("def_list", []),  # 9
    ("stmt_list", []),  # 10
]

ACTION = {
    0: {"TYPE": "s2", "$": "r3"},
    1: {"$": "acc"},
    2: {"ID": "r7", "TYPE": "r7"},
    3: {"ID": "s6"},
    4: {"$": "r2"},
    5: {"'{'": "s8"},
    6: {"'('": "s9"},
    7: {"'{'": "r6"},
    8: {"'}'": "r9"},
    9: {"')'": "s11"},
    10: {"'}'": "r10"},
    11: {"'{'": "r5"},
    12: {"$": "r4"},
    13: {"$": "r8"},
}

GOTO = {
    0: {"ext_def_list": 1, "ext_def": 4, "func_decl": 5, "type_specifier": 7},
    2: {"pointers": 3},
    8: {"def_list": 10},
    10: {"stmt_list": 13},
    5: {"compound_stmt": 12},
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
        print(f"state: {state}, token: {token}", file=sys.stderr)
        action = ACTION.get(state, {}).get(token.kind)

        if token.kind in ["(", ")", "{", "}", ";", ","]:
            action = ACTION.get(state, {}).get(f"'{token.kind}'")

        if action is None:
            print(f"SyntaxError: Unexpected token {token.lexeme}", file=sys.stderr)
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