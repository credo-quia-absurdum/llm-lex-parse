
import re
import sys
from collections import defaultdict

def lex(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    token_specification = [
        ('INT', r'[1-9][0-9]*|0'),
        ('F', r'[0-9]+\.[0-9]*([eE][-+]?[0-9]+)?'),
        ('ID', r'[A-Za-z_][A-Za-z_0-9]*'),
        ('OP', r'\->|\.\.|\+\+|--|==|!=|<=|>=|&&|\|\|[(){}\[\].,;=*/%+\-<>!&]'),
        ('NEWLINE', r'\n'),
        ('SKIP', r'[ \t]+'),
        ('MISMATCH', r'.'),
    ]

    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)

    keywords = {'break', 'char', 'continue', 'else', 'float', 'for', 'if', 'int', 'return', 'struct', 'while', 'NULL'}
    ids = defaultdict(int)
    keys = defaultdict(int)

    line_num = 1
    line_start = 0
    for mo in re.finditer(tok_regex, content):
        kind = mo.lastgroup
        value = mo.group()
        column = mo.start() - line_start

        if kind == 'ID':
            if value in keywords:
                keys[value] += 1
                print(f'KEY\t{value}\t{keys[value]}')
            else:
                ids[value] += 1
                print(f'ID\t{value}\t{ids[value]}')
        elif kind == 'NEWLINE':
            line_start = mo.end()
            line_num += 1
        elif kind == 'SKIP':
            pass
        elif kind == 'MISMATCH':
            # This is a simple way to handle errors.
            # A real lexer would have more sophisticated error handling.
            # For now, we just ignore mismatched characters.
            pass
        else:
            print(f'{kind}\t{value}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        lex(sys.argv[1])
    else:
        print("Usage: python lexer.py <file_path>")
