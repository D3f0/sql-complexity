import sys

import click
from rich.console import Console
from rich.syntax import Syntax

from sql_complexity import SQLComplexityAssessment

out = Console()
err = Console(stderr=True)


@click.command()
@click.argument("input", type=click.File("r"), required=False, default="-")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose mode")
def main(input, verbose: bool):
    """SQL Complexity assessment"""
    if sys.stdin.isatty():
        err.print("[bold green]Running in interactive mode[/bold green]")
    contents = input.read().strip()
    if verbose:
        err.print(Syntax(contents, lexer="sql"))
    checker = SQLComplexityAssessment()
    score = checker.assess(contents)
    if verbose:
        out.print(score)
    print(score.total)
