#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../.. && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Choose Model"
echo "(0) codex"
echo "(1) gemini"
echo "(2) claude"
read -r choice

if [ "$choice" = "1" ]; then
    model="gemini"
elif [ "$choice" = "0" ]; then
    model="codex"
elif [ "$choice" = "2" ]; then
    model="claude"
else
    echo "Invalid input. Please enter 1, 0, or 2."
    exit 1
fi


EXP_DIR="$PROJECT_DIR/llm_lex_parse/llm_parse/exp_$model"

# iterate from 1 to 3

for i in {1..3}; do
    echo "Running parser test $i"

    python "$EXP_DIR/parser.py" "$SCRIPT_DIR/${i}_input.txt" > "$SCRIPT_DIR/${i}_output_parser.txt" 2>&1

    if ! diff -u "$SCRIPT_DIR/${i}_output.txt" "$SCRIPT_DIR/${i}_output_parser.txt"; then
        echo "❌ Mismatch detected in test $i."
    else
        echo "✅ All tokens match expected output in test $i."
    fi
done
