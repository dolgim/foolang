# Foolang

A simple DSL that transpiles to JavaScript with compile-time optimizations.

## Installation

```bash
uv sync
```

## Usage

```bash
# Compile a .foo file to JavaScript
uv run foolang compile examples/hello.foo -o output.js

# Run the compiled JavaScript
node output.js
```

## Example

```
// hello.foo
let x = 1 + 2 * 3

fn add(a, b) {
    return a + b
}

print(add(10, 20))
print(x)
```

Compiles to:

```javascript
let x = 7;
function add(a, b) {
  return (a + b);
}
console.log(add(10, 20));
console.log(x);
```

## Optimizations

- **Constant Folding**: `1 + 2 * 3` → `7`
- **Dead Code Elimination**: Unused variables and functions are removed
