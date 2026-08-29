import sys
sys.setrecursionlimit(20000)
from lexer import tokenize
from parser import Parser

class WasmCompiler:
    def compile(self, ast):
        self.ast = ast
        lines = ["(module"]
        for s in ast.body:
            if s.type == 'FnDef' and s.name:
                lines += self.fn(s)
        for s in ast.body:
            if s.type == 'FnDef' and s.name:
                lines.append(f'  (export "{s.name}" (func ${s.name}))')
        lines.append(")")
        return "\n".join(lines)
    def fn(self, n):
        params = "".join(f" (param ${p} i32)" for p in n.params)
        out = [f"  (func ${n.name}{params} (result i32)"]
        for l in self.locals(n.body, set(n.params)):
            out.append(f"    (local ${l} i32)")
        for s in n.body:
            out += self.stmt(s)
        out.append("  )")
        return out
    def locals(self, body, seen):
        loc = []
        for s in body:
            if s.type == 'Let' and s.name not in seen:
                seen.add(s.name); loc.append(s.name)
        return loc
    def stmt(self, n):
        t = n.type
        if t == 'Return':
            return ["    " + l for l in self.expr(n.value)]
        if t == 'Let':
            return ["    " + l for l in self.expr(n.value)] + [f"    local.set ${n.name}"]
        if t == 'Assign' and n.t.type == 'Var':
            return ["    " + l for l in self.expr(n.v)] + [f"    local.set ${n.t.n}"]
        return []
    def expr(self, n):
        t = n.type
        if t == 'Num': return [f"i32.const {int(n.v)}"]
        if t == 'Var': return [f"local.get ${n.n}"]
        if t == 'Bin':
            op = {'+': 'i32.add', '-': 'i32.sub', '*': 'i32.mul'}.get(n.op)
            return self.expr(n.l) + self.expr(n.r) + [op]
        if t == 'Call' and n.c.type == 'Var':
            lines = []
            for a in n.args: lines += self.expr(a)
            lines.append(f"call ${n.c.n}")
            return lines
        return ["i32.const 0"]

if __name__ == '__main__':
    src = open(sys.argv[1]).read()
    ast = Parser(tokenize(src)).parse()
    wat = WasmCompiler().compile(ast)
    out = sys.argv[2] if len(sys.argv) > 2 else sys.argv[1].replace('.sahaj', '.wat')
    open(out, 'w').write(wat)
    print(f"Generated: {out}")
