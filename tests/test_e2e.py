"""End-to-end tests for ghs."""

import json
import subprocess
import time

import pytest
from typer.testing import CliRunner

from ghss.commands import app

runner = CliRunner()


@pytest.fixture
def e2e_test_env_file(tmp_path):
    """Create a test .env file with test secrets."""
    env_file = tmp_path / "test.env"
    env_file.write_text(
        "E2E_TEST_SECRET_1=test_value_1\n"
        "E2E_TEST_SECRET_2=test_value_2\n"
        "E2E_TEST_SECRET_3=test_value_3\n"
    )
    return env_file


@pytest.fixture
def e2e_output_env_file(tmp_path):
    """Create a path for output .env file."""
    return tmp_path / "output.env"


def is_gh_authenticated():
    """Check if gh CLI is authenticated."""
    result = subprocess.run(
        ["gh", "auth", "status"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def cleanup_e2e_secrets():
    """Clean up any E2E test secrets from the repository."""
    try:
        result = subprocess.run(
            ["gh", "secret", "list", "--json", "name"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            secrets = json.loads(result.stdout)
            for secret in secrets:
                if secret["name"].startswith("E2E_TEST_SECRET_"):
                    subprocess.run(
                        ["gh", "secret", "delete", secret["name"]],
                        capture_output=True,
                        check=False,
                    )
    except Exception:
        pass  # Best effort cleanup


@pytest.mark.e2e
class TestE2EWorkflow:
    """End-to-end tests for the complete workflow.

    These tests require:
    - gh CLI to be installed and authenticated
    - Access to a GitHub repository
    - Permission to create and delete secrets in that repository

    Run with: pytest -m e2e
    Skip with: pytest -m "not e2e"
    """

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Set up and tear down for each test."""
        # Check if gh is authenticated
        if not is_gh_authenticated():
            pytest.skip(
                "gh CLI is not authenticated. Run 'gh auth login' to authenticate."
            )

        # Clean up before test
        cleanup_e2e_secrets()

        yield

        # Clean up after test
        cleanup_e2e_secrets()

    def test_e2e_set_and_get_secrets(self, e2e_test_env_file, e2e_output_env_file):
        """Test the complete workflow: set secrets from .env and retrieve them.

        This test:
        1. Sets secrets from a test .env file using the 'set' command
        2. Retrieves secret names using the 'get' command
        3. Compares the retrieved secret names with the original ones
        """
        # Step 1: Set secrets from the test .env file
        set_result = runner.invoke(app, ["set", "-f", str(e2e_test_env_file)])
        assert set_result.exit_code == 0, f"Set command failed: {set_result.stdout}"
        assert "Successfully set 3 secret(s)" in set_result.stdout

        # Wait a bit for secrets to propagate
        time.sleep(3)

        # Step 2: Get secrets and write to output file
        get_result = runner.invoke(app, ["get", "-f", str(e2e_output_env_file)])
        assert get_result.exit_code == 0, f"Get command failed: {get_result.stdout}"
        assert "Found 3 secret(s)" in get_result.stdout or "Found" in get_result.stdout

        # Step 3: Read the output file and verify secret names
        assert e2e_output_env_file.exists(), "Output .env file was not created"

        output_content = e2e_output_env_file.read_text()
        output_lines = [
            line.strip() for line in output_content.strip().split("\n") if line.strip()
        ]

        # Parse secret names from output file
        output_secrets = set()
        for line in output_lines:
            if "=" in line:
                key = line.split("=")[0].strip()
                if key.startswith("E2E_TEST_SECRET_"):
                    output_secrets.add(key)

        # Verify all test secrets are present
        expected_secrets = {
            "E2E_TEST_SECRET_1",
            "E2E_TEST_SECRET_2",
            "E2E_TEST_SECRET_3",
        }
        assert output_secrets == expected_secrets, (
            f"Retrieved secrets {output_secrets} do not match expected {expected_secrets}"
        )

        # Step 4: Read the original file and compare structure
        original_content = e2e_test_env_file.read_text()
        original_lines = [line.strip() for line in original_content.strip().split("\n")]

        original_keys = set()
        for line in original_lines:
            if "=" in line:
                key = line.split("=")[0].strip()
                original_keys.add(key)

        # Verify all original keys are in output (values will be empty in output)
        assert original_keys == output_secrets, (
            f"Original keys {original_keys} do not match output keys {output_secrets}"
        )

    def test_e2e_testconf(self):
        """Test the testconf command end-to-end.

        This test runs the testconf command which:
        1. Checks authentication
        2. Creates a test secret
        3. Verifies the secret exists
        4. Deletes the test secret
        """
        result = runner.invoke(app, ["testconf"])

        assert result.exit_code == 0, f"Testconf failed: {result.stdout}"
        assert "authenticated" in result.stdout
        assert "All tests passed" in result.stdout

    def test_e2e_empty_env_file(self, tmp_path, e2e_output_env_file):
        """Test handling of empty .env file."""
        empty_file = tmp_path / "empty.env"
        empty_file.write_text("")

        result = runner.invoke(app, ["set", "-f", str(empty_file)])

        assert result.exit_code == 0
        assert "No secrets found" in result.stdout

    def test_e2e_file_not_found(self, tmp_path):
        """Test handling of non-existent file."""
        non_existent = tmp_path / "nonexistent.env"

        result = runner.invoke(app, ["set", "-f", str(non_existent)])

        assert result.exit_code == 1
        assert "not found" in result.stdout
