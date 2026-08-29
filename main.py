#!/usr/bin/env python3
import sys, os
sys.setrecursionlimit(50000)
sys.path.insert(0, os.path.dirname(__file__))

from lexer import tokenize
from parser import Parser
from interpreter import Interpreter

def main():
    if len(sys.argv) < 2:
        print("SahajCore Interpreter v1.0")
        print("Usage: sahajcore <file.sahaj>")
        print("       sahajcore --repl")
        return
    if sys.argv[1] == '--repl':
        interp = Interpreter()
        print("SahajCore REPL. Type 'exit' to quit.")
        while True:
            try:
                line = input("sahajcore> ")
                if line.strip() == 'exit': break
                if not line.strip(): continue
                tokens = tokenize(line)
                ast = Parser(tokens).parse()
                result = interp.run(ast)
                if result is not None:
                    print(result)
            except Exception as e:
                print(f"Error: {e}")
        return
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"File not found: {path}")
        sys.exit(1)
    source = open(path).read()
    tokens = tokenize(source)
    ast = Parser(tokens).parse()
    interp = Interpreter()
    interp.run(ast)

if __name__ == '__main__':
    main()
