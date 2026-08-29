import sys, os
sys.setrecursionlimit(20000)
from lexer import tokenize
from parser import Parser

class CCompiler:
    def __init__(self):
        self.output = []
        self.indent = 0
    def emit(self, line):
        self.output.append("    " * self.indent + line)
    def compile(self, ast):
        self.emit("#include <stdio.h>")
        self.emit("#include <stdlib.h>")
        self.emit("")
        for stmt in ast.body:
            self.stmt(stmt)
        return "\n".join(self.output)
    def stmt(self, n):
        t = n.type
        if t == 'Let':
            self.emit(f"int {n.name} = {self.expr(n.value)};")
        elif t == 'FnDef' and n.name:
            if n.name == 'main':
                self.emit("int main() {")
            else:
                params = ", ".join(f"int {p}" for p in n.params) or "void"
                self.emit(f"int {n.name}({params}) {{")
            self.indent += 1
            for s in n.body: self.stmt(s)
            if n.name == 'main': self.emit("return 0;")
            self.indent -= 1
            self.emit("}")
            self.emit("")
        elif t == 'Return':
            self.emit(f"return {self.expr(n.value)};")
        elif t == 'If':
            self.emit(f"if ({self.expr(n.cond)}) {{")
            self.indent += 1
            for s in n.then: self.stmt(s)
            self.indent -= 1
            if n.els:
                self.emit("} else {")
                self.indent += 1
                for s in n.els: self.stmt(s)
                self.indent -= 1
            self.emit("}")
        elif t == 'While':
            self.emit(f"while ({self.expr(n.cond)}) {{")
            self.indent += 1
            for s in n.body: self.stmt(s)
            self.indent -= 1
            self.emit("}")
        elif t == 'Call' and n.c.type == 'Var' and n.c.n == 'print':
            for a in n.args:
                self.emit(f"printf(\"%d\\n\", {self.expr(a)});")
        elif t == 'Assign' and n.t.type == 'Var':
            self.emit(f"{n.t.n} = {self.expr(n.v)};")
    def expr(self, n):
        t = n.type
        if t == 'Num': return str(int(n.v))
        if t == 'Var': return n.n
        if t == 'Bool': return "1" if n.v else "0"
        if t == 'Bin': return f"({self.expr(n.l)} {n.op} {self.expr(n.r)})"
        if t == 'Call' and n.c.type == 'Var':
            args = ", ".join(self.expr(a) for a in n.args)
            return f"{n.c.n}({args})"
        return "0"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 cc.py <file.sahaj> [output.c]")
        sys.exit(1)
    src = open(sys.argv[1]).read()
    ast = Parser(tokenize(src)).parse()
    c_code = CCompiler().compile(ast)
    out_file = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].replace('.sahaj', '.c')
    open(out_file, 'w').write(c_code)
    print(f"Generated: {out_file}")
