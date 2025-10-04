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


def get_secret_info(repo: str, secret_name: str) -> dict:
    """Get secret information using GitHub API (metadata only, not the actual value)."""
    result = run_gh_command(
        [
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            f"/repos/{repo}/actions/secrets/{secret_name}",
        ]
    )

    import json

    return json.loads(result.stdout)


def get_variable_info(repo: str, variable_name: str) -> dict:
    """Get repository variable information using GitHub API (includes the actual value)."""
    result = run_gh_command(
        [
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            f"/repos/{repo}/actions/variables/{variable_name}",
        ]
    )

    import json

    return json.loads(result.stdout)


def list_variables(repo: str) -> dict:
    """List all repository variables using GitHub API (includes the actual values)."""
    result = run_gh_command(
        [
            "api",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            f"/repos/{repo}/actions/variables",
        ]
    )

    import json

    return json.loads(result.stdout)
