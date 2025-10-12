# Iteration 1 – Lexer

- Environment: Python 3.13.7
- Command: `python3 llm_lex/exp/lexer_1.py llm_lex/input.txt > llm_lex/exp/output_1.txt 2>&1`
- Summary: Implemented tokenizer covering nested comments, keywords/identifiers with reference counts, numeric literals (including floats and `..` disambiguation), and the operator set from the spec.
- Result: `llm_lex/exp/output_1.txt` matches `llm_lex/output.txt` (verified via `diff`).
