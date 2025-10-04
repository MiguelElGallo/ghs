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
    delete_variable,
    get_current_repo,
    get_variable_info,
    list_variables,
    run_gh_command,
    set_variable,
)

app = typer.Typer(help="Sync your .env files with Github Repository Variables")


@app.command()
def testconf() -> None:
    """Test configuration by creating, reading, and deleting a test variable."""
    typer.echo("Testing gh CLI authentication...")
    check_gh_auth()
    typer.echo("✓ gh CLI is authenticated")

    repo = get_current_repo()
    typer.echo(f"✓ Using repository: {repo}")

    # Generate a random string for the test variable
    random_string = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    variable_name = f"GHS_TEST_VARIABLE_{random_string}"
    variable_value = "test_value_12345"

    typer.echo(f"Creating test variable: {variable_name}...")
    set_variable(repo, variable_name, variable_value)
    typer.echo("✓ Test variable created")

    typer.echo("Verifying test variable exists...")
    typer.echo("Waiting 3 seconds before trying to get the variable...")

    time.sleep(3)
    
    variables_data = list_variables(repo)
    variables = variables_data.get("variables", [])
    variable_names = [v["name"] for v in variables]

    if variable_name.upper() not in variable_names:
        typer.echo("✗ Test variable not found in repository", err=True)
        raise typer.Exit(1)

    typer.echo("✓ Test variable verified")
    
    # Verify we can read the value
    variable_info = get_variable_info(repo, variable_name)
    if variable_info.get("value") != variable_value:
        typer.echo("✗ Test variable value mismatch", err=True)
        raise typer.Exit(1)
    
    typer.echo("✓ Test variable value verified")

    typer.echo("Deleting test variable...")
    delete_variable(repo, variable_name)
    typer.echo("✓ Test variable deleted")

    typer.echo("\n✓ All tests passed! Configuration is working correctly.")


@app.command()
def get(
    file: Annotated[
        str, typer.Option("-f", "--file", help="Output file path")
    ] = ".env",
) -> None:
    """Get all variables from the repository and write them to a .env file."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()

    repo = get_current_repo()
    typer.echo(f"Getting variables from repository: {repo}")

    variables_data = list_variables(repo)
    variables = variables_data.get("variables", [])

    if not variables:
        typer.echo("No variables found in repository.")
        return

    typer.echo(f"Found {len(variables)} variable(s)")
    typer.echo(f"Writing variables to {file}...")

    write_env_file(file, variables)

    typer.echo(f"✓ Variables written to {file}")
    typer.echo(
        "\n⚠️  WARNING: Variable values are retrievable via API and may be visible to repository collaborators!"
    )
    typer.echo(
        "See https://docs.github.com/en/actions/learn-github-actions/variables#creating-configuration-variables-for-a-repository for more info."
    )


@app.command()
def set(
    file: Annotated[str, typer.Option("-f", "--file", help="Input file path")] = ".env",
) -> None:
    """Read a .env file and set the variables in the repository."""
    typer.echo("Checking gh CLI authentication...")
    check_gh_auth()

    repo = get_current_repo()
    
    variables_to_set = load_env_file(file)

    if not variables_to_set:
        typer.echo("No variables found in .env file.")
        return

    typer.echo(f"Found {len(variables_to_set)} variable(s) to set in repository: {repo}")
    
    # Display warning and ask for confirmation
    typer.echo("\n⚠️  WARNING: All values of your .env file will be set as variables of this repository.")
    typer.echo("Repository collaborators could have access to these values.")
    typer.echo(
        "See https://docs.github.com/en/actions/learn-github-actions/variables#creating-configuration-variables-for-a-repository for more info."
    )
    
    confirmation = typer.confirm("\nDo you want to continue?", default=False)
    
    if not confirmation:
        typer.echo("Operation cancelled.")
        raise typer.Exit(0)

    typer.echo("\nSetting variables...")
    for key, value in variables_to_set.items():
        typer.echo(f"Setting variable: {key}...")
        set_variable(repo, key, value)

    typer.echo(f"\n✓ Successfully set {len(variables_to_set)} variable(s)")


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
