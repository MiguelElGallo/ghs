"""CLI command implementations."""

import json
import random
import string
import time

import typer
from typing_extensions import Annotated

from .env_utils import load_env_file, write_env_file
from .gh_utils import (
    check_gh_auth,
    get_current_repo,
    get_secret_info,
    get_variable_info,
    list_variables,
    run_gh_command,
)

app = typer.Typer(help="Sync your .env files with Github Secrets")


@app.command()
def testconf() -> None:
    """Test configuration by creating, reading, and deleting a test secret."""
    typer.echo("Testing gh CLI authentication...")
    check_gh_auth()
    typer.echo("✓ gh CLI is authenticated")

    repo = get_current_repo()
    typer.echo(f"✓ Using repository: {repo}")

    # Generate a random string for the test secret
    random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    secret_name = f"ghs_test_secret_{random_string}"
    secret_value = "test_value_12345"

    typer.echo(f"Creating test secret: {secret_name}...")
    result = run_gh_command(
        ["secret", "set", secret_name, "--body", secret_value, "--repo", repo]
    )
    typer.echo("✓ Test secret created")

    typer.echo("Verifying test secret exists...")
    typer.echo("Waiting 3 seconds before trying to get the secret...")

    time.sleep(3)
    result = run_gh_command(
        [
            "secret",
            "list",
            "--repo",
            repo,
            "--json",
            "name",
        ]
    )
    secrets = json.loads(result.stdout)
    typer.echo(f"Returned secrets: {secrets}")
    secret_names = [s["name"] for s in secrets]

    if secret_name.upper() not in secret_names:
        typer.echo("✗ Test secret not found in repository", err=True)
        raise typer.Exit(1)

    typer.echo("✓ Test secret verified")

    typer.echo("Deleting test secret...")
    result = run_gh_command(["secret", "delete", secret_name.upper(), "--repo", repo])
    typer.echo("✓ Test secret deleted")

    typer.echo("\n✓ All tests passed! Configuration is working correctly.")


@app.command()
def get(
    file: Annotated[
        str, typer.Option("-f", "--file", help="Output file path")
    ] = ".env",
) -> None:
    """Get all secrets from the repository and write them to a .env file."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()

    repo = get_current_repo()
    typer.echo(f"Getting secrets from repository: {repo}")

    result = run_gh_command(
        [
            "secret",
            "list",
            "--repo",
            repo,
            "--json",
            "name",
        ]
    )

    secrets = json.loads(result.stdout)

    if not secrets:
        typer.echo("No secrets found in repository.")
        return

    typer.echo(f"Found {len(secrets)} secret(s)")
    typer.echo("\nNote: Secret values cannot be retrieved from GitHub.")
    typer.echo(f"Writing secret names to {file}...")

    write_env_file(file, secrets)

    typer.echo(f"✓ Secret names written to {file}")
    typer.echo("\nPlease fill in the values manually.")


@app.command()
def set(
    file: Annotated[str, typer.Option("-f", "--file", help="Input file path")] = ".env",
) -> None:
    """Read a .env file and set the secrets in the repository."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()

    repo = get_current_repo()
    typer.echo(f"Setting secrets in repository: {repo}")

    secrets_to_set = load_env_file(file)

    if not secrets_to_set:
        typer.echo("No secrets found in .env file.")
        return

    typer.echo(f"Found {len(secrets_to_set)} secret(s) to set")

    for key, value in secrets_to_set.items():
        typer.echo(f"Setting secret: {key}...")
        result = run_gh_command(["secret", "set", key, "--body", value, "--repo", repo])

    typer.echo(f"\n✓ Successfully set {len(secrets_to_set)} secret(s)")


@app.command()
def get_secret(
    secret_name: Annotated[
        str, typer.Argument(help="Name of the secret to retrieve info for")
    ],
) -> None:
    """Get information about a specific secret (metadata only, not the actual value)."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()

    repo = get_current_repo()
    typer.echo(f"Getting secret info from repository: {repo}")

    try:
        secret_info = get_secret_info(repo, secret_name)

        typer.echo(f"\n✓ Secret '{secret_name}' found!")
        typer.echo(f"Name: {secret_info.get('name', 'N/A')}")
        typer.echo(f"Created at: {secret_info.get('created_at', 'N/A')}")
        typer.echo(f"Updated at: {secret_info.get('updated_at', 'N/A')}")

        # Note: The actual secret value is never returned by the API for security reasons
        typer.echo(
            "\nNote: The actual secret value cannot be retrieved via the API for security reasons."
        )

    except typer.Exit:
        typer.echo(f"✗ Secret '{secret_name}' not found or error occurred", err=True)
        raise


@app.command()
def get_variable(
    variable_name: Annotated[
        str, typer.Argument(help="Name of the variable to retrieve")
    ],
) -> None:
    """Get information about a specific repository variable (including the actual value)."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()

    repo = get_current_repo()
    typer.echo(f"Getting variable info from repository: {repo}")

    try:
        variable_info = get_variable_info(repo, variable_name)

        typer.echo(f"\n✓ Variable '{variable_name}' found!")
        typer.echo(f"Name: {variable_info.get('name', 'N/A')}")
        typer.echo(f"Value: {variable_info.get('value', 'N/A')}")
        typer.echo(f"Created at: {variable_info.get('created_at', 'N/A')}")
        typer.echo(f"Updated at: {variable_info.get('updated_at', 'N/A')}")

        typer.echo(
            "\n⚠️  WARNING: Variable values are retrievable via API and may be visible to repository collaborators!"
        )

    except typer.Exit:
        typer.echo(
            f"✗ Variable '{variable_name}' not found or error occurred", err=True
        )
        raise


@app.command()
def list_vars() -> None:
    """List all repository variables (including their actual values)."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()

    repo = get_current_repo()
    typer.echo(f"Getting variables from repository: {repo}")

    try:
        variables_data = list_variables(repo)
        variables = variables_data.get("variables", [])

        if not variables:
            typer.echo("No variables found in repository.")
            return

        typer.echo(f"\n✓ Found {len(variables)} variable(s):")

        for var in variables:
            typer.echo(f"\n  Name: {var.get('name', 'N/A')}")
            typer.echo(f"  Value: {var.get('value', 'N/A')}")
            typer.echo(f"  Created: {var.get('created_at', 'N/A')}")
            typer.echo(f"  Updated: {var.get('updated_at', 'N/A')}")

        typer.echo(
            "\n⚠️  WARNING: Variable values are retrievable via API and may be visible to repository collaborators!"
        )

    except typer.Exit:
        typer.echo("✗ Error retrieving variables", err=True)
        raise
