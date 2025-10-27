#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "invoke-toolkit",
# ]
# ///

# pylint: skip-file
"""
Automation tasks, run this script with uv run tasks.py
"""

import re
from shutil import which
import subprocess
import sys
from pathlib import Path

from rich.prompt import Prompt

from invoke_toolkit import Context, task, script
from invoke.util import debug

try:
    REPO_ROOT = Path(
        subprocess.check_output("git rev-parse --show-toplevel", shell=True)
        .strip()
        .decode()
    )
except subprocess.SubprocessError:
    REPO_ROOT = Path()


@task()
def clean(ctx: Context):
    """Cleans dist"""
    with ctx.cd(REPO_ROOT):
        ctx.run(r"rm -rf ./dist/*.{tar.gz,whl}")


@task(
    help={
        "target_": "Target format",
        "output": "Output directory, by default is ./dist/",
    },
    autoprint=True,
    pre=[clean],
)
def build(ctx: Context, target_=[], output="./dist/"):  # pylint: disable=dangerous-default-value
    """Builds distributable package"""
    with ctx.cd(REPO_ROOT):
        ctx.run("uv build")


@task()
def show_package_files(ctx: Context, file_type="whl"):
    """Shows the contents of the latest package"""
    with ctx.cd(REPO_ROOT / "dist"):
        ls = ctx.run(f"ls -t *.{file_type}", warn=True, echo=ctx.config.run.echo)
        if not ls.ok:
            ctx.rich_exit(
                f"Couldn't find any package files of type [red]{file_type}[/red]"
            )
        newest_pkg, *_ = ls.stdout.splitlines()
        ctx.run(f"tar tvf {newest_pkg}")


@task(
    aliases=["t"],
    help={
        "debug": "Uses [green]pdb[pp][/green] to debug tests, use [bold]sticky[/bold]",
        "verbose": "Run in verbose mode, shows output to stdout",
        "capture_output": "Do not capture output",
        "picked": "Run only changed tests in git",
        "fzf": "Uses fuzzy finder to select which tests to run",
    },
)
def test(
    ctx: Context,
    debug_=False,
    verbose=False,
    capture_output=True,
    picked=False,
    keyword: list[str] = [],
    last_failed: bool = False,
    fzf: bool = False,
    html: bool = False,
):
    """Runs [green]pytest[/green] and exposes some commonly used flags"""
    with ctx.cd(REPO_ROOT):
        args = ""
        if debug_:
            args = f"{args} --pdb"
        if verbose:
            args = f"{args} -v"
        if not capture_output:
            args = f"{args} -s"
        # Run on tests of changed files
        if picked:
            args = f"{args} --picked"
        if keyword:
            kw = " ".join(f"-k {kw}" for kw in keyword)
            args = f"{args} {kw}"
        if last_failed:
            args = f"{args} --last-failed"
        if html:
            # addopts = "--html=report.html --self-contained-html"
            args = f"{args} --html=report.html --self-contained-html"
        if fzf:
            # Select the tests with fzf
            if not which("fzf"):
                ctx.rich_exit("[bold]fzf[/bold] not found")
            if which("bat"):
                debug("Running with bat")
                preview_cmd = r"bat --color always {}"
            else:
                debug("Preview with cat")
                preview_cmd = r"cat {}"
            test_to_run = ctx.run(
                f"""
                find ./tests/ -name 'test_*.py' | fzf --preview '{preview_cmd}'
                """
            ).stdout.strip()
            if not test_to_run:
                ctx.rich_exit("No tests selected 😭")
            else:
                args = f"{args} {test_to_run}"

        run = ctx.run(f"uv run pytest {args}", pty=True, warn=True)
        if html:
            ctx.run("test -f report.html && open report.html")
        if not run.ok:
            ctx.rich_exit("test failed", exit_code=run.return_code)


@task()
def release(ctx: Context, skip_sync: bool = False) -> None:
    """
    Tags (if the git repo is [bold]clean[/bold]) proposing the next tag
    Pushes the tag to [bold]github[/bold]
    Creates a release
    """
    if not skip_sync:
        with ctx.status("Syncing tags 🏷️ "):
            ctx.run("git fetch --tags")

    with ctx.status("Getting existing tags 👀 "):
        git_status = ctx.run(
            "git status --porcelain ", warn=True, hide=not ctx.config.run.echo
        )
    if git_status.stdout:
        sys.exit(f"The repo has changes: \n{git_status.stdout}")
    tags = [
        tag.strip("v")
        for tag in ctx.run(
            # "git tag --sort=-creatordate",
            "git tag --sort=-creatordate | sed -e 's/^v//g' | sort -r",
            hide=not ctx.config.run.echo,
        ).stdout.splitlines()
    ]

    def compare(dotted_version: str) -> tuple[int, int, int]:
        major, minor, patch, *_ = dotted_version.split(".")
        return int(major), int(minor), int(patch)

    tags.sort(key=compare, reverse=True)

    most_recent_tag, *_rest = tags
    major_minor, patch = most_recent_tag.rsplit(".", maxsplit=1)
    patch_integer = int(patch) + 1
    next_tag_version = f"v{major_minor}.{patch_integer}"

    while True:
        try:
            user_input = Prompt.ask(
                f"New tag [blue]{next_tag_version}[/blue] "
                "[bold]Ctrl-C[/bold]/[bold]Ctrl-D[/bold] to cancel? "
            )
        except EOFError:
            sys.exit("User cancelled")
        if not user_input:
            break
        if re.match(r"v?\d\.\d+\.\d+", user_input):
            break

    ctx.print("[blue]Creating tag...")
    ctx.run(f"git tag {next_tag_version}")
    ctx.run("git push origin --tags")
    ctx.print("[blue]Pushing tag...[/blue]")
    ctx.print("[bold]OK[/bold]")
    clean(ctx)
    build(ctx, target_="wheel")

    ctx.print("Creating the release on github")

    subprocess.run(
        f"gh release create {next_tag_version} ./dist/*.whl",
        shell=True,
        check=True,
    )


@task(pre=[clean, build])
def publish(ctx: Context):
    """
    Build and publish to PyPI using a token.

    [red]TODO:[/red] This should be a github action with trusted publishing
    """
    ctx.run(
        """
        test -n PYPI_PASSWORD && uv publish -t $PYPI_PASSWORD
        """
    )


@task()
def env(ctx: Context, clear=False) -> None:
    """([green]re[/green])creates the virtual environment (with [red]uv[/red])"""
    args = ""
    if clear:
        args = f"{args} --clear"
    ctx.run(f"uv venv {args}; uv sync --group dev", pty=True)


script()
