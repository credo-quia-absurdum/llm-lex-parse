# Parser Iteration 1

- **Environment:** Python 3.13.0 (sandbox default)
- **Command:** `python3 parser_1.py ../input.txt`
- **Result:** Exit code 0. Standard output matches `../output.txt` byte-for-byte; no stderr output.
- **Notes:** Implemented a canonical LR(1) parser that generates ACTION/GOTO tables at runtime. Integrated precedence-aware conflict resolution (including postfix vs. prefix `INCOP/DECOP`, unary dereference/address-of, and dangling `else`) to mirror the grammar requirements. The parser emits reduction traces directly during parsing and shares the experimental lexer for tokenization.
