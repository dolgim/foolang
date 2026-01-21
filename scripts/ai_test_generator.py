#!/usr/bin/env python3
"""AI-powered test generator using Claude Code SDK.

This script uses Claude to analyze the Foolang codebase, generate
edge case tests, and create a PR if issues are found.
"""

import asyncio
import os
from pathlib import Path

from claude_code_sdk import ClaudeCodeOptions, query


PROMPT = """
You are a test engineer for the Foolang compiler. Your task is to generate edge case tests and create a PR if issues are found.

## Instructions

1. **Analyze the codebase**
   - Read the source files in src/foolang/ to understand the implementation
   - Focus on: lexer.py, parser.py, optimizer.py, codegen.py

2. **Generate edge case tests**
   Create tests for scenarios that might break the compiler:

   **Lexer edge cases:**
   - Empty input, whitespace only
   - Very long strings or identifiers
   - Unicode characters in strings
   - Numbers at boundaries (very large, very small)

   **Parser edge cases:**
   - Deeply nested expressions: ((((1 + 2) + 3) + 4) + 5)
   - Empty function bodies
   - Functions with many parameters
   - Chained function calls: foo()()()

   **Optimizer edge cases:**
   - Division by zero in constant folding
   - Very long chains of operations
   - Mixed types in operations

   **CodeGen edge cases:**
   - JavaScript reserved words as identifiers
   - Special characters in strings that need escaping

3. **Write the tests**
   - Save to tests/test_generated.py
   - Use pytest style with descriptive test names
   - Include both "should work" and "should fail gracefully" tests

4. **Run the tests**
   - Execute: uv run pytest tests/test_generated.py -v
   - Analyze any failures

5. **Create a PR if there are changes**
   If you generated new tests or found issues:
   - Create a new branch: git checkout -b ai-generated-tests-$(date +%Y%m%d-%H%M%S)
   - Commit the changes with a descriptive message
   - Push the branch: git push -u origin HEAD
   - Create a PR using: gh pr create

   The PR title and body should be dynamically generated based on:
   - What tests were created
   - What edge cases were covered
   - Any bugs or issues discovered
   - Test results summary

   Make the PR description informative and actionable for reviewers.

6. **If no issues found**
   - Report that all edge cases passed
   - No PR needed if tests already exist and pass
"""


async def main():
    # Ensure we're in the project directory
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)

    print("=" * 60)
    print("AI Test Generator for Foolang")
    print("=" * 60)
    print()

    options = ClaudeCodeOptions(
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        max_budget_usd=5.0,
        cwd=str(project_dir),
    )

    async for message in query(prompt=PROMPT, options=options):
        print(message)

    print()
    print("=" * 60)
    print("AI Test Generation Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())