
import re
import sys
from collections import defaultdict

def lex(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # The order of token specification is important
    token_specification = [
        ('F', r'[0-9]+\.(?!\.)[0-9]*([eE][-+]?[0-9]+)?'), # Lookahead to avoid matching '..'
        ('INT', r'[1-9][0-9]*|0'),
        ('ID', r'[A-Za-z_][A-Za-z_0-9]*'),
        ('OP', r'\->|\.\.|\+\+|--|==|!=|<=|>=|&&|\|\|[(){}\[\].,;=*/%+\-<>!&]'),
        ('NEWLINE', r'\n'),
        ('SKIP', r'[ \t]+'),
    ]

    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    regex = re.compile(tok_regex)

    keywords = {'break', 'char', 'continue', 'else', 'float', 'for', 'if', 'int', 'return', 'struct', 'while', 'NULL'}
    ids = defaultdict(int)
    keys = defaultdict(int)

    pos = 0
    while pos < len(content):
        if content[pos:pos+2] == '/*':
            comment_depth = 1
            pos += 2
            while comment_depth > 0 and pos < len(content):
                if content[pos:pos+2] == '/*':
                    comment_depth += 1
                    pos += 2
                elif content[pos:pos+2] == '*/':
                    comment_depth -= 1
                    pos += 2
                else:
                    pos += 1
            continue

        match = regex.match(content, pos)
        if not match:
            pos += 1
            continue

        kind = match.lastgroup
        value = match.group()
        pos = match.end()

        if kind == 'ID':
            if value in keywords:
                keys[value] += 1
                print(f'KEY\t{value}\t{keys[value]}')
            else:
                ids[value] += 1
                print(f'ID\t{value}\t{ids[value]}')
        elif kind == 'NEWLINE' or kind == 'SKIP':
            pass
        else:
            print(f'{kind}\t{value}')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        lex(sys.argv[1])
    else:
        print("Usage: python lexer.py <file_path>")
