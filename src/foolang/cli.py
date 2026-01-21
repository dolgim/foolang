"""CLI for Foolang compiler."""

import argparse
import sys
from pathlib import Path

from foolang.codegen import CodeGenerator
from foolang.lexer import Lexer, LexerError
from foolang.optimizer import Optimizer
from foolang.parser import ParseError, Parser


def compile_source(source: str, optimize: bool = True) -> str:
    """Compile Foolang source to JavaScript."""
    # Lexer
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    # Parser
    parser = Parser(tokens)
    ast = parser.parse()

    # Optimizer
    if optimize:
        optimizer = Optimizer()
        ast = optimizer.optimize(ast)

    # Code Generator
    codegen = CodeGenerator()
    return codegen.generate(ast)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="foolang",
        description="Foolang - A simple DSL that transpiles to JavaScript",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compile command
    compile_parser = subparsers.add_parser("compile", help="Compile a .foo file to JavaScript")
    compile_parser.add_argument("input", type=str, help="Input .foo file")
    compile_parser.add_argument("-o", "--output", type=str, help="Output .js file")
    compile_parser.add_argument(
        "--no-optimize", action="store_true", help="Disable optimizations"
    )

    args = parser.parse_args()

    if args.command == "compile":
        return compile_command(args)

    return 0


def compile_command(args) -> int:
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        return 1

    try:
        source = input_path.read_text()
        js_code = compile_source(source, optimize=not args.no_optimize)

        if args.output:
            output_path = Path(args.output)
            output_path.write_text(js_code)
            print(f"Compiled {input_path} -> {output_path}")
        else:
            print(js_code)

        return 0

    except LexerError as e:
        print(f"Lexer error: {e}", file=sys.stderr)
        return 1

    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
