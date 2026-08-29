import sys, os
sys.setrecursionlimit(20000)
from lexer import tokenize, KEYWORDS
from parser import Parser
from interpreter import Interp

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <file> | --repl | --vm <file> | --compile <file>")
        return
    if sys.argv[1] in ('--vm', '--compile'):
        from vm import Compiler, VM
        src = open(sys.argv[2]).read()
        code = Compiler().compile(Parser(tokenize(src)).parse())
        if sys.argv[1] == '--compile':
            for i, (op, arg) in enumerate(code): print(f"{i:04} {op} {arg if arg is not None else ''}")
            return
        VM(code).run(); return
    if sys.argv[1] == '--repl':
        interp = Interp()
        try:
            import readline
            def complete(text, state):
                opts = [w for w in KEYWORDS + interp.names() if w.startswith(text)]
                return opts[state] if state < len(opts) else None
            readline.set_completer(complete)
            readline.parse_and_bind("tab: complete")
        except Exception: pass
        print("SahajCore v4.0 REPL. Tab=complete, Up/Down=history, 'exit' to quit.")
        while True:
            line = input("sahajcore> ")
            if line.strip() == 'exit': break
            if not line.strip(): continue
            try:
                r = interp.run(Parser(tokenize(line)).parse())
                if r is not None: print(r)
            except Exception as e: print(f"Error: {e}")
        return
    src = open(sys.argv[1]).read()
    Interp().run(Parser(tokenize(src)).parse())

if __name__ == '__main__':
    main()
