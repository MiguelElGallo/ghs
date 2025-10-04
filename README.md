# ghss

[![Tests](https://github.com/MiguelElGallo/ghs/actions/workflows/tests.yml/badge.svg)](https://github.com/MiguelElGallo/ghs/actions/workflows/tests.yml)
[![Publish to PyPI](https://github.com/MiguelElGallo/ghs/actions/workflows/publish-to-pypi.yml/badge.svg)](https://github.com/MiguelElGallo/ghs/actions/workflows/publish-to-pypi.yml)

Sync your `.env` files with GitHub Repository Variables in both directions using a simple CLI tool.

![alt text](media/ghss.png)

## ⚠️ IMPORTANT SECURITY NOTICE

**This tool uses GitHub Repository Variables, NOT GitHub Secrets.**

- **Variables are NOT encrypted** and their values can be retrieved via the GitHub API
- **Repository collaborators may have access** to variable values depending on permissions
- **Do NOT store sensitive secrets** like API keys, passwords, or tokens using this tool
- For sensitive data, use GitHub Secrets directly or a proper secrets management solution

See [GitHub's documentation on configuration variables](https://docs.github.com/en/actions/learn-github-actions/variables#creating-configuration-variables-for-a-repository) for more information about security implications.

## What it does

`ghss` synchronizes environment variables between your local `.env` files and GitHub repository variables. You can push variables from your local environment to GitHub or pull variable names and values from GitHub to create a `.env` file.

### Typical Use Case

You start working on a new repository and create a `.env` file with all your configuration. Later, you move to another PC, clone your repo, and notice the `.env` file is missing (because it's gitignored). With `ghss`, you can:

1. **Push variables to GitHub** from your first PC: `uvx --refresh ghss set`
2. **Pull variables from GitHub** on your second PC: `uvx --refresh ghss get`
3. You're ready to work with your configuration restored

This leverages GitHub Repository Variables to store your environment configuration without committing data to your repository.

**Note:** This is suitable for non-sensitive configuration values. For sensitive data, use proper secrets management.

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

Test your configuration by creating, reading, and deleting a test variable in your repository.

**Usage:**
```bash
uvx --refresh ghss testconf
```

**Example output:**
```
Testing gh CLI authentication...
✓ gh CLI is authenticated
✓ Using repository: MiguelElGallo/ghs
Creating test variable: GHS_TEST_VARIABLE_abc12345...
✓ Test variable created
Verifying test variable exists...
Waiting 3 seconds before trying to get the variable...
✓ Test variable verified
✓ Test variable value verified
Deleting test variable...
✓ Test variable deleted
✓ All tests passed! Configuration is working correctly.
```

**Options:**
- `--help`: Show help message

---

### `get`

Get all variables from the repository and write them to a `.env` file with their values.

**Note:** Unlike GitHub Secrets, variable values CAN be retrieved from the API. The values will be written to your local `.env` file.

**⚠️ Security Warning:** Variable values are retrievable and may be visible to repository collaborators.

**Usage:**
```bash
uvx --refresh ghss get
uvx --refresh ghss get -f custom.env
```

**Example output:**
```
Checking gh CLI authentication...
Getting variables from repository: MiguelElGallo/ghs
Found 3 variable(s)
Writing variables to .env...
✓ Variables written to .env

⚠️  WARNING: Variable values are retrievable via API and may be visible to repository collaborators!
See https://docs.github.com/en/actions/learn-github-actions/variables#creating-configuration-variables-for-a-repository for more info.
```

**Options:**
- `-f, --file TEXT`: Output file path (default: `.env`)
- `--help`: Show help message

**Generated file format:**
```env
API_KEY=your_api_key_value
DATABASE_URL=postgres://localhost/db
APP_ENV=development
```

---

### `set`

Read a `.env` file and set the variables in the repository.

**⚠️ Security Warning:** All values will be stored as repository variables and may be accessible to collaborators. You will be prompted for confirmation before proceeding.

**Usage:**
```bash
uvx --refresh ghss set
uvx --refresh ghss set -f custom.env
```

**Example output:**
```
Checking gh CLI authentication...
Found 3 variable(s) to set in repository: MiguelElGallo/ghs

⚠️  WARNING: All values of your .env file will be set as variables of this repository.
Repository collaborators could have access to these values.
See https://docs.github.com/en/actions/learn-github-actions/variables#creating-configuration-variables-for-a-repository for more info.

Do you want to continue? [y/N]: y

Setting variables...
Setting variable: API_KEY...
Setting variable: DATABASE_URL...
Setting variable: APP_ENV...

✓ Successfully set 3 variable(s)
```

**Options:**
- `-f, --file TEXT`: Input file path (default: `.env`)
- `--help`: Show help message

**Input file format:**
```env
API_KEY=your_api_key_here
DATABASE_URL=postgres://user:pass@localhost/db
APP_ENV=development
```

---

## Example Workflow

**⚠️ Important:** This tool stores values as repository variables, not secrets. Only use it for non-sensitive configuration data.

1. **Initial setup on your main PC:**
   ```bash
   # Create your .env file with configuration
   echo "API_URL=https://api.example.com" >> .env
   echo "APP_ENV=development" >> .env
   
   # Test configuration
   uvx --refresh ghss testconf
   
   # Push variables to GitHub (you'll be prompted for confirmation)
   uvx --refresh ghss set
   ```

2. **On a different PC:**
   ```bash
   # Clone your repository
   git clone https://github.com/yourusername/yourrepo.git
   cd yourrepo
   
   # Pull variables from GitHub (values included!)
   uvx --refresh ghss get
   
   # You're ready to work!
   ```

## License

MIT
