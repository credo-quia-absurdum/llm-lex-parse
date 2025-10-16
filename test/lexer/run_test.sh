#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Choose Model"
echo "(0) codex"
echo "(1) gemini"
read -r choice

if [ "$choice" = "1" ]; then
    model="gemini"
elif [ "$choice" = "0" ]; then
    model="codex"
else
    echo "Invalid input. Please enter 1 or 0."
    exit 1
fi


EXP_DIR="$PROJECT_DIR/llm_lex_parse/llm_lex/exp_$model"

echo "Running lexer test 1"

python "$EXP_DIR/lexer.py" "$SCRIPT_DIR/1_input.txt" > "$SCRIPT_DIR/1_output_lexer.txt"

if ! diff -u "$SCRIPT_DIR/1_output.txt" "$SCRIPT_DIR/1_output_lexer.txt"; then
    echo "❌ Mismatch detected."
else
    echo "✅ All tokens match expected output."
fi

