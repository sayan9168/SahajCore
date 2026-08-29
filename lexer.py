import re

class Token:
    def __init__(self, type, value, line=0):
        self.type = type
        self.value = value
        self.line = line
    def __repr__(self):
        return f"Token({self.type}, {self.value!r})"

KEYWORDS = ['let', 'fn', 'return', 'if', 'else', 'while', 'for', 'true', 'false', 'null', 'and', 'or', 'not', 'in', 'import']
SYMBOLS = ['{', '}', '(', ')', '[', ']', ',', ';', ':', '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=', '+=', '-=', '.']

def tokenize(source):
    tokens = []
    i = 0
    line = 1
    while i < len(source):
        c = source[i]
        if c == '\n':
            line += 1
            i += 1
            continue
        if c in ' \t\r':
            i += 1
            continue
        if c == '/' and i + 1 < len(source) and source[i+1] == '/':
            while i < len(source) and source[i] != '\n':
                i += 1
            continue
        if c == '"' or c == "'":
            quote = c
            j = i + 1
            s = ""
            while j < len(source) and source[j] != quote:
                if source[j] == '\\' and j + 1 < len(source):
                    nxt = source[j+1]
                    if nxt == 'n': s += '\n'
                    elif nxt == 't': s += '\t'
                    elif nxt == '"': s += '"'
                    elif nxt == "'": s += "'"
                    elif nxt == '\\': s += '\\'
                    else: s += nxt
                    j += 2
                else:
                    s += source[j]
                    j += 1
            tokens.append(Token('STRING', s, line))
            i = j + 1
            continue
        if c.isdigit() or (c == '-' and i + 1 < len(source) and source[i+1].isdigit() and (not tokens or tokens[-1].type in ('OP','SYMBOL','KEYWORD'))):
            j = i
            if c == '-': j += 1
            while j < len(source) and (source[j].isdigit() or source[j] == '.'):
                j += 1
            num_str = source[i:j]
            num = float(num_str) if '.' in num_str else int(num_str)
            tokens.append(Token('NUMBER', num, line))
            i = j
            continue
        if c.isalpha() or c == '_':
            j = i
            while j < len(source) and (source[j].isalnum() or source[j] == '_'):
                j += 1
            word = source[i:j]
            if word in KEYWORDS:
                if word == 'true': tokens.append(Token('BOOL', True, line))
                elif word == 'false': tokens.append(Token('BOOL', False, line))
                elif word == 'null': tokens.append(Token('NULL', None, line))
                else: tokens.append(Token('KEYWORD', word, line))
            else:
                tokens.append(Token('IDENT', word, line))
            i = j
            continue
        matched = False
        for sym in sorted(SYMBOLS, key=len, reverse=True):
            if source.startswith(sym, i):
                tokens.append(Token('SYMBOL', sym, line))
                i += len(sym)
                matched = True
                break
        if not matched:
            raise SyntaxError(f"Unexpected character {c!r} at line {line}")
    tokens.append(Token('EOF', None, line))
    return tokens
