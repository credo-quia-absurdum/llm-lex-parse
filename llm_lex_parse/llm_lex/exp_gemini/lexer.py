
import re
import sys
from collections import defaultdict

def remove_comments(text):
    """Removes nested /* ... */ comments from a string."""
    result = []
    comment_depth = 0
    i = 0
    while i < len(text):
        if text[i:i+2] == '/*':
            comment_depth += 1
            i += 2
        elif text[i:i+2] == '*/':
            comment_depth -= 1
            i += 2
        elif comment_depth == 0:
            result.append(text[i])
            i += 1
        else:
            i += 1
    return "".join(result)

def lex(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    content = remove_comments(content)

    # Operators need to be ordered from longest to shortest to ensure correct matching
    operators = ['->', '..', '++', '--', '==', '!=', '<=', '>=', '&&', '||', '(', ')', '[', ']', '{', '}', '.', ',', '!', '*', '/', '%', '+', '-', '<', '>', '&', ';', '=']
    operators.sort(key=len, reverse=True)
    op_regex = '|'.join(re.escape(op) for op in operators)

    token_specification = [
        ('F', r'[0-9]+\.(?!\.)[0-9]*([eE][-+]?[0-9]+)?'),
        ('INT', r'[1-9][0-9]*|0'),
        ('ID', r'[A-Za-z_][A-Za-z_0-9]*'),
        ('OP', op_regex),
        ('NEWLINE', r'\n'),
        ('SKIP', r'[ \t]+'),
        ('MISMATCH', r'.'),
    ]

    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)

    keywords = {'break', 'char', 'continue', 'else', 'float', 'for', 'if', 'int', 'return', 'struct', 'while', 'NULL'}
    ids = defaultdict(int)
    keys = defaultdict(int)

    for mo in re.finditer(tok_regex, content):
        kind = mo.lastgroup
        value = mo.group()

        if kind == 'ID':
            if value in keywords:
                keys[value] += 1
                print(f'KEY\t{value}\t{keys[value]}')
            else:
                ids[value] += 1
                print(f'ID\t{value}\t{ids[value]}')
        elif kind in ('NEWLINE', 'SKIP', 'MISMATCH'):
            pass
        else:
            print(f'{kind}\t{value}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        lex(sys.argv[1])
    else:
        print("Usage: python lexer.py <file_path>")
