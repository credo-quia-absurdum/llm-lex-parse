#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python "$SCRIPT_DIR/../../llm_lex/lexer/exp/lexer.py" 1_input.txt > "$SCRIPT_DIR/../../llm_lex/lexer/exp/1_output_lexer.txt"
echo Checking lexer output for "$SCRIPT_DIR/../../llm_lex/lexer/exp/1_output_lexer.txt"
diff "$SCRIPT_DIR/1_output.txt" "$SCRIPT_DIR/../../llm_lex/lexer/exp/1_output_lexer.txt"
