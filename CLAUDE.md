# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_lexer.py

# Run a specific test
uv run pytest tests/test_lexer.py::TestLexerBasics::test_empty_input

# Lint and format
uv run ruff check src tests
uv run ruff format src tests

# Compile a .foo file to JavaScript
uv run foolang compile examples/hello.foo -o output.js

# Compile without optimizations
uv run foolang compile examples/hello.foo -o output.js --no-optimize

# Run compiled JavaScript
node output.js
```

## Architecture

Foolang is a simple DSL that transpiles to JavaScript with compile-time optimizations.

### Compiler Pipeline

```
Source (.foo) → Lexer → Parser → Optimizer → CodeGen → JavaScript (.js)
```

### Module Overview

- [lexer.py](src/foolang/lexer.py) - Tokenizes source code into a token stream
- [ast.py](src/foolang/ast.py) - Defines AST node types using dataclasses and Visitor pattern
- [parser.py](src/foolang/parser.py) - Recursive descent parser that builds AST from tokens
- [optimizer.py](src/foolang/optimizer.py) - AST optimization passes (constant folding, dead code elimination)
- [codegen.py](src/foolang/codegen.py) - Generates JavaScript from optimized AST
- [cli.py](src/foolang/cli.py) - Command-line interface

### DSL Syntax

```
let x = 10              // variable declaration
fn add(a, b) { ... }    // function definition
return expr             // return statement
if (cond) { } else { }  // conditionals
print(x)                // maps to console.log
// comment              // single-line comments
```

### Optimization Passes

1. **Constant Folding** - Evaluates constant expressions at compile time (`1 + 2` → `3`)
2. **Dead Code Elimination** - Removes unused variables and functions

## CI/CD

### AI Test Generation

GitHub Actions workflow that uses Claude Code SDK to automatically generate edge case tests.

```bash
# Run locally (requires ANTHROPIC_API_KEY)
python scripts/ai_test_generator.py

# Run via GitHub Actions
# Go to Actions → AI Test Generation → Run workflow
```

The AI agent will:
1. Analyze the codebase
2. Generate edge case tests
3. Run tests and analyze failures
4. Create a PR with findings (if issues found)
