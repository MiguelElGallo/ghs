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
    """Create a test .env file with test variables."""
    env_file = tmp_path / "test.env"
    env_file.write_text(
        "E2E_TEST_VARIABLE_1=test_value_1\n"
        "E2E_TEST_VARIABLE_2=test_value_2\n"
        "E2E_TEST_VARIABLE_3=test_value_3\n"
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


def cleanup_e2e_variables():
    """Clean up any E2E test variables from the repository."""
    try:
        result = subprocess.run(
            ["gh", "api", "/repos/{owner}/{repo}/actions/variables"],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            variables = data.get("variables", [])
            for variable in variables:
                if variable["name"].startswith("E2E_TEST_VARIABLE_"):
                    subprocess.run(
                        ["gh", "api", "--method", "DELETE", 
                         f"/repos/{{owner}}/{{repo}}/actions/variables/{variable['name']}"],
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
    - Permission to create and delete variables in that repository

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
        cleanup_e2e_variables()

        yield

        # Clean up after test
        cleanup_e2e_variables()

    def test_e2e_set_and_get_variables(self, e2e_test_env_file, e2e_output_env_file):
        """Test the complete workflow: set variables from .env and retrieve them.

        This test:
        1. Sets variables from a test .env file using the 'set' command
        2. Retrieves variable names and values using the 'get' command
        3. Compares the retrieved variables with the original ones
        """
        # Step 1: Set variables from the test .env file (auto-confirm)
        set_result = runner.invoke(app, ["set", "-f", str(e2e_test_env_file)], input="y\n")
        assert set_result.exit_code == 0, f"Set command failed: {set_result.stdout}"
        assert "Successfully set 3 variable(s)" in set_result.stdout

        # Wait a bit for variables to propagate
        time.sleep(3)

        # Step 2: Get variables and write to output file
        get_result = runner.invoke(app, ["get", "-f", str(e2e_output_env_file)])
        assert get_result.exit_code == 0, f"Get command failed: {get_result.stdout}"
        assert "Found 3 variable(s)" in get_result.stdout or "Found" in get_result.stdout

        # Step 3: Read the output file and verify variable names and values
        assert e2e_output_env_file.exists(), "Output .env file was not created"

        output_content = e2e_output_env_file.read_text()
        output_lines = [
            line.strip() for line in output_content.strip().split("\n") if line.strip()
        ]

        # Parse variables from output file
        output_variables = {}
        for line in output_lines:
            if "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                if key.startswith("E2E_TEST_VARIABLE_"):
                    output_variables[key] = value

        # Verify all test variables are present with correct values
        expected_variables = {
            "E2E_TEST_VARIABLE_1": "test_value_1",
            "E2E_TEST_VARIABLE_2": "test_value_2",
            "E2E_TEST_VARIABLE_3": "test_value_3",
        }
        assert output_variables == expected_variables, (
            f"Retrieved variables {output_variables} do not match expected {expected_variables}"
        )

        # Step 4: Read the original file and compare
        original_content = e2e_test_env_file.read_text()
        original_lines = [line.strip() for line in original_content.strip().split("\n")]

        original_variables = {}
        for line in original_lines:
            if "=" in line:
                key, value = line.split("=", 1)
                original_variables[key.strip()] = value.strip()

        # Verify all original variables match output
        assert original_variables == output_variables, (
            f"Original variables {original_variables} do not match output variables {output_variables}"
        )

    def test_e2e_testconf(self):
        """Test the testconf command end-to-end.

        This test runs the testconf command which:
        1. Checks authentication
        2. Creates a test variable
        3. Verifies the variable exists
        4. Verifies the variable value
        5. Deletes the test variable
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
        assert "No variables found" in result.stdout

    def test_e2e_file_not_found(self, tmp_path):
        """Test handling of non-existent file."""
        non_existent = tmp_path / "nonexistent.env"

        result = runner.invoke(app, ["set", "-f", str(non_existent)])

        assert result.exit_code == 1
        assert "not found" in result.stdout
