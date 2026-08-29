class Token:
    def __init__(self, type, value, line=0):
        self.type = type; self.value = value; self.line = line
    def __repr__(self): return f"Token({self.type}, {self.value!r})"

KEYWORDS = ['let', 'fn', 'return', 'if', 'else', 'while', 'for', 'in', 'true', 'false', 'null', 'and', 'or', 'not', 'import', 'class', 'extends', 'new', 'this', 'try', 'catch', 'throw', 'break', 'continue', 'match', 'case', 'async', 'await', 'yield']
SYMBOLS = ['{', '}', '(', ')', '[', ']', ',', ';', ':', '+=', '-=', '==', '!=', '<=', '>=', '+', '-', '*', '/', '%', '=', '<', '>', '.', '?']

def tokenize(source):
    tokens, i, line = [], 0, 1
    while i < len(source):
        c = source[i]
        if c == '\n': line += 1; i += 1; continue
        if c in ' \t\r': i += 1; continue
        if c == '/' and i+1 < len(source) and source[i+1] == '/':
            while i < len(source) and source[i] != '\n': i += 1
            continue
        if c == '"':
            j, parts, cur = i+1, [], ""
            while j < len(source) and source[j] != '"':
                if source[j] == '\\' and j+1 < len(source):
                    nxt = source[j+1]
                    cur += {'n':'\n','t':'\t','"':'"','\\':'\\'}.get(nxt, nxt); j += 2
                elif source[j] == '$' and j+1 < len(source) and source[j+1] == '{':
                    if cur: parts.append(("str", cur)); cur = ""
                    k, depth, expr = j+2, 1, ""
                    while k < len(source) and depth > 0:
                        if source[k] == '{': depth += 1
                        elif source[k] == '}':
                            depth -= 1
                            if depth == 0: break
                        expr += source[k]; k += 1
                    parts.append(("expr", expr)); j = k+1
                else: cur += source[j]; j += 1
            if cur: parts.append(("str", cur))
            if not parts: tokens.append(Token('STRING', '', line))
            elif len(parts) == 1 and parts[0][0] == "str": tokens.append(Token('STRING', parts[0][1], line))
            else: tokens.append(Token('INTERP', parts, line))
            i = j+1; continue
        if c == "'":
            j, s = i+1, ""
            while j < len(source) and source[j] != "'":
                if source[j] == '\\' and j+1 < len(source): s += source[j+1]; j += 2
                else: s += source[j]; j += 1
            tokens.append(Token('STRING', s, line)); i = j+1; continue
        if c.isdigit():
            j = i
            while j < len(source) and (source[j].isdigit() or source[j] == '.'): j += 1
            ns = source[i:j]
            tokens.append(Token('NUMBER', float(ns) if '.' in ns else int(ns), line)); i = j; continue
        if c.isalpha() or c == '_':
            j = i
            while j < len(source) and (source[j].isalnum() or source[j] == '_'): j += 1
            w = source[i:j]
            if w == 'true': tokens.append(Token('BOOL', True, line))
            elif w == 'false': tokens.append(Token('BOOL', False, line))
            elif w == 'null': tokens.append(Token('NULL', None, line))
            elif w in KEYWORDS: tokens.append(Token('KEYWORD', w, line))
            else: tokens.append(Token('IDENT', w, line))
            i = j; continue
        matched = False
        for sym in SYMBOLS:
            if source.startswith(sym, i):
                tokens.append(Token('SYMBOL', sym, line)); i += len(sym); matched = True; break
        if not matched: raise SyntaxError(f"Unexpected char {c!r} at line {line}")
    tokens.append(Token('EOF', None, line))
    return tokens
