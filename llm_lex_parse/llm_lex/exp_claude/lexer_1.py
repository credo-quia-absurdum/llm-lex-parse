#!/usr/bin/env python3
"""
SubC Lexer - Iteration 1
Implements a lexical analyzer for the subC language.
"""

import sys
import re

class SubCLexer:
    def __init__(self, source_code):
        self.source = source_code
        self.pos = 0
        self.length = len(source_code)

        # Reference counts for identifiers and keywords
        self.identifier_counts = {}
        self.keyword_counts = {}

        # Keywords
        self.keywords = {
            'break', 'char', 'continue', 'else', 'float', 'for',
            'if', 'int', 'return', 'struct', 'while', 'NULL'
        }

        # Multi-character operators (order matters - longer first)
        self.multi_char_ops = ['->',  '..', '++', '--', '<=', '>=', '==', '!=', '&&', '||']

        # Single-character operators
        self.single_char_ops = ['(', ')', '[', ']', '{', '}', '.', ',', '!',
                               '*', '/', '%', '+', '-', '<', '>', '&', ';', '=']

    def current_char(self):
        """Return current character or None if at end"""
        if self.pos < self.length:
            return self.source[self.pos]
        return None

    def peek_char(self, offset=1):
        """Look ahead at character at pos + offset"""
        peek_pos = self.pos + offset
        if peek_pos < self.length:
            return self.source[peek_pos]
        return None

    def advance(self):
        """Move to next character"""
        self.pos += 1

    def skip_whitespace(self):
        """Skip spaces, tabs, and newlines"""
        while self.current_char() in [' ', '\t', '\n', '\r']:
            self.advance()

    def skip_comment(self):
        """Skip nested comments /* ... */"""
        if self.current_char() == '/' and self.peek_char() == '*':
            self.advance()  # skip '/'
            self.advance()  # skip '*'

            depth = 1
            while depth > 0 and self.pos < self.length:
                if self.current_char() == '/' and self.peek_char() == '*':
                    depth += 1
                    self.advance()
                    self.advance()
                elif self.current_char() == '*' and self.peek_char() == '/':
                    depth -= 1
                    self.advance()
                    self.advance()
                else:
                    self.advance()
            return True
        return False

    def read_number(self):
        """Read integer or float constant"""
        start_pos = self.pos

        # Read digits
        while self.current_char() and self.current_char().isdigit():
            self.advance()

        # Check for float (decimal point followed by optional digits and exponent)
        if self.current_char() == '.':
            # Need to distinguish between .. operator and float
            next_char = self.peek_char()

            # If next char is not a digit and not end, it might be .. operator
            if next_char == '.':
                # This is .. operator, return integer
                return ('INT', self.source[start_pos:self.pos])
            elif next_char and not next_char.isdigit():
                # Decimal point followed by non-digit, could be error or ..
                # For now, treat as float with no fractional part
                pass

            # It's a float
            self.advance()  # skip '.'

            # Read optional fractional digits
            while self.current_char() and self.current_char().isdigit():
                self.advance()

            # Check for exponent
            if self.current_char() in ['e', 'E']:
                self.advance()
                if self.current_char() in ['+', '-']:
                    self.advance()
                while self.current_char() and self.current_char().isdigit():
                    self.advance()

            return ('F', self.source[start_pos:self.pos])
        else:
            # Integer constant
            return ('INT', self.source[start_pos:self.pos])

    def read_identifier(self):
        """Read identifier or keyword"""
        start_pos = self.pos

        # First char is letter or underscore
        self.advance()

        # Rest can be letters, digits, or underscores
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            self.advance()

        lexeme = self.source[start_pos:self.pos]

        # Check if it's a keyword
        if lexeme in self.keywords:
            self.keyword_counts[lexeme] = self.keyword_counts.get(lexeme, 0) + 1
            return ('KEY', lexeme, self.keyword_counts[lexeme])
        else:
            self.identifier_counts[lexeme] = self.identifier_counts.get(lexeme, 0) + 1
            return ('ID', lexeme, self.identifier_counts[lexeme])

    def read_operator(self):
        """Read operator (single or multi-character)"""
        # Try multi-character operators first
        for op in self.multi_char_ops:
            if self.pos + len(op) <= self.length:
                if self.source[self.pos:self.pos+len(op)] == op:
                    self.pos += len(op)
                    return ('OP', op)

        # Single character operator
        char = self.current_char()
        if char in self.single_char_ops:
            self.advance()
            return ('OP', char)

        return None

    def tokenize(self):
        """Main tokenization loop"""
        tokens = []

        while self.pos < self.length:
            self.skip_whitespace()

            if self.pos >= self.length:
                break

            # Try to skip comment
            if self.skip_comment():
                continue

            char = self.current_char()

            # Numbers
            if char.isdigit():
                token = self.read_number()
                tokens.append(token)

            # Identifiers and keywords
            elif char.isalpha() or char == '_':
                token = self.read_identifier()
                tokens.append(token)

            # Operators
            else:
                token = self.read_operator()
                if token:
                    tokens.append(token)
                else:
                    # Unknown character, skip it
                    self.advance()

        return tokens

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 lexer_1.py <input_file>", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]

    try:
        with open(input_file, 'r') as f:
            source_code = f.read()
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found", file=sys.stderr)
        sys.exit(1)

    lexer = SubCLexer(source_code)
    tokens = lexer.tokenize()

    # Print tokens
    for token in tokens:
        if len(token) == 3:
            # Keyword or Identifier with reference count
            print(f"{token[0]}\t{token[1]}\t{token[2]}")
        else:
            # Operator, INT, or F without reference count
            print(f"{token[0]}\t{token[1]}")

if __name__ == "__main__":
    main()
