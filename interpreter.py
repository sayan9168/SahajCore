import os, json, sys
sys.setrecursionlimit(20000)
class Ret(Exception):
    def __init__(self, v): self.v = v
class Thr(Exception):
    def __init__(self, v): self.v = v
class Env:
    def __init__(self, p=None): self.v, self.p = {}, p
    def get(self, n):
        if n in self.v: return self.v[n]
        return self.p.get(n) if self.p else None
    def set(self, n, val): self.v[n] = val
    def assign(self, n, val):
        if n in self.v: self.v[n] = val; return
        if self.p: self.p.assign(n, val); return
class Func:
    def __init__(self, n, p, b, c): self.n, self.p, self.b, self.c = n, p, b, c
class BFunc:
    def __init__(self, n, f): self.n, self.f = n, f
class Cls:
    def __init__(self, n, p, m): self.n, self.p, self.m = n, p, m
def find_method(cls, name):
    while cls:
        if name in cls.m:
            return cls.m[name]
        cls = cls.p
    return None

class Inst:
    def __init__(self, c): self.c, self.f = c, {}
    def get(self, n):
        if n in self.f: return self.f[n]
        m = find_method(self.c, n)
        if m: return Bnd(self, m)
        return None
class Bnd:
    def __init__(self, i, f): self.i, self.f = i, f

LM = {'push': lambda l, *a: l.append(a[0]) if a else None, 'pop': lambda l: l.pop() if l else None, 'len': lambda l: len(l), 'contains': lambda l, x: x in l}
DM = {'keys': lambda d: list(d.keys()), 'values': lambda d: list(d.values()), 'has': lambda d, k: k in d}
SM = {'len': lambda s: len(s), 'upper': lambda s: s.upper(), 'lower': lambda s: s.lower(), 'split': lambda s, x=" ": s.split(x), 'contains': lambda s, x: x in s}

class Interp:
    def __init__(self):
        self.g = Env()
        for n, f in {'print': lambda *a: print(*a) or None, 'len': len, 'str': str, 'int': int, 'float': float, 'range': lambda *a: list(range(*[int(x) for x in a])), 'type': lambda x: type(x).__name__, 'read_file': lambda p: open(p).read(), 'write_file': lambda p, c: open(p, 'w').write(c) or None}.items():
            self.g.set(n, BFunc(n, f))
    def run(self, ast, env=None):
        env = env or self.g
        r = None
        for s in ast.body: r = self.ev(s, env)
        return r
    def ev(self, n, e):
        t = n.type
        if t == 'Num' or t == 'Str' or t == 'Bool': return n.v
        if t == 'Null': return None
        if t == 'This': return e.get("this")
        if t == 'IStr':
            r = ""
            for k, v in n.p:
                if k == "str": r += v
                else:
                    from lexer import tokenize
                    from parser import Parser
                    r += str(self.ev(Parser(tokenize(v)).parse().body[0], e))
            return r
        if t == 'List': return [self.ev(i, e) for i in n.its]
        if t == 'Dict': return {k: self.ev(v, e) for k, v in n.ps}
        if t == 'Var': return e.get(n.n)
        if t == 'Let': v = self.ev(n.value, e); e.set(n.name, v); return v
        if t == 'Assign':
            v = self.ev(n.v, e)
            if n.t.type == 'Var':
                if n.op == '=': e.assign(n.t.n, v)
                elif n.op == '+=': e.assign(n.t.n, e.get(n.t.n) + v)
                elif n.op == '-=': e.assign(n.t.n, e.get(n.t.n) - v)
            elif n.t.type == 'Idx': o = self.ev(n.t.o, e); o[self.ev(n.t.i, e)] = v
            elif n.t.type == 'Field':
                o = self.ev(n.t.o, e)
                if isinstance(o, Inst): o.f[n.t.f] = v
                else: o[n.t.f] = v
            return v
        if t == 'Bin':
            if n.op == 'and': return self.ev(n.l, e) and self.ev(n.r, e)
            if n.op == 'or': return self.ev(n.l, e) or self.ev(n.r, e)
            l, r = self.ev(n.l, e), self.ev(n.r, e)
            return {'+': l+r, '-': l-r, '*': l*r, '/': l/r, '%': l%r, '==': l==r, '!=': l!=r, '<': l<r, '>': l>r, '<=': l<=r, '>=': l>=r, 'in': l in r}[n.op]
        if t == 'Un':
            v = self.ev(n.v, e)
            return -v if n.op == '-' else not v
        if t == 'Call':
            args = [self.ev(a, e) for a in n.args]
            if n.c.type == 'Field':
                obj = self.ev(n.c.o, e); m = n.c.f
                if isinstance(obj, list) and m in LM: return LM[m](obj, *args)
                if isinstance(obj, dict) and m in DM: return DM[m](obj, *args)
                if isinstance(obj, str) and m in SM: return SM[m](obj, *args)
                if isinstance(obj, Inst):
                    bnd = obj.get(m)
                    if isinstance(bnd, Bnd):
                        fe = Env(bnd.f.c); fe.set("this", bnd.i)
                        rp = [p for p in bnd.f.p if p != "this"]
                        for p, a in zip(rp, args): fe.set(p, a)
                        try:
                            for s in bnd.f.b: self.ev(s, fe)
                        except Ret as r: return r.v
                        return None
            c = self.ev(n.c, e)
            if isinstance(c, BFunc): return c.f(*args)
            if isinstance(c, Func):
                fe = Env(c.c)
                for p, a in zip(c.p, args): fe.set(p, a)
                try:
                    for s in c.b: self.ev(s, fe)
                except Ret as r: return r.v
            if isinstance(c, Bnd):
                fe = Env(c.f.c); fe.set("this", c.i)
                rp = [p for p in c.f.p if p != "this"]
                for p, a in zip(rp, args): fe.set(p, a)
                try:
                    for s in c.f.b: self.ev(s, fe)
                except Ret as r: return r.v
        if t == 'New':
            cls = e.get(n.c)
            inst = Inst(cls)
            if "init" in cls.m:
                fn = cls.m["init"]; fe = Env(fn.c); fe.set("this", inst)
                rp = [p for p in fn.p if p != "this"]
                for p, a in zip(rp, n.args): fe.set(p, a)
                try:
                    for s in fn.b: self.ev(s, fe)
                except Ret: pass
            return inst
        if t == 'Idx': return self.ev(n.o, e)[self.ev(n.i, e)]
        if t == 'Field':
            o = self.ev(n.o, e)
            if isinstance(o, Inst): return o.get(n.f)
            if isinstance(o, dict): return o.get(n.f)
        if t == 'FnDef':
            fn = Func(n.name, n.params, n.body, e)
            if n.name: e.set(n.name, fn)
            return fn
        if t == 'ClassDef':
            pc = e.get(n.parent) if n.parent else None; ms = {}; ce = Env(e)
            for m in n.methods: ms[m.name] = Func(m.name, m.params, m.body, ce)
            cls = Cls(n.name, pc, ms); e.set(n.name, cls); return cls
        if t == 'Return': raise Ret(self.ev(n.value, e))
        if t == 'Throw': raise Thr(self.ev(n.value, e))
        if t == 'Try':
            try:
                for s in n.body: self.ev(s, e)
            except Thr as th:
                ce = Env(e); ce.set(n.var, th.v)
                for s in n.catch: self.ev(s, ce)
        if t == 'If':
            if self.ev(n.cond, e):
                for s in n.then: self.ev(s, e)
            elif n.els:
                for s in n.els: self.ev(s, e)
        if t == 'While':
            while self.ev(n.cond, e):
                for s in n.body: self.ev(s, e)
        if t == 'For':
            for it in self.ev(n.iter, e):
                le = Env(e); le.set(n.var, it)
                for s in n.body: self.ev(s, le)
        return None
