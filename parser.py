class ASTNode:
    def __init__(self, type, **kwargs):
        self.type = type
        for k, v in kwargs.items():
            setattr(self, k, v)
    def __repr__(self):
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items() if k != 'type')
        return f"{self.type}({attrs})"

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None
    
    def eat(self, type=None, value=None):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end of input")
        if type and tok.type != type:
            raise SyntaxError(f"Expected {type}, got {tok.type} ({tok.value!r}) at line {tok.line}")
        if value is not None and tok.value != value:
            raise SyntaxError(f"Expected {value!r}, got {tok.value!r} at line {tok.line}")
        self.pos += 1
        return tok
    
    def parse(self):
        stmts = []
        while self.peek() and self.peek().type != 'EOF':
            stmts.append(self.parse_statement())
        return ASTNode('Program', body=stmts)
    
    def parse_statement(self):
        tok = self.peek()
        if tok.type == 'KEYWORD':
            if tok.value == 'let': return self.parse_let()
            if tok.value == 'fn': return self.parse_fn()
            if tok.value == 'return': return self.parse_return()
            if tok.value == 'if': return self.parse_if()
            if tok.value == 'while': return self.parse_while()
            if tok.value == 'import': return self.parse_import()
        expr = self.parse_expression()
        if self.peek() and self.peek().value == ';':
            self.eat('SYMBOL', ';')
        return expr
    
    def parse_let(self):
        self.eat('KEYWORD', 'let')
        name = self.eat('IDENT').value
        self.eat('SYMBOL', '=')
        value = self.parse_expression()
        if self.peek() and self.peek().value == ';':
            self.eat('SYMBOL', ';')
        return ASTNode('Let', name=name, value=value)
    
    def parse_fn(self):
        self.eat('KEYWORD', 'fn')
        name = self.eat('IDENT').value
        self.eat('SYMBOL', '(')
        params = []
        while self.peek() and self.peek().value != ')':
            params.append(self.eat('IDENT').value)
            if self.peek() and self.peek().value == ',':
                self.eat('SYMBOL', ',')
        self.eat('SYMBOL', ')')
        body = self.parse_block()
        return ASTNode('FnDef', name=name, params=params, body=body)
    
    def parse_block(self):
        self.eat('SYMBOL', '{')
        stmts = []
        while self.peek() and self.peek().value != '}':
            stmts.append(self.parse_statement())
        self.eat('SYMBOL', '}')
        return stmts
    
    def parse_return(self):
        self.eat('KEYWORD', 'return')
        if self.peek() and self.peek().value not in (';', '}'):
            val = self.parse_expression()
        else:
            val = ASTNode('Null')
        if self.peek() and self.peek().value == ';':
            self.eat('SYMBOL', ';')
        return ASTNode('Return', value=val)
    
    def parse_if(self):
        self.eat('KEYWORD', 'if')
        cond = self.parse_expression()
        then = self.parse_block()
        els = None
        if self.peek() and self.peek().value == 'else':
            self.eat('KEYWORD', 'else')
            if self.peek() and self.peek().value == 'if':
                els = [self.parse_if()]
            else:
                els = self.parse_block()
        return ASTNode('If', condition=cond, then=then, els=els)
    
    def parse_while(self):
        self.eat('KEYWORD', 'while')
        cond = self.parse_expression()
        body = self.parse_block()
        return ASTNode('While', condition=cond, body=body)
    
    def parse_import(self):
        self.eat('KEYWORD', 'import')
        path = self.eat('STRING').value
        if self.peek() and self.peek().value == ';':
            self.eat('SYMBOL', ';')
        return ASTNode('Import', path=path)
    
    def parse_expression(self):
        return self.parse_or()
    
    def parse_or(self):
        left = self.parse_and()
        while self.peek() and self.peek().type == 'KEYWORD' and self.peek().value == 'or':
            self.eat()
            right = self.parse_and()
            left = ASTNode('BinOp', op='or', left=left, right=right)
        return left
    
    def parse_and(self):
        left = self.parse_comparison()
        while self.peek() and self.peek().type == 'KEYWORD' and self.peek().value == 'and':
            self.eat()
            right = self.parse_comparison()
            left = ASTNode('BinOp', op='and', left=left, right=right)
        return left
    
    def parse_comparison(self):
        left = self.parse_add()
        while self.peek() and (self.peek().value in ('==', '!=', '<', '>', '<=', '>=') or (self.peek().type == 'KEYWORD' and self.peek().value == 'in')):
            op = self.eat().value
            right = self.parse_add()
            left = ASTNode('BinOp', op=op, left=left, right=right)
        return left
    
    def parse_add(self):
        left = self.parse_mul()
        while self.peek() and self.peek().type == 'SYMBOL' and self.peek().value in ('+', '-'):
            op = self.eat().value
            right = self.parse_mul()
            left = ASTNode('BinOp', op=op, left=left, right=right)
        return left
    
    def parse_mul(self):
        left = self.parse_unary()
        while self.peek() and self.peek().type == 'SYMBOL' and self.peek().value in ('*', '/', '%'):
            op = self.eat().value
            right = self.parse_unary()
            left = ASTNode('BinOp', op=op, left=left, right=right)
        return left
    
    def parse_unary(self):
        if self.peek() and self.peek().type == 'KEYWORD' and self.peek().value == 'not':
            self.eat()
            return ASTNode('Unary', op='not', operand=self.parse_unary())
        if self.peek() and self.peek().type == 'SYMBOL' and self.peek().value == '-':
            self.eat()
            return ASTNode('Unary', op='-', operand=self.parse_unary())
        return self.parse_postfix()
    
    def parse_postfix(self):
        node = self.parse_primary()
        while True:
            if self.peek() and self.peek().type == 'SYMBOL' and self.peek().value == '(':
                self.eat('SYMBOL', '(')
                args = []
                while self.peek() and self.peek().value != ')':
                    args.append(self.parse_expression())
                    if self.peek() and self.peek().value == ',':
                        self.eat('SYMBOL', ',')
                self.eat('SYMBOL', ')')
                node = ASTNode('Call', callee=node, args=args)
            elif self.peek() and self.peek().type == 'SYMBOL' and self.peek().value == '[':
                self.eat('SYMBOL', '[')
                idx = self.parse_expression()
                self.eat('SYMBOL', ']')
                node = ASTNode('Index', object=node, index=idx)
            elif self.peek() and self.peek().type == 'SYMBOL' and self.peek().value == '.':
                self.eat('SYMBOL', '.')
                field = self.eat('IDENT').value
                node = ASTNode('Field', object=node, field=field)
            elif self.peek() and self.peek().type == 'SYMBOL' and self.peek().value in ('=', '+=', '-='):
                op = self.eat().value
                val = self.parse_expression()
                node = ASTNode('Assign', target=node, op=op, value=val)
            else:
                break
        return node
    
    def parse_primary(self):
        tok = self.peek()
        if tok is None:
            raise SyntaxError("Unexpected end")
        if tok.type == 'NUMBER':
            self.eat()
            return ASTNode('Number', value=tok.value)
        if tok.type == 'STRING':
            self.eat()
            return ASTNode('String', value=tok.value)
        if tok.type == 'BOOL':
            self.eat()
            return ASTNode('Bool', value=tok.value)
        if tok.type == 'NULL':
            self.eat()
            return ASTNode('Null')
        if tok.type == 'IDENT':
            self.eat()
            return ASTNode('Var', name=tok.value)
        if tok.type == 'SYMBOL' and tok.value == '(':
            self.eat()
            expr = self.parse_expression()
            self.eat('SYMBOL', ')')
            return expr
        if tok.type == 'SYMBOL' and tok.value == '[':
            self.eat()
            items = []
            while self.peek() and self.peek().value != ']':
                items.append(self.parse_expression())
                if self.peek() and self.peek().value == ',':
                    self.eat('SYMBOL', ',')
            self.eat('SYMBOL', ']')
            return ASTNode('List', items=items)
        if tok.type == 'SYMBOL' and tok.value == '{':
            self.eat()
            pairs = []
            while self.peek() and self.peek().value != '}':
                key = self.eat('STRING').value
                self.eat('SYMBOL', ':')
                val = self.parse_expression()
                pairs.append((key, val))
                if self.peek() and self.peek().value == ',':
                    self.eat('SYMBOL', ',')
            self.eat('SYMBOL', '}')
            return ASTNode('Dict', pairs=pairs)
        raise SyntaxError(f"Unexpected token {tok} at line {tok.line}")
