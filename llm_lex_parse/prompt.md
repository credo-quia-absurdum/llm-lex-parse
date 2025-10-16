# 🧩 Project Prompt: subC Lexer and Parser (AI Agent Specification)

## 1. Overview

This project implements a **Python-based lexical analyzer (lexer) and syntactic parser** for a simplified C-like language called **`subC`**.  

- The lexer reads raw source code, tokenizes it based on the lexical rules defined in `llm_lex/spec.md`, and emits **tab-separated ASCII tokens** or a reusable token stream. Whenever additional terminals (e.g., `CHAR_CONST`, `STRING`, `SYM_NULL`, logical or structural operators) surface in the parser grammar, revise the lexer spec and implementation so both components stay aligned. The canonical `llm_parse/lexer.py` should remain untouched after the initial refactor—store experiment-specific edits under `llm_parse/exp_codex/` instead.  
- The parser imports the shared lexer, applies the grammar and table-driven strategy defined in `llm_parse/parser_spec.md`, and emits production reductions or diagnostics.

Development follows an **iterative approach** — each iteration refines functionality, records outputs, and documents analysis results.

---

## 2. Environment & Dependencies

- **Python version:** 3.13  
  Verify with:
  ```bash
  python3 --version
  ```
- **Dependencies:** Python standard library only  
  (`re`, `argparse`, `dataclasses`, `sys`)
- **Execution Commands:**
  ```bash
  python3 llm_lex/exp/lexer_N.py llm_lex/input.txt > llm_lex/exp/output_N.txt 2>&1
  ```
  Replace `N` with the iteration number.  
Parser iterations should follow the same invocation pattern under `llm_parse/exp/`, using the parser entry point once implemented.

---

## 3. Directory & File Structure

```
llm_lex/
 ├── spec.md
 ├── input.txt
 ├── output.txt
 ├── clean.sh
 └── exp/
     ├── lexer_1.py
     ├── output_1.txt
     └── analysis_1.md
llm_parse/
 ├── lexer_spec.md
 ├── parser_spec.md
 ├── input.txt
 ├── output.txt
 ├── lexer.py
 └── exp/
     ├── parser_1.py
     ├── output_1.txt
     └── analysis_1.md
test/
 └── ...
```

- Each component maintains its own `exp/` history directly beneath the component root.
- Keep lexer and parser modules **cleanly separated** while ensuring their interfaces remain compatible.
- The `output.txt` files serve as the authoritative expected results for each component; use them to validate experiment outputs.
- Maintain consistent **relative paths** in scripts and docs for both components.

---

## 4. Iteration Workflow

Each iteration targets a single core objective: refine the script so its runtime output **exactly matches the canonical `output.txt`** stored alongside the component. To do that, every experiment produces **three artifacts** inside the component-specific `exp/` directory (`llm_lex/exp/` today, `llm_parse/exp/` once enabled). *Skipping any artifact invalidates the iteration.*

1. **Source Script**  
   `lexer_N.py` or `parser_N.py` — Python source code for iteration `N`.

2. **Execution Output**  
   `output_N.txt` — Captures both `stdout` and `stderr`.  
   Example:
   ```bash
   python3 llm_lex/exp/lexer_N.py llm_lex/input.txt > llm_lex/exp/output_N.txt 2>&1
   ```
   Adjust the command to target the parser binary and input file when working in `llm_parse/`.

3. **Analysis Report**  
   `analysis_N.md` — Summarizes:
   - Component version and environment
   - Input and full output
   - Discrepancies, bug notes, and improvements

> **Actionable rule:** Always check in the trio (`lexer_N.py`/`parser_N.py`, `output_N.txt`, `analysis_N.md`) together. Even for small tweaks, rerun the executable, capture the fresh logs, and document what changed so the experiment ledger remains reproducible.
> For the first parser iteration, also refactor `llm_parse/lexer.py` into an importable `tokenize()` helper and mirror the updated lexer under `llm_parse/exp/`. Keep the repository’s top-level `llm_parse/lexer.py` frozen after this baseline refactor; apply subsequent lexer changes only inside the experiment directory so the canonical file remains stable.


### Terminate Condition
When the generated `output_N.txt` matches the target `output.txt` in the corresponding component directory (`llm_lex` for the lexer, `llm_parse` for the parser), stop iteration for that component.
+
+When the iteration terminates, promote the final experiment script to the canonical entry point inside `exp/`:
+
+- Copy the successful `lexer_N.py` to `lexer.py`.
+- Copy the successful `parser_N.py` to `parser.py`.
+
+This ensures downstream tooling can reference a stable filename even after the experiment cycle ends.
---

## 6. Development Principles

- Strictly conform to lexical specifications in `llm_lex/spec.md` and the LALR(1) grammar requirements in `llm_parse/parser_spec.md`.
- Maintain compatibility between lexer and parser modules.
- Use the shared lexer module inside the parser; do not scrape stdout.
- Keep the parser’s reduction log formatting consistent with `llm_parse/output.txt` (one `lhs->rhs` per line, literals quoted).
- Respect prefix vs. postfix handling for `++`/`--`: do not conflate them during parsing, and validate that reductions distinguish `INCOP`/`DECOP` in both positions.
- Document every meaningful design or behavioral change.
- Treat each iteration as a self-contained, reproducible experiment.
- Preserve consistent versioning and directory hygiene for regression tests.

---

## 7. Summary

The **subC Lexer & Parser project** emphasizes clarity, reproducibility, and disciplined iteration.  
Each version must demonstrate measurable improvement in tokenization or syntactic analysis accuracy and code maintainability, supported by transparent documentation.  
Refer to `llm_parse/parser_spec.md` for the authoritative grammar, precedence table, and subC language restrictions (no typedef, union, multi-dimensional arrays, pointer-to-function types, etc.).
