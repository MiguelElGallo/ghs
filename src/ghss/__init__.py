"""ghs - Sync your .env files with Github Secrets."""
from .commands import app


def main() -> None:
    app()
