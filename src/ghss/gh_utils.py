"""GitHub CLI utility functions."""

import subprocess

import typer


def run_gh_command(args: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a gh CLI command and return the result."""
    result = subprocess.run(
        ["gh"] + args,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        typer.echo(f"Error running gh command: {result.stderr}", err=True)
        raise typer.Exit(1)
    return result


def check_gh_auth() -> None:
    """Check if gh CLI is installed and authenticated."""
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        typer.echo("Error: gh CLI is not authenticated.", err=True)
        typer.echo("Please run 'gh auth login' to authenticate.", err=True)
        raise typer.Exit(1)


def get_current_repo() -> str:
    """Get the current repository in the format owner/repo."""
    result = run_gh_command(
        ["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
    )
    return result.stdout.strip()
