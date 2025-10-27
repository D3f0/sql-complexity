"""
Command line interface
"""

import sys
from importlib import metadata

import click
from rich.console import Console
from rich.syntax import Syntax

from sql_complexity import SQLComplexityAssessment

out = Console()
err = Console(stderr=True)


@click.command()
@click.argument("user_input", type=click.File("r"), required=False, default="-")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose mode")
@click.option("-V", "--version", is_flag=True, help="Show version")
def main(user_input, verbose: bool, version: bool):
    """SQL Complexity assessment"""
    if version:
        out.print(metadata.version("sql-complexity"))
        sys.exit(0)
    if sys.stdin.isatty():
        err.print("[bold green]Running in interactive mode[/bold green]")
    contents = user_input.read().strip()
    if verbose:
        err.print(Syntax(contents, lexer="sql"))
    checker = SQLComplexityAssessment()
    score = checker.assess(contents)
    if verbose:
        out.print(score)
    out.print(score.total)
