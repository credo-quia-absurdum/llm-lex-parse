# 🧩 Project Prompt: subC Lexe and Parser (AI Agent Specification)

## 1. Overview

This project implements a **Python-based lexical analyzer (lexer) and syntactic parser** for a simplified C-like language called **`subC`**.  

- The lexer reads raw source code, tokenizes it based on the lexical rules defined in `lexer/spec.md`, and emits **tab-separated ASCII tokens**.  
- The parser consumes lexer output, apply the grammar in `parser/spec.md`, and report parse trees or diagnostics.

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
  python3 llm_lex/lexer/exp/lexer_N.py llm_lex/lexer/input.txt > llm_lex/lexer/exp/output_N.txt 2>&1
  ```
  Replace `N` with the iteration number.  
  Parser iterations should follow the same invocation pattern under `llm_parse/parser/exp/`, using the parser entry point once implemented.

---

## 3. Directory & File Structure

```
llm_lex/
 ├── lexer/
 │   ├── spec.md
 │   ├── input.txt
 │   ├── output.txt
 │   ├── exp/
 │   │   ├── lexer_1.py
 │   │   ├── output_1.txt
 │   │   └── analysis_1.md
 │   └── ...
 └── parser/
     ├── spec.md
     ├── input.txt
     ├── output.txt
     ├── exp/
     │   ├── parser_1.py
     │   ├── output_1.txt
     │   └── analysis_1.md
     └── ...
```

- Each component maintains its own `exp/` history.  
- Keep lexer and parser modules **cleanly separated** while ensuring their interfaces remain compatible.  
- The `output.txt` files serve as the authoritative expected results for each component; use them to validate experiment outputs.  
- Maintain consistent **relative paths** in scripts and docs for both components.

---

## 4. Iteration Workflow

Each iteration targets a single core objective: refine the script so its runtime output **exactly matches the canonical `output.txt`** stored alongside the component. To do that, every experiment produces **three artifacts** inside the component-specific `exp/` directory (`lexer/exp/` today, `parser/exp/` once enabled):

1. **Source Script**  
   `lexer_N.py` or `parser_N.py` — Python source code for iteration `N`.

2. **Execution Output**  
   `output_N.txt` — Captures both `stdout` and `stderr`.  
   Example:
   ```bash
   python3 lexer/exp/lexer_N.py ../input.txt > lexer/exp/output_N.txt 2>&1
   ```
   Adjust the command to target the parser binary and input file when working in `llm_parse/`.

3. **Analysis Report**  
   `analysis_N.md` — Summarizes:
   - Component version and environment
   - Input and full output
   - Discrepancies, bug notes, and improvements


### Terminate Condition
When the generated `output_N.txt` matches the target `output.txt` in the corresponding component directory (`llm_lex` for the lexer, `llm_parse` for the parser), stop iteration for that component.
---

## 6. Development Principles

- Strictly conform to lexical specifications in `lexer/spec.md` and `parser/spec.md`.
- Maintain compatibility between lexer and parser modules.
- Document every meaningful design or behavioral change.
- Treat each iteration as a self-contained, reproducible experiment.
- Preserve consistent versioning and directory hygiene for regression tests.

---

## 7. Summary

The **subC Lexer & Parser project** emphasizes clarity, reproducibility, and disciplined iteration.  
Each version must demonstrate measurable improvement in tokenization or syntactic analysis accuracy and code maintainability, supported by transparent documentation.  
Until the parser is implemented, maintain stubs and documentation so the transition into parser development is seamless.
