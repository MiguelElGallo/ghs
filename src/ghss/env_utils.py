"""Environment file utility functions."""
from pathlib import Path

import typer
from dotenv import dotenv_values


def load_env_file(file: str) -> dict[str, str]:
    """Load secrets from a .env file using python-dotenv.
    
    Args:
        file: Path to the .env file
        
    Returns:
        Dictionary of environment variables (keys and values)
        
    Raises:
        typer.Exit: If the file is not found
    """
    env_path = Path(file)
    if not env_path.exists():
        typer.echo(f"Error: File {file} not found.", err=True)
        raise typer.Exit(1)
    
    secrets = dotenv_values(env_path)
    
    # Filter out None values, empty keys, and empty values
    return {k: v for k, v in secrets.items() if k and v}


def write_env_file(file: str, variables: list[dict[str, str]]) -> None:
    """Write variable names and values to a .env file.
    
    Args:
        file: Path to the output .env file
        variables: List of variable dictionaries with 'name' and 'value' keys
    """
    output_path = Path(file)
    with output_path.open("w") as f:
        for var in variables:
            name = var.get('name', '')
            value = var.get('value', '')
            f.write(f"{name}={value}\n")
