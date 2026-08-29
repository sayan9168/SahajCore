import sys, os
sys.setrecursionlimit(20000)
from lexer import tokenize
from parser import Parser
from interpreter import Interp

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <file> | --repl | --vm <file> | --compile <file>")
        return
    if sys.argv[1] in ('--vm', '--compile'):
        from vm import Compiler, VM
        src = open(sys.argv[2]).read()
        ast = Parser(tokenize(src)).parse()
        code = Compiler().compile(ast)
        if sys.argv[1] == '--compile':
            for i, (op, arg) in enumerate(code):
                print(f"{i:04} {op} {arg if arg is not None else ''}")
            return
        VM(code).run()
        return
    if sys.argv[1] == '--repl':
        interp = Interp()
        print("SahajCore v3.0 REPL. Type 'exit'.")
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

main()
