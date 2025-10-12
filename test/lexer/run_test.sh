#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXP_DIR="$PROJECT_DIR/llm_lex_parse/llm_lex/exp"

echo "Running lexer test 1"

python "$EXP_DIR/lexer.py" "$SCRIPT_DIR/1_input.txt" > "$SCRIPT_DIR/1_output_lexer.txt"

if ! diff -u "$SCRIPT_DIR/1_output.txt" "$SCRIPT_DIR/1_output_lexer.txt"; then
    echo "❌ Mismatch detected."
else
    echo "✅ All tokens match expected output."
fi

