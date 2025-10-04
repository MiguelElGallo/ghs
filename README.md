# ghss

[![Tests](https://github.com/MiguelElGallo/ghs/actions/workflows/tests.yml/badge.svg)](https://github.com/MiguelElGallo/ghs/actions/workflows/tests.yml)
[![Publish to PyPI](https://github.com/MiguelElGallo/ghs/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/MiguelElGallo/ghs/actions/workflows/publish-to-pypi.yml)

Sync your `.env` files with GitHub Secrets in both directions using a simple CLI tool.

## What it does

`ghss` synchronizes environment variables between your local `.env` files and GitHub repository secrets. You can push secrets from your local environment to GitHub or pull secret names from GitHub to create a template `.env` file.

### Typical Use Case

You start working on a new repository and create a `.env` file with all your configuration. Later, you move to another PC, clone your repo, and notice the `.env` file is missing (because it's gitignored). With `ghss`, you can:

1. **Push secrets to GitHub** from your first PC: `uvx --refresh ghss set`
2. **Pull secret names from GitHub** on your second PC: `uvx --refresh ghss get`
3. Fill in the values and you're ready to work

This leverages GitHub Secrets to safely store your environment configuration without committing sensitive data to your repository.

## Installation

**No installation required!** Just run the tool directly using `uvx`:

```bash
uvx --refresh ghss [command]
```

The `--refresh` flag ensures you're always running the latest version.

## Prerequisites

`ghss` requires the [GitHub CLI (`gh`)](https://cli.github.com/) to be installed and authenticated. This is typically already set up if you work with GitHub repositories.

To check if you're authenticated:

```bash
gh auth status
```

If not authenticated, run:

```bash
gh auth login
```

## Commands

### `testconf`

Test your configuration by creating, reading, and deleting a test secret in your repository.

**Usage:**
```bash
uvx --refresh ghss testconf
```

**Example output:**
```
Testing gh CLI authentication...
✓ gh CLI is authenticated
✓ Using repository: MiguelElGallo/ghs
Creating test secret: ghs_test_secret_abc12345...
✓ Test secret created
Verifying test secret exists...
Waiting 3 seconds before trying to get the secret...
✓ Test secret found in repository
Deleting test secret...
✓ Test secret deleted
✓ All tests passed successfully
```

**Options:**
- `--help`: Show help message

---

### `get`

Get all secret names from the repository and write them to a `.env` file.

**Note:** GitHub Secrets API does not allow retrieving secret values for security reasons. This command only retrieves secret names and creates a template file where you need to fill in the values manually.

**Usage:**
```bash
uvx --refresh ghss get
uvx --refresh ghss get -f custom.env
```

**Example output:**
```
Checking gh CLI authentication...
Getting secrets from repository: MiguelElGallo/ghs
Found 3 secret(s)

Note: Secret values cannot be retrieved from GitHub.
Writing secret names to .env...
✓ Secret names written to .env

Please fill in the values manually.
```

**Options:**
- `-f, --file TEXT`: Output file path (default: `.env`)
- `--help`: Show help message

**Generated file format:**
```env
API_KEY=
DATABASE_URL=
SECRET_TOKEN=
```

---

### `set`

Read a `.env` file and set the secrets in the repository.

**Usage:**
```bash
uvx --refresh ghss set
uvx --refresh ghss set -f custom.env
```

**Example output:**
```
Checking gh CLI authentication...
Setting secrets in repository: MiguelElGallo/ghs
Found 3 secret(s) to set
Setting secret: API_KEY...
Setting secret: DATABASE_URL...
Setting secret: SECRET_TOKEN...

✓ Successfully set 3 secret(s)
```

**Options:**
- `-f, --file TEXT`: Input file path (default: `.env`)
- `--help`: Show help message

**Input file format:**
```env
API_KEY=your_api_key_here
DATABASE_URL=postgres://user:pass@localhost/db
SECRET_TOKEN=secret123
```

---

## Example Workflow

1. **Initial setup on your main PC:**
   ```bash
   # Create your .env file with secrets
   echo "API_KEY=secret123" >> .env
   echo "DATABASE_URL=postgres://localhost/db" >> .env
   
   # Test configuration
   uvx --refresh ghss testconf
   
   # Push secrets to GitHub
   uvx --refresh ghss set
   ```

2. **On a different PC:**
   ```bash
   # Clone your repository
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo
   
   # Pull secret names from GitHub
   uvx --refresh ghss get
   
   # Edit .env and fill in the values
   nano .env
   
   # You're ready to work!
   ```

## License

MIT
