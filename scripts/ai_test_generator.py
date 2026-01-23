#!/usr/bin/env python3
"""AI-powered test generator using Claude Code SDK.

This script uses Claude to analyze the Foolang codebase, generate
edge case tests, run them, and create a GitHub Issue if failures are found.
Tests are NOT committed - only failures are reported.
"""

import asyncio
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from claude_code_sdk import (
    AssistantMessage,
    ClaudeCodeOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    query,
)


@dataclass
class TestReport:
    """Collects data for the final report."""

    analyzed_files: list[str] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    test_output: str = ""
    passed_count: int = 0
    failed_count: int = 0
    failed_tests: list[dict] = field(default_factory=list)
    cost_usd: float | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    num_turns: int = 0
    duration_ms: int = 0


# Configuration via environment variables
MAX_TESTS_PER_MODULE = int(os.environ.get("MAX_TESTS_PER_MODULE", "5"))


def get_prompt() -> str:
    """Generate prompt with configurable test count."""
    return f"""
You are a test engineer for the Foolang compiler. Your task is to generate edge case tests and report any failures.

## IMPORTANT RULES
- Generate tests in a TEMPORARY file: /tmp/test_foolang_edge_cases.py
- DO NOT commit or push anything
- DO NOT create branches or PRs
- Only run tests and report results

## Instructions

1. **Analyze the codebase**
   - Read the source files in src/foolang/ to understand the implementation
   - Focus on: lexer.py, parser.py, optimizer.py, codegen.py
   - Print a list of analyzed files with line counts

2. **Generate edge case tests** (MAX {MAX_TESTS_PER_MODULE} per module, ~{MAX_TESTS_PER_MODULE * 4} total)
   Create tests for scenarios that might break the compiler:

   **Lexer edge cases (max {MAX_TESTS_PER_MODULE}):**
   - Empty input, whitespace only
   - Very long strings or identifiers
   - Unicode characters in strings

   **Parser edge cases (max {MAX_TESTS_PER_MODULE}):**
   - Deeply nested expressions
   - Empty function bodies
   - Edge cases in syntax

   **Optimizer edge cases (max {MAX_TESTS_PER_MODULE}):**
   - Division by zero in constant folding
   - Complex constant expressions

   **CodeGen edge cases (max {MAX_TESTS_PER_MODULE}):**
   - JavaScript reserved words as identifiers
   - Special characters in strings

3. **Write the tests**
   - Save to /tmp/test_foolang_edge_cases.py
   - Use pytest style with descriptive test names
   - Include both "should work" and "should fail gracefully" tests

4. **Run the tests**
   - Execute: uv run pytest /tmp/test_foolang_edge_cases.py -v
   - Capture the full output

5. **Report results**
   Print a structured summary:
   - Total tests: N
   - Passed: N
   - Failed: N
   - For each failure, include:
     - Test name
     - Input that caused the failure
     - Expected behavior
     - Actual error/behavior
"""


def get_actions_url() -> str:
    """Get the GitHub Actions run URL if running in CI."""
    if os.environ.get("GITHUB_ACTIONS"):
        server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        run_id = os.environ.get("GITHUB_RUN_ID", "")
        return f"{server}/{repo}/actions/runs/{run_id}"
    return "(local run)"


def print_report(report: TestReport) -> None:
    """Print the final structured report."""
    print()
    print("=" * 60)
    print("AI Test Generation Report")
    print("=" * 60)
    print()

    # Analyzed files
    if report.analyzed_files:
        print("Analyzed files:")
        for f in report.analyzed_files:
            print(f"  - {f}")
        print()

    # Tool usage summary
    tool_counts: dict[str, int] = {}
    for tc in report.tool_calls:
        name = tc.get("name", "unknown")
        tool_counts[name] = tool_counts.get(name, 0) + 1
    if tool_counts:
        print("Tool usage:")
        for name, count in sorted(tool_counts.items()):
            print(f"  - {name}: {count} calls")
        print()

    # Test results
    print("Test results:")
    print(f"  - Total: {report.passed_count + report.failed_count}")
    print(f"  - Passed: {report.passed_count}")
    print(f"  - Failed: {report.failed_count}")
    print()

    # Failed tests detail
    if report.failed_tests:
        print("Failed tests:")
        for i, test in enumerate(report.failed_tests, 1):
            print(f"  {i}. {test.get('name', 'unknown')}")
            if test.get("input"):
                print(f"     Input: {test['input']}")
            if test.get("error"):
                print(f"     Error: {test['error']}")
        print()

    # Usage stats
    print("Usage:")
    if report.cost_usd is not None:
        print(f"  - Cost: ${report.cost_usd:.4f}")
    print(f"  - Tokens: {report.input_tokens + report.output_tokens:,} "
          f"(input: {report.input_tokens:,} / output: {report.output_tokens:,})")
    print(f"  - Turns: {report.num_turns}")
    print(f"  - Duration: {report.duration_ms / 1000:.1f}s")
    print()

    # Actions link
    actions_url = get_actions_url()
    print(f"Actions log: {actions_url}")
    print()


def create_github_issue(report: TestReport) -> bool:
    """Create a GitHub Issue for failed tests. Returns True if created."""
    if report.failed_count == 0:
        return False

    actions_url = get_actions_url()

    # Build issue body
    body_lines = [
        "## AI Test Failure Report",
        "",
        f"**Actions log**: [{actions_url}]({actions_url})",
        "",
        "### Failed Tests",
        "",
    ]

    for i, test in enumerate(report.failed_tests, 1):
        body_lines.append(f"{i}. **{test.get('name', 'unknown')}**")
        if test.get("input"):
            body_lines.append(f"   - Input: `{test['input']}`")
        if test.get("error"):
            body_lines.append(f"   - Error: `{test['error']}`")
        body_lines.append("")

    body_lines.extend([
        "### Usage",
        f"- Cost: ${report.cost_usd:.4f}" if report.cost_usd else "- Cost: N/A",
        f"- Tokens: {report.input_tokens + report.output_tokens:,}",
        "",
        "---",
        "*This issue was automatically created by the AI test generator.*",
    ])

    body = "\n".join(body_lines)
    title = f"AI Test Failure: {report.failed_count} edge case(s) failed"

    try:
        result = subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body],
            capture_output=True,
            text=True,
            check=True,
        )
        print(f"GitHub Issue created: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to create GitHub Issue: {e.stderr}")
        return False
    except FileNotFoundError:
        print("gh CLI not found, skipping issue creation")
        return False


def parse_test_output(output: str, report: TestReport) -> None:
    """Parse pytest output to extract pass/fail counts."""
    import re

    # Look for summary line like "5 passed, 2 failed" or "20 passed"
    # Match patterns: "20 passed", "5 passed, 2 failed", etc.
    passed_match = re.search(r"(\d+)\s+passed", output, re.IGNORECASE)
    failed_match = re.search(r"(\d+)\s+failed", output, re.IGNORECASE)

    if passed_match:
        report.passed_count = int(passed_match.group(1))
    if failed_match:
        report.failed_count = int(failed_match.group(1))

    # Extract failed test names
    for line in output.split("\n"):
        if "FAILED" in line and "::" in line:
            # Line like "FAILED test_file.py::test_name - Error"
            parts = line.split("::")
            if len(parts) >= 2:
                test_name = parts[1].split()[0] if parts[1] else "unknown"
                error = line.split(" - ")[-1] if " - " in line else ""
                report.failed_tests.append({"name": test_name, "error": error})


async def main() -> None:
    """Main entry point."""
    project_dir = Path(__file__).parent.parent
    os.chdir(project_dir)

    print("=" * 60)
    print("AI Test Generator for Foolang")
    print("=" * 60)
    print(f"Model: claude-haiku-4-5")
    print(f"Max turns: 30")
    print(f"Max tests per module: {MAX_TESTS_PER_MODULE} (set MAX_TESTS_PER_MODULE env to change)")
    print()

    report = TestReport()

    options = ClaudeCodeOptions(
        model="claude-haiku-4-5",
        allowed_tools=["Read", "Write", "Edit", "Bash", "Glob", "Grep"],
        permission_mode="bypassPermissions",
        max_turns=30,
        cwd=str(project_dir),
    )

    print("Starting AI agent...")
    print("-" * 60)

    async for message in query(prompt=get_prompt(), options=options):
        # Process different message types
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    # Print AI text responses
                    print(f"[AI] {block.text[:200]}..." if len(block.text) > 200 else f"[AI] {block.text}")
                    # Also try to parse test results from AI's text output
                    if "passed" in block.text.lower():
                        parse_test_output(block.text, report)
                elif isinstance(block, ToolUseBlock):
                    # Track tool calls
                    report.tool_calls.append({
                        "name": block.name,
                        "input": block.input,
                    })
                    # Track file reads for "analyzed files"
                    if block.name == "Read" and "file_path" in block.input:
                        file_path = block.input["file_path"]
                        if "src/foolang" in file_path:
                            report.analyzed_files.append(file_path)
                    print(f"[Tool] {block.name}: {str(block.input)[:100]}...")
                elif isinstance(block, ToolResultBlock):
                    # Check for test output
                    content = str(block.content) if block.content else ""
                    if "pytest" in content.lower() or "passed" in content.lower():
                        report.test_output = content
                        parse_test_output(content, report)

        elif isinstance(message, ResultMessage):
            # Extract final usage stats
            report.cost_usd = message.total_cost_usd
            report.num_turns = message.num_turns
            report.duration_ms = message.duration_ms
            if message.usage:
                report.input_tokens = message.usage.get("input_tokens", 0)
                report.output_tokens = message.usage.get("output_tokens", 0)

    print("-" * 60)

    # Print structured report
    print_report(report)

    # Create GitHub issue if there are failures
    if report.failed_count > 0:
        print("Creating GitHub Issue for failures...")
        create_github_issue(report)
    else:
        print("All tests passed! No issue created.")

    print("=" * 60)
    print("AI Test Generation Complete")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
