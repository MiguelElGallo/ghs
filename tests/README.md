# Tests for ghs

This directory contains comprehensive tests for the ghs CLI tool, including both unit tests and end-to-end (E2E) tests.

## Test Structure

- `test_env_utils.py` - Unit tests for environment file utilities
- `test_gh_utils.py` - Unit tests for GitHub CLI utilities
- `test_commands.py` - Unit tests for CLI commands
- `test_e2e.py` - End-to-end tests that interact with actual GitHub repositories

## Running Tests

### Install Dependencies

First, install the project with dev dependencies:

```bash
uv sync --extra dev
```

### Run All Unit Tests

To run only unit tests (excluding E2E tests):

```bash
uv run pytest tests/ -v -m "not e2e"
```

### Run E2E Tests

E2E tests require:
- `gh` CLI to be installed and authenticated (`gh auth login`)
- Access to a GitHub repository
- Permission to create and delete secrets in that repository

To run E2E tests:

```bash
uv run pytest tests/ -v -m "e2e"
```

### Run All Tests

To run all tests (unit + E2E):

```bash
uv run pytest tests/ -v
```

Note: E2E tests will be automatically skipped if `gh` CLI is not authenticated.

## Unit Tests

Unit tests mock all IO operations and test all possible responses:
- Success cases
- Failure cases
- Edge cases (empty files, missing files, etc.)

All external dependencies (subprocess calls, file operations) are mocked using `pytest-mock`.

## E2E Tests

E2E tests use the actual `.env` file and GitHub CLI to:
1. Set secrets from a test `.env` file
2. Retrieve secrets from GitHub
3. Compare retrieved secret names with the original ones

These tests verify the complete workflow end-to-end.

## Test Coverage

The tests cover:
- ✅ Environment file loading and writing
- ✅ GitHub CLI command execution
- ✅ Authentication checks
- ✅ Repository detection
- ✅ Secret creation and retrieval
- ✅ Error handling
- ✅ Edge cases
- ✅ Complete E2E workflow
