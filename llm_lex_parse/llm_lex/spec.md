# Python Lexer for subC

## 1. Goal

Implement a Python-based lexer for the `subC` language. The lexer will read a `subC` source file and print the recognized tokens to standard output according to the specified format.

## 2. Lexical Structure

### 2.1. Token Definitions

| Name               | Regular Expression                          |
| ------------------ | ------------------------------------------- |
| `letter`           | `[A-Za-z_]`                                 |
| `digit`            | `[0-9]`                                     |
| `whitespace`       | `[ \t]` (space and tab)                    |
| `integer-constant` | `[1-9]{digit}*\|0`                           |
| `float-constant`   | `{digit}+\.{digit}*([eE][-+]?{digit}+)?`   |

### 2.2. Operators

The following are single-character and multi-character operators:

`(`, `)`, `[`, `]`, `{`, `}`, `->`, `.`, `,`, `..`, `!`, `++`, `--`, `*`, `/`, `%`, `+`, `-`, `<`, `<=`, `>`, `>=`, `==`, `!=`, `&`, `&&`, `||`, `;`, `=`

### 2.3. Comments

- Comments are enclosed in `/*` and `*/`.
- The lexer must support nested comments. For example: `/* This is /* a nested */ comment */`.

### 2.4. Keywords

The following are reserved keywords:

`break`, `char`, `continue`, `else`, `float`, `for`, `if`, `int`, `return`, `struct`, `while`, `NULL`

### 2.5. Identifiers and Keywords

- Identifiers follow the pattern: `{letter}({letter}|{digit})*`.
- They are case-sensitive.
- Keywords (listed in 2.4) are reserved and cannot be used as identifiers.
- The lexer must distinguish between Identifiers and Keywords.
- A reference count must be maintained for each unique Identifier and Keyword lexeme.

## 3. Implementation Details

### 3.1. Ambiguities

#### Nested Comments

A depth counter should be used to correctly handle nested `/* ... */` comments. The lexer should enter a "comment mode" when `/*` is encountered and exit only when the outermost `*/` is found.

#### Dotdot (`..`) Operator vs. Float Constant

The lexer must correctly distinguish between the `..` operator and a float constant. For example:
- `1..2` should be tokenized as `integer-constant`, `..` (operator), `integer-constant`.
- `1.2` should be tokenized as a single `float-constant`.

This can be handled with careful ordering of regular expressions and potentially lookahead logic in the lexer.

## 4. Output Format

For each token recognized, print a line to standard output with fields separated by a single tab (`\t`).

- **For Keywords and Identifiers:** `{Token Type Abbreviation}	{Lexeme}	{Reference Count}`
- **For other tokens:** `{Token Type Abbreviation}	{Lexeme}`

### Token Type Abbreviations

| Token Type         | Abbreviation |
| ------------------ | ------------ |
| Keyword            | `KEY`        |
| Identifier         | `ID`         |
| Operator           | `OP`         |
| Integer-constant   | `INT`        |
| Float-constant     | `F`          |

### Example

Given the input:
```c
/************************
/* nested comments */
***************************/
struct _point {
float x, y, z;
int color ;
} point [20];
```

The expected output starts with (fields are tab-separated):
```
KEY	struct	1
ID	_point	1
OP	{
KEY	float	1
ID	x	1
OP	,
ID	y	1
OP	,
ID	z	1
OP	;
KEY	int	1
ID	color	1
OP	;
OP	}
ID	point	1
OP	[
INT	20
```

## 5. Experiment Artifacts

Every lexer iteration must publish a complete triplet of deliverables under `llm_lex/exp/`:

- `lexer_N.py` — the Python source for iteration `N`.
- `output_N.txt` — console output captured via `python3 llm_lex/exp/lexer_N.py llm_lex/input.txt > llm_lex/exp/output_N.txt 2>&1`.
- `analysis_N.md` — a short report that records the environment, command executed, observed output, and any findings or follow-up actions.

Do not omit the execution log or analysis. These artifacts ensure traceability between code changes and their observed behaviour.

## 6. Finalization

When the lexer experiment reaches the terminate condition (the generated output matches `llm_lex/output.txt`), promote the latest iteration file to a stable entry point within `llm_lex/exp/`:

- Copy the successful `lexer_N.py` to `lexer.py`.
- Ensure the corresponding `output_N.txt` and `analysis_N.md` remain for historical reference.

Downstream consumers should import or execute `lexer.py`, so keep it synchronized with the most recent validated iteration.
