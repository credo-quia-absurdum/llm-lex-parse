# Lexer
```
You will implement and run lexer experiments for Claude Code.
Untrathink for this project.

Your working directory is `llm_lex/exp_claude/`, hereafter referred to as `exp/`.

Read the following resources carefully:
- prompt.md  
- llm_lex/spec.md  

Begin a lexer implementation experiment in `exp/` and iterate until the generated tokens
exactly match `llm_lex/output.txt` when tested on `llm_lex/input.txt`.

For each iteration **N**, record the following trio:
- `exp/lexer_N.py`
- `exp/output_N.txt` (captured with `python3 ... > ... 2>&1`)
- `exp/analysis_N.md`

Continue refining the lexer until convergence is reached.
Once it matches perfectly, promote the final working script to:
- `exp/lexer.py`
```

# Parser
```
You will implement and run parser experiments for Codex.

Your working directory is `llm_parse/exp_codex/`, hereafter referred to as `exp/`.

Read the following resources carefully:
- prompt.md  
- llm_parse/lexer_spec.md  
- llm_parse/parser_spec.md  
- llm_parse/lexer.py  
- llm_parse/input.txt  
- llm_parse/output.txt  

Start by implementing `exp/lexer.py`, referring to `llm_parse/lexer.py`.  
This lexer will later be imported by the parser.

You may need to define additional token classes to satisfy the grammar requirements described in `parser_spec.md`.

Then, begin iterative parser implementation in `exp/`.  
For each iteration **N**, produce the following files:
- `exp/parser_N.py`
- `exp/output_N.txt` (captured with `python3 ... > ... 2>&1`)
- `exp/analysis_N.md`

Continue iterating until the output of your parser exactly matches  
`llm_parse/output.txt` when tested on `llm_parse/input.txt`.

Once convergence is reached, promote the final working script to:
- `exp/parser.py`
```