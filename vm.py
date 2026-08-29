class Compiler:
    def __init__(self): self.code = []
    def emit(self, op, arg=None): self.code.append((op, arg))
    def compile(self, ast):
        for s in ast.body: self.stmt(s)
        self.emit('HALT')
        return self.code
    def stmt(self, n):
        t = n.type
        if t == 'Let':
            self.expr(n.value); self.emit('STORE', n.name)
        elif t == 'Assign' and n.t.type == 'Var':
            self.expr(n.v); self.emit('STORE', n.t.n)
        elif t == 'Call' and n.c.type == 'Var' and n.c.n == 'print':
            for a in n.args: self.expr(a)
            self.emit('PRINT', len(n.args))
        elif t == 'If':
            self.expr(n.cond)
            jz = len(self.code); self.emit('JZ', None)
            for s in n.then: self.stmt(s)
            if n.els:
                jmp = len(self.code); self.emit('JMP', None)
                self.code[jz] = ('JZ', len(self.code))
                for s in n.els: self.stmt(s)
                self.code[jmp] = ('JMP', len(self.code))
            else:
                self.code[jz] = ('JZ', len(self.code))
        elif t == 'While':
            start = len(self.code)
            self.expr(n.cond)
            jz = len(self.code); self.emit('JZ', None)
            for s in n.body: self.stmt(s)
            self.emit('JMP', start)
            self.code[jz] = ('JZ', len(self.code))
        else:
            self.expr(n); self.emit('POP')
    def expr(self, n):
        t = n.type
        if t in ('Num', 'Str', 'Bool'): self.emit('CONST', n.v)
        elif t == 'Var': self.emit('LOAD', n.n)
        elif t == 'Bin':
            self.expr(n.l); self.expr(n.r); self.emit('BIN', n.op)
        else: raise Exception('VM unsupported expr: ' + t)

class VM:
    def __init__(self, code): self.code, self.stack, self.vars, self.ip = code, [], {}, 0
    def bin2(self, l, r, op):
        return {'+': l+r, '-': l-r, '*': l*r, '/': l/r, '%': l%r, '==': l==r, '!=': l!=r, '<': l<r, '>': l>r, '<=': l<=r, '>=': l>=r}[op]
    def run(self):
        while True:
            op, arg = self.code[self.ip]; self.ip += 1
            if op == 'HALT': break
            elif op == 'CONST': self.stack.append(arg)
            elif op == 'LOAD': self.stack.append(self.vars.get(arg))
            elif op == 'STORE': self.vars[arg] = self.stack.pop()
            elif op == 'POP': self.stack.pop()
            elif op == 'PRINT':
                args = [self.stack.pop() for _ in range(arg or 1)][::-1]
                print(*args)
            elif op == 'JMP': self.ip = arg
            elif op == 'JZ':
                if not self.stack.pop(): self.ip = arg
            elif op == 'BIN':
                r = self.stack.pop(); l = self.stack.pop()
                self.stack.append(self.bin2(l, r, arg))
        return self.stack
