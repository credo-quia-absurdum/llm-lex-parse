# Python Parser for subC

## 1. Goal

Build a Python-based bottom-up LALR(1) parser for the `subC` language. The parser reads a `subC` translation unit, consumes the token stream produced according to `llm_parse/lexer_spec.md`, and verifies that the program conforms to the grammar reproduced in Section 2. On success, the parser must emit the exact sequence of production reductions that recognizes the input; on failure, it must report the first syntax error with actionable diagnostics.

## 2. Grammar

### 2.1 Token Summary

The parser relies on the token kinds below. Literal punctuation tokens (parentheses, braces, brackets, comma, semicolon, assignment operator, arithmetic operators, logical negation, address-of, dereference, dot, and percent) are emitted by the lexer as their own one-character lexemes.

| Symbol Name   | Lexeme(s)                            | Notes                                    |
| ------------- | ------------------------------------ | ---------------------------------------- |
| `TYPE`        | `int`, `char`                        | Built-in arithmetic types                |
| `VOID`        | `void`                               | Function return type only                |
| `STRUCT`      | `struct`                             | Begins a struct declaration              |
| `SYM_NULL`    | `NULL`                               | Null pointer literal                     |
| `RETURN`      | `return`                             |                                          |
| `IF`          | `if`                                 |                                          |
| `ELSE`        | `else`                               |                                          |
| `WHILE`       | `while`                              |                                          |
| `FOR`         | `for`                                |                                          |
| `BREAK`       | `break`                              |                                          |
| `CONTINUE`    | `continue`                           |                                          |
| `INTEGER_CONST` | decimal integer literal            | No sign; lexer handles leading zeros     |
| `CHAR_CONST`  | character literal                    | Includes escape handling                 |
| `STRING`      | string literal                       | Double-quoted, C-style escapes           |
| `ID`          | identifier                           | Case-sensitive, excludes keywords        |
| `LOGICAL_OR`  | `||`                                 |                                          |
| `LOGICAL_AND` | `&&`                                 |                                          |
| `RELOP`       | `<`, `<=`, `>`, `>=`                 | Relational operators                     |
| `EQUOP`       | `==`, `!=`                           | Equality operators                       |
| `INCOP`       | `++`                                 | Pre- and postfix                         |
| `DECOP`       | `--`                                 | Pre- and postfix                         |
| `STRUCTOP`    | `->`                                 | Structure member access through pointer  |

### 2.2 Operator Precedence and Associativity

Expressions obey the precedence and associativity rules listed below (1 is the highest precedence). Operators appearing on the same row share the same precedence.

| Level | Operators                                        | Associativity | Notes                                           |
| ----- | ------------------------------------------------ | ------------- | ----------------------------------------------- |
| 1     | `()` call, `[]` subscript, `.` member, `STRUCTOP`, `INCOP` (postfix), `DECOP` (postfix) | Left          | Postfix operations                              |
| 2     | `INCOP` (prefix), `DECOP` (prefix), unary `-`, `!`, unary `*`, unary `&` | Right         | Prefix operators                                |
| 3     | `*`, `/`, `%`                                    | Left          | Multiplicative                                  |
| 4     | `+`, `-`                                         | Left          | Additive                                        |
| 5     | `RELOP`                                          | Left          | Relational comparisons                          |
| 6     | `EQUOP`                                          | Left          | Equality comparisons                            |
| 7     | `LOGICAL_AND`                                    | Left          | Logical AND                                     |
| 8     | `LOGICAL_OR`                                     | Left          | Logical OR                                      |
| 9     | `=`                                              | Right         | Assignment                                      |
| 10    | `,`                                              | Left          | Comma sequence                                  |

The dangling-`else` rule binds `else` to the nearest unmatched `if`. Respect the precedence assignments when constructing or reducing expressions.

### 2.4 subC vs. Standard C

subC intentionally limits several C features to keep the grammar manageable:

- No `typedef`.
- No `union`.
- No multi-dimensional arrays.
- No pointer-to-function types.
- No forward declarations.
- No `long`, `short`, `float`, `double`, `unsigned`, or `void` (outside function returns).
- Only `int` and `char` appear as built-in data types.
- Structure and function definitions are permitted only at global scope.
- Nested comments are allowed (handled lexically).
- No explicit type casts.
- Strong type checking is assumed but enforced outside the parser.

### 2.3 Productions

The grammar is the behavioural contract for the parser. `epsilon` denotes the empty production.

```
program               -> ext_def_list
ext_def_list          -> ext_def_list ext_def | epsilon
ext_def               -> type_specifier pointers ID ';'
                       | type_specifier pointers ID '[' INTEGER_CONST ']' ';'
                       | struct_specifier ';'
                       | func_decl compound_stmt
type_specifier        -> TYPE | VOID | struct_specifier
struct_specifier      -> STRUCT ID '{' def_list '}' | STRUCT ID
func_decl             -> type_specifier pointers ID '(' ')'
                       | type_specifier pointers ID '(' VOID ')'
                       | type_specifier pointers ID '(' param_list ')'
pointers              -> '*' | epsilon
param_list            -> param_decl | param_list ',' param_decl
param_decl            -> type_specifier pointers ID
                       | type_specifier pointers ID '[' INTEGER_CONST ']'
def_list              -> def_list def | epsilon
def                   -> type_specifier pointers ID ';'
                       | type_specifier pointers ID '[' INTEGER_CONST ']' ';'
compound_stmt         -> '{' def_list stmt_list '}'
stmt_list             -> stmt_list stmt | epsilon
stmt                  -> expr ';'
                       | compound_stmt
                       | RETURN ';'
                       | RETURN expr ';'
                       | ';'
                       | IF '(' expr ')' stmt
                       | IF '(' expr ')' stmt ELSE stmt
                       | WHILE '(' expr ')' stmt
                       | FOR '(' expr_e ';' expr_e ';' expr_e ')' stmt
                       | BREAK ';'
                       | CONTINUE ';'
expr_e                -> expr | epsilon
expr                  -> unary '=' expr
                       | binary
binary                -> binary RELOP binary
                       | binary EQUOP binary
                       | binary '+' binary
                       | binary '-' binary
                       | binary '*' binary
                       | binary '/' binary
                       | binary '%' binary
                       | unary
                       | binary LOGICAL_AND binary
                       | binary LOGICAL_OR binary
unary                 -> '(' expr ')'
                       | INTEGER_CONST
                       | CHAR_CONST
                       | STRING
                       | ID
                       | '-' unary
                       | '!' unary
                       | unary INCOP
                       | unary DECOP
                       | INCOP unary
                       | DECOP unary
                       | '&' unary
                       | '*' unary
                       | unary '[' expr ']'
                       | unary '.' ID
                       | unary STRUCTOP ID
                       | unary '(' args ')'
                       | unary '(' ')'
                       | SYM_NULL
args                  -> expr | args ',' expr
```

The Python implementation may internally refactor left-recursive productions (for example, `ext_def_list`, `def_list`, `stmt_list`, `binary`, and `args`) into iterative loops or right-recursive helpers to suit the chosen parsing strategy, but the accepted concrete syntax and the emitted reductions must match the grammar above.

## 3. Implementation Details

### 3.1 Command-Line Interface

- Invocation mirrors the lexer experiments: `python3 llm_parse/exp/parser_N.py llm_parse/input.txt`.
- Accept a single positional argument path to a `subC` source file. Read the entire file using UTF-8.
- Print reductions to `stdout`; direct diagnostics and syntax errors to `stderr` with a non-zero exit code.

### 3.2 Token Stream

- Refactor `llm_parse/lexer.py` during the first parser iteration so that it exposes a reusable `tokenize()` API (returning an iterable of tokens). Mirror that implementation under `llm_parse/exp/` for experiment tracking.
- The parser must import this shared lexer module instead of invoking a standalone CLI or relying on stdout capture.
- Ensure each token exposes at least `kind`, `lexeme`, and `line:column` metadata to support precise error messages.
- Preserve all tokens required by the grammar, including punctuation and keywords; the parser must not silently coerce unexpected lexemes.

### 3.3 Parsing Strategy

- Implement a table-driven LALR(1) parser. Augment the grammar with `program' -> program`, construct the canonical LR(1) item sets, merge compatible states, and derive ACTION/GOTO tables that the runtime uses to shift, reduce, or accept.
- Generate parsing tables ahead of time (either as static Python dictionaries checked into the repo or dynamically at startup using only the Python standard library). Persist the tables in a deterministic format so experiments remain reproducible.
- Maintain an explicit parse stack of states and grammar symbols. For each input token, consult `ACTION[state, lookahead]`; perform the indicated shift or reduce, print the reduction immediately when `reduce` is triggered, and follow `GOTO` to push the correct successor state. Enter the accept state when ACTION returns `ACCEPT`.
- Handle the dangling `else` by ensuring the grammar or precedence rules resolve the ambiguity in favour of binding `ELSE` to the nearest unmatched `IF`. Encode any precedence directives directly into the table-construction phase so no ad-hoc runtime fixes are required.

### 3.4 Error Reporting

- Upon encountering an unexpected token, emit `SyntaxError: expected <description> before <offending lexeme> at line X, column Y` (wording may vary but must clearly identify both expectation and location).
- After the first syntax error, stop parsing and return a non-zero exit code. Do not print reduction logs for partially reduced productions after the failure point.
- Treat end-of-file as a special token to detect truncated constructs and report missing delimiters.

## 4. Output Format

- Print one line per completed reduction using the exact layout `lhs->rhs1 rhs2 ...` (no spaces adjoining `->`). Use `epsilon` for empty right-hand sides.
- Quote literal terminals with single quotes (e.g., `'('`, `';'`, `'{'`) to match `llm_parse/output.txt`. Nonterminals remain bare symbol names.
- Reductions must appear in the precise order produced by the bottom-up ACTION table. Emit the log line immediately when a reduce action fires, before the stack is rewritten with the production’s left-hand side.
- No additional whitespace, prompts, or debugging text is permitted on `stdout`.

Example reductions for a simple program:

```
ext_def_list->epsilon
type_specifier->TYPE
pointers->epsilon
func_decl->type_specifier pointers ID '(' ')'
compound_stmt->'{' def_list stmt_list '}'
ext_def->func_decl compound_stmt
ext_def_list->ext_def_list ext_def
program->ext_def_list
```

## 5. Experiment Artifacts

Each parser iteration must produce the following artifacts under `llm_parse/exp/`:

- `parser_N.py` — Python source for iteration `N`.
- `output_N.txt` — capture `stdout` and `stderr` via `python3 llm_parse/exp/parser_N.py llm_parse/input.txt > llm_parse/exp/output_N.txt 2>&1`.
- `analysis_N.md` — document environment details, command executed, observed output, deviations from `llm_parse/output.txt`, and follow-up actions.
- `lexer_N.py` — for iteration 1, refactor `llm_parse/lexer.py` into `llm_parse/exp/lexer_1.py` (and promote improvements back to `llm_parse/lexer.py`) so the parser can import a shared tokenizer.

Do not omit the execution log or the analysis report; they provide the reproducibility trail for each experiment.

## 6. Finalization

When an iteration achieves a perfect match with `llm_parse/output.txt`, freeze that implementation:

- Copy the successful `parser_N.py` to `llm_parse/parser.py`.
- Retain the corresponding `output_N.txt` and `analysis_N.md` for history.

The canonical parser entry point (`parser.py`) should always mirror the latest validated experiment so that downstream tooling can import or execute it directly.
