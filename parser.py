class ASTNode:
    def __init__(self, type, **kw):
        self.type = type
        for k, v in kw.items(): setattr(self, k, v)

class Parser:
    def __init__(self, tokens): self.tokens, self.pos = tokens, 0
    def peek(self): return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    def eat(self, type=None, value=None):
        t = self.peek()
        if not t: raise SyntaxError("Unexpected EOF")
        if type and t.type != type: raise SyntaxError(f"Expected {type}, got {t.type}")
        if value is not None and t.value != value: raise SyntaxError(f"Expected {value}, got {t.value}")
        self.pos += 1; return t

    def parse(self):
        stmts = []
        while self.peek() and self.peek().type != 'EOF': stmts.append(self.parse_stmt())
        return ASTNode('Program', body=stmts)

    def parse_stmt(self):
        t = self.peek()
        if t.type == 'KEYWORD':
            if t.value == 'let': return self.parse_let()
            if t.value == 'fn': return self.parse_fn()
            if t.value == 'return': return self.parse_return()
            if t.value == 'if': return self.parse_if()
            if t.value == 'while': return self.parse_while()
            if t.value == 'for': return self.parse_for()
            if t.value == 'class': return self.parse_class()
            if t.value == 'try': return self.parse_try()
            if t.value == 'throw': return self.parse_throw()
            if t.value == 'import': return self.parse_import()
            if t.value == 'break': self.eat(); return ASTNode('Break')
            if t.value == 'continue': self.eat(); return ASTNode('Continue')
            if t.value == 'match': return self.parse_match()
            if t.value == 'async': self.eat(); n = self.parse_fn(); n.is_async = True; return n
            if t.value == 'yield': return self.parse_yield()
        e = self.parse_expr()
        if self.peek() and self.peek().value == ';': self.eat('SYMBOL', ';')
        return e

    def parse_let(self):
        self.eat('KEYWORD', 'let'); n = self.eat('IDENT').value; self.eat('SYMBOL', '=')
        v = self.parse_expr()
        if self.peek() and self.peek().value == ';': self.eat('SYMBOL', ';')
        return ASTNode('Let', name=n, value=v)

    def parse_fn(self):
        self.eat('KEYWORD', 'fn')
        name = None
        if self.peek().type == 'IDENT': name = self.eat('IDENT').value
        self.eat('SYMBOL', '('); params = []
        while self.peek() and self.peek().value != ')':
            if self.peek().type == 'IDENT':
                params.append(self.eat('IDENT').value)
            elif self.peek().type == 'KEYWORD' and self.peek().value == 'this':
                params.append(self.eat().value)
            else:
                raise SyntaxError("Expected parameter name")
            if self.peek().value == ',': self.eat('SYMBOL', ',')
        self.eat('SYMBOL', ')'); body = self.parse_block()
        n = ASTNode('FnDef', name=name, params=params, body=body)
        n.is_async = False
        return n

    def parse_block(self):
        self.eat('SYMBOL', '{'); stmts = []
        while self.peek() and self.peek().value != '}': stmts.append(self.parse_stmt())
        self.eat('SYMBOL', '}'); return stmts

    def parse_return(self):
        self.eat('KEYWORD', 'return')
        v = ASTNode('Null')
        if self.peek() and self.peek().value not in (';', '}'): v = self.parse_expr()
        if self.peek() and self.peek().value == ';': self.eat('SYMBOL', ';')
        return ASTNode('Return', value=v)

    def parse_if(self):
        self.eat('KEYWORD', 'if'); c = self.parse_expr(); t = self.parse_block(); e = None
        if self.peek() and self.peek().value == 'else':
            self.eat('KEYWORD', 'else')
            e = [self.parse_if()] if self.peek().value == 'if' else self.parse_block()
        return ASTNode('If', cond=c, then=t, els=e)

    def parse_while(self):
        self.eat('KEYWORD', 'while'); c = self.parse_expr(); b = self.parse_block()
        return ASTNode('While', cond=c, body=b)

    def parse_for(self):
        self.eat('KEYWORD', 'for'); v = self.eat('IDENT').value; self.eat('KEYWORD', 'in')
        it = self.parse_expr(); b = self.parse_block()
        return ASTNode('For', var=v, iter=it, body=b)

    def parse_class(self):
        self.eat('KEYWORD', 'class'); n = self.eat('IDENT').value; p = None
        if self.peek() and self.peek().value == 'extends': self.eat('KEYWORD', 'extends'); p = self.eat('IDENT').value
        self.eat('SYMBOL', '{'); m = []
        while self.peek() and self.peek().value != '}':
            if self.peek().value == 'fn': m.append(self.parse_fn())
            else: self.eat()
        self.eat('SYMBOL', '}')
        return ASTNode('ClassDef', name=n, parent=p, methods=m)

    def parse_try(self):
        self.eat('KEYWORD', 'try'); b = self.parse_block(); self.eat('KEYWORD', 'catch')
        v = self.eat('IDENT').value; cb = self.parse_block()
        return ASTNode('Try', body=b, var=v, catch=cb)

    def parse_throw(self):
        self.eat('KEYWORD', 'throw'); v = self.parse_expr()
        if self.peek() and self.peek().value == ';': self.eat('SYMBOL', ';')
        return ASTNode('Throw', value=v)

    def parse_import(self):
        self.eat('KEYWORD', 'import')
        return ASTNode('Import', path=self.eat('STRING').value)
    def parse_yield(self):
        self.eat('KEYWORD', 'yield')
        return ASTNode('Yield', value=self.parse_expr())
    def parse_expr(self): return self.parse_ternary()
    def parse_ternary(self):
        c = self.parse_or()
        if self.peek() and self.peek().type == 'SYMBOL' and self.peek().value == '?':
            self.eat()
            a = self.parse_ternary()
            self.eat('SYMBOL', ':')
            b = self.parse_ternary()
            return ASTNode('Ternary', c=c, a=a, b=b)
        return c
    def parse_match(self):
        self.eat('KEYWORD', 'match')
        subject = self.parse_expr()
        self.eat('SYMBOL', '{')
        cases = []
        while self.peek() and not (self.peek().type == 'SYMBOL' and self.peek().value == '}'):
            self.eat('KEYWORD', 'case')
            pat = self.parse_prim()
            body = self.parse_block()
            cases.append((pat, body))
        self.eat('SYMBOL', '}')
        return ASTNode('Match', subject=subject, cases=cases)
    def parse_or(self):
        l = self.parse_and()
        while self.peek() and self.peek().value == 'or': self.eat(); l = ASTNode('Bin', op='or', l=l, r=self.parse_and())
        return l
    def parse_and(self):
        l = self.parse_cmp()
        while self.peek() and self.peek().value == 'and': self.eat(); l = ASTNode('Bin', op='and', l=l, r=self.parse_cmp())
        return l
    def parse_cmp(self):
        l = self.parse_add()
        while self.peek() and self.peek().type == 'SYMBOL' and self.peek().value in ('==','!=','<','>','<=','>='):
            o = self.eat().value; l = ASTNode('Bin', op=o, l=l, r=self.parse_add())
        while self.peek() and self.peek().value == 'in': self.eat(); l = ASTNode('Bin', op='in', l=l, r=self.parse_add())
        return l
    def parse_add(self):
        l = self.parse_mul()
        while self.peek() and self.peek().type == 'SYMBOL' and self.peek().value in ('+','-'):
            o = self.eat().value; l = ASTNode('Bin', op=o, l=l, r=self.parse_mul())
        return l
    def parse_mul(self):
        l = self.parse_unary()
        while self.peek() and self.peek().type == 'SYMBOL' and self.peek().value in ('*','/','%'):
            o = self.eat().value; l = ASTNode('Bin', op=o, l=l, r=self.parse_unary())
        return l
    def parse_unary(self):
        if self.peek() and self.peek().type == 'KEYWORD' and self.peek().value == 'await': self.eat(); return ASTNode('Await', v=self.parse_unary())
        if self.peek() and self.peek().value == 'not': self.eat(); return ASTNode('Un', op='not', v=self.parse_unary())
        if self.peek() and self.peek().value == '-': self.eat(); return ASTNode('Un', op='-', v=self.parse_unary())
        return self.parse_post()
    def parse_post(self):
        n = self.parse_prim()
        while True:
            if self.peek() and self.peek().value == '(':
                self.eat('SYMBOL', '('); args = []
                while self.peek() and self.peek().value != ')':
                    args.append(self.parse_expr())
                    if self.peek().value == ',': self.eat('SYMBOL', ',')
                self.eat('SYMBOL', ')'); n = ASTNode('Call', c=n, args=args)
            elif self.peek() and self.peek().value == '[':
                self.eat('SYMBOL', '['); i = self.parse_expr(); self.eat('SYMBOL', ']'); n = ASTNode('Idx', o=n, i=i)
            elif self.peek() and self.peek().value == '.':
                self.eat('SYMBOL', '.'); f = self.eat('IDENT').value; n = ASTNode('Field', o=n, f=f)
            elif self.peek() and self.peek().value in ('=','+=','-='):
                o = self.eat().value; v = self.parse_expr(); n = ASTNode('Assign', t=n, op=o, v=v)
            else: break
        return n
    def parse_prim(self):
        t = self.peek()
        if not t: raise SyntaxError("Unexpected EOF")
        if t.type == 'NUMBER': self.eat(); return ASTNode('Num', v=t.value)
        if t.type == 'STRING': self.eat(); return ASTNode('Str', v=t.value)
        if t.type == 'INTERP': self.eat(); return ASTNode('IStr', p=t.value)
        if t.type == 'BOOL': self.eat(); return ASTNode('Bool', v=t.value)
        if t.type == 'NULL': self.eat(); return ASTNode('Null')
        if t.type == 'IDENT': self.eat(); return ASTNode('Var', n=t.value)
        if t.value == 'this': self.eat(); return ASTNode('This')
        if t.value == 'new':
            self.eat(); c = self.eat('IDENT').value; self.eat('SYMBOL', '('); args = []
            while self.peek() and self.peek().value != ')':
                args.append(self.parse_expr())
                if self.peek().value == ',': self.eat('SYMBOL', ',')
            self.eat('SYMBOL', ')'); return ASTNode('New', c=c, args=args)
        if t.value == '(': self.eat(); e = self.parse_expr(); self.eat('SYMBOL', ')'); return e
        if t.value == '[':
            self.eat(); its = []
            while self.peek() and self.peek().value != ']':
                its.append(self.parse_expr())
                if self.peek().value == ',': self.eat('SYMBOL', ',')
            self.eat('SYMBOL', ']'); return ASTNode('List', its=its)
        if t.value == '{':
            self.eat(); ps = []
            while self.peek() and self.peek().value != '}':
                k = self.eat('STRING').value; self.eat('SYMBOL', ':'); v = self.parse_expr(); ps.append((k,v))
                if self.peek().value == ',': self.eat('SYMBOL', ',')
            self.eat('SYMBOL', '}'); return ASTNode('Dict', ps=ps)
        raise SyntaxError(f"Unexpected {t}")
