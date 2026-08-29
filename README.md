# SahajCore

A minimalist, dynamically-typed programming language with a **self-hosting interpreter** — an interpreter for SahajCore, written in SahajCore itself.

## Features
- Clean C/JS-like syntax: `let`, `fn`, `if/else`, `while`, `return`
- Data types: number, string, bool, list, dict, null
- First-class functions with closures & recursion
- Built-in self-hosting: `selfhost.sahaj` runs `target.sahaj`

## Run a program
```bash
python3 main.py hello.sahaj
```

## REPL
```bash
python3 main.py --repl
```

## Self-Hosting (Bootstrapping)
```bash
python3 main.py selfhost.sahaj
```
This runs the SahajCore interpreter (written in SahajCore) which then executes `target.sahaj`.

## Example
fn fib(n) {
if n < 2 { return n }
return fib(n - 1) + fib(n - 2)
}
let i = 0
while i < 10 {
print("fib(" + str(i) + ") = " + str(fib(i)))
i = i + 1
}
