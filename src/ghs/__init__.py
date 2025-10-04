import json
import subprocess
from pathlib import Path

import typer
from typing_extensions import Annotated

app = typer.Typer(help="Sync your .env files with Github Secrets")


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
    result = run_gh_command(["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"])
    return result.stdout.strip()


@app.command()
def testconf() -> None:
    """Test configuration by creating, reading, and deleting a test secret."""
    typer.echo("Testing gh CLI authentication...")
    check_gh_auth()
    typer.echo("✓ gh CLI is authenticated")
    
    repo = get_current_repo()
    typer.echo(f"✓ Using repository: {repo}")
    
    # Generate a random string for the test secret
    import random
    import string
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    secret_name = f"ghs_test_secret_{random_string}"
    secret_value = "test_value_12345"
    
    typer.echo(f"Creating test secret: {secret_name}...")
    result = run_gh_command([
        "secret", "set", secret_name,
        "--body", secret_value,
        "--repo", repo
    ])
    typer.echo(f"✓ Test secret created")
    
    typer.echo(f"Verifying test secret exists...")
    result = run_gh_command([
        "secret", "list",
        "--repo", repo,
        "--json", "name",
    ])
    secrets = json.loads(result.stdout)
    secret_names = [s["name"] for s in secrets]
    
    if secret_name not in secret_names:
        typer.echo(f"✗ Test secret not found in repository", err=True)
        raise typer.Exit(1)
    
    typer.echo(f"✓ Test secret verified")
    
    typer.echo(f"Deleting test secret...")
    result = run_gh_command([
        "secret", "delete", secret_name,
        "--repo", repo
    ])
    typer.echo(f"✓ Test secret deleted")
    
    typer.echo("\n✓ All tests passed! Configuration is working correctly.")


@app.command()
def get(
    file: Annotated[str, typer.Option("-f", "--file", help="Output file path")] = ".env"
) -> None:
    """Get all secrets from the repository and write them to a .env file."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()
    
    repo = get_current_repo()
    typer.echo(f"Getting secrets from repository: {repo}")
    
    result = run_gh_command([
        "secret", "list",
        "--repo", repo,
        "--json", "name",
    ])
    
    secrets = json.loads(result.stdout)
    
    if not secrets:
        typer.echo("No secrets found in repository.")
        return
    
    typer.echo(f"Found {len(secrets)} secret(s)")
    typer.echo(f"\nNote: Secret values cannot be retrieved from GitHub.")
    typer.echo(f"Writing secret names to {file}...")
    
    output_path = Path(file)
    with output_path.open("w") as f:
        for secret in secrets:
            f.write(f"{secret['name']}=\n")
    
    typer.echo(f"✓ Secret names written to {file}")
    typer.echo(f"\nPlease fill in the values manually.")


@app.command()
def set(
    file: Annotated[str, typer.Option("-f", "--file", help="Input file path")] = ".env"
) -> None:
    """Read a .env file and set the secrets in the repository."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()
    
    repo = get_current_repo()
    typer.echo(f"Setting secrets in repository: {repo}")
    
    env_path = Path(file)
    if not env_path.exists():
        typer.echo(f"Error: File {file} not found.", err=True)
        raise typer.Exit(1)
    
    secrets_to_set = {}
    with env_path.open("r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            if "=" not in line:
                typer.echo(f"Warning: Skipping invalid line {line_num}: {line}", err=True)
                continue
            
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            if not key:
                typer.echo(f"Warning: Skipping line {line_num} with empty key", err=True)
                continue
            
            secrets_to_set[key] = value
    
    if not secrets_to_set:
        typer.echo("No secrets found in .env file.")
        return
    
    typer.echo(f"Found {len(secrets_to_set)} secret(s) to set")
    
    for key, value in secrets_to_set.items():
        typer.echo(f"Setting secret: {key}...")
        result = run_gh_command([
            "secret", "set", key,
            "--body", value,
            "--repo", repo
        ])
    
    typer.echo(f"\n✓ Successfully set {len(secrets_to_set)} secret(s)")


def main() -> None:
    app()
