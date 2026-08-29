import os, json

class ReturnSignal(Exception):
    def __init__(self, value): self.value = value

class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent
    def get(self, name):
        if name in self.vars: return self.vars[name]
        if self.parent: return self.parent.get(name)
        raise NameError(f"Undefined variable: {name}")
    def set(self, name, value):
        self.vars[name] = value
    def assign(self, name, value):
        if name in self.vars:
            self.vars[name] = value
            return
        if self.parent:
            self.parent.assign(name, value)
            return
        raise NameError(f"Undefined variable: {name}")

class Function:
    def __init__(self, name, params, body, closure):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

class BuiltinFunction:
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

class Interpreter:
    def __init__(self):
        self.globals = Environment()
        self._register_builtins()
    
    def _register_builtins(self):
        builtins = {
            'print': lambda *a: print(*a) or None,
            'len': lambda x: len(x),
            'str': lambda x: str(x),
            'int': lambda x: int(x),
            'float': lambda x: float(x),
            'push': lambda lst, v: lst.append(v) or None,
            'pop': lambda lst: lst.pop(),
            'keys': lambda d: list(d.keys()),
            'values': lambda d: list(d.values()),
            'items': lambda d: list(d.items()),
            'type': lambda x: type(x).__name__,
            'range': lambda *a: list(range(*a)),
            'input': lambda prompt="": input(prompt),
            'read_file': lambda p: open(p).read(),
            'write_file': lambda p, c: open(p, 'w').write(c) or None,
            'file_exists': lambda p: os.path.exists(p),
            'json_parse': lambda s: json.loads(s),
            'json_stringify': lambda x: json.dumps(x, indent=2),
        }
        for name, fn in builtins.items():
            self.globals.set(name, BuiltinFunction(name, fn))
    
    def run(self, ast, env=None):
        env = env or self.globals
        result = None
        for stmt in ast.body:
            result = self.eval(stmt, env)
        return result
    
    def eval(self, node, env):
        t = node.type
        if t == 'Number': return node.value
        if t == 'String': return node.value
        if t == 'Bool': return node.value
        if t == 'Null': return None
        if t == 'List': return [self.eval(i, env) for i in node.items]
        if t == 'Dict': return {k: self.eval(v, env) for k, v in node.pairs}
        if t == 'Var': return env.get(node.name)
        if t == 'Let':
            val = self.eval(node.value, env)
            env.set(node.name, val)
            return val
        if t == 'Assign':
            val = self.eval(node.value, env)
            if node.target.type == 'Var':
                if node.op == '=': env.assign(node.target.name, val)
                elif node.op == '+=': env.assign(node.target.name, env.get(node.target.name) + val)
                elif node.op == '-=': env.assign(node.target.name, env.get(node.target.name) - val)
                return val
            elif node.target.type == 'Index':
                obj = self.eval(node.target.object, env)
                idx = self.eval(node.target.index, env)
                if node.op == '=': obj[idx] = val
                return val
            elif node.target.type == 'Field':
                obj = self.eval(node.target.object, env)
                if node.op == '=': obj[node.target.field] = val
                return val
            raise TypeError("Invalid assignment target")
        if t == 'BinOp':
            if node.op == 'and': return self.eval(node.left, env) and self.eval(node.right, env)
            if node.op == 'or': return self.eval(node.left, env) or self.eval(node.right, env)
            l = self.eval(node.left, env)
            r = self.eval(node.right, env)
            if node.op == '+': return l + r
            if node.op == '-': return l - r
            if node.op == '*': return l * r
            if node.op == '/': return l / r
            if node.op == '%': return l % r
            if node.op == '==': return l == r
            if node.op == '!=': return l != r
            if node.op == '<': return l < r
            if node.op == '>': return l > r
            if node.op == '<=': return l <= r
            if node.op == '>=': return l >= r
            if node.op == 'in': return l in r
            if node.op == 'in': return l in r
        if t == 'Unary':
            v = self.eval(node.operand, env)
            if node.op == '-': return -v
            if node.op == 'not': return not v
        if t == 'Call':
            callee = self.eval(node.callee, env)
            args = [self.eval(a, env) for a in node.args]
            if isinstance(callee, BuiltinFunction):
                return callee.fn(*args)
            if isinstance(callee, Function):
                fn_env = Environment(callee.closure)
                for p, a in zip(callee.params, args):
                    fn_env.set(p, a)
                try:
                    for stmt in callee.body:
                        self.eval(stmt, fn_env)
                except ReturnSignal as r:
                    return r.value
                return None
            raise TypeError(f"Not callable: {callee}")
        if t == 'Index':
            obj = self.eval(node.object, env)
            idx = self.eval(node.index, env)
            return obj[idx]
        if t == 'Field':
            obj = self.eval(node.object, env)
            return obj[node.field]
        if t == 'FnDef':
            fn = Function(node.name, node.params, node.body, env)
            env.set(node.name, fn)
            return fn
        if t == 'Return':
            raise ReturnSignal(self.eval(node.value, env))
        if t == 'If':
            if self.eval(node.condition, env):
                for s in node.then: self.eval(s, env)
            elif node.els:
                for s in node.els: self.eval(s, env)
            return None
        if t == 'While':
            while self.eval(node.condition, env):
                for s in node.body: self.eval(s, env)
            return None
        if t == 'Import':
            path = node.path
            if not os.path.exists(path):
                path = os.path.join(os.path.dirname(__file__), path)
            source = open(path).read()
            from lexer import tokenize
            from parser import Parser
            tokens = tokenize(source)
            ast = Parser(tokens).parse()
            self.run(ast, env)
            return None
        raise ValueError(f"Unknown node: {t}")
