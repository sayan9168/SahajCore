import sys, os
sys.setrecursionlimit(20000)
from lexer import tokenize
from parser import Parser
from interpreter import Interp
if len(sys.argv) < 2: print("Usage: python3 main.py <file>"); sys.exit()
src = open(sys.argv[1]).read()
Interp().run(Parser(tokenize(src)).parse())
