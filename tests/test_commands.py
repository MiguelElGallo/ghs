"""Unit tests for commands module."""

import json
from unittest.mock import MagicMock

import typer
from typer.testing import CliRunner

from ghss.commands import app

runner = CliRunner()


class TestTestconf:
    """Tests for testconf command."""

    def test_testconf_success(self, mocker):
        """Test successful testconf execution."""
        # Mock all the dependencies
        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")
        mocker.patch("ghss.commands.set_variable")
        mocker.patch("ghss.commands.delete_variable")
        
        # Mock list_variables to return the test variable
        mock_list_variables = mocker.patch("ghss.commands.list_variables")
        mock_list_variables.return_value = {
            "variables": [{"name": "GHS_TEST_VARIABLE_ABC12345"}]
        }
        
        # Mock get_variable_info to return the test variable with correct value
        mock_get_variable_info = mocker.patch("ghss.commands.get_variable_info")
        mock_get_variable_info.return_value = {
            "name": "GHS_TEST_VARIABLE_ABC12345",
            "value": "test_value_12345"
        }

        # Mock random string generation
        mocker.patch("ghss.commands.random.choices", return_value=list("abc12345"))
        mocker.patch("ghss.commands.time.sleep")

        result = runner.invoke(app, ["testconf"])

        assert result.exit_code == 0
        assert "authenticated" in result.stdout
        assert "All tests passed" in result.stdout

    def test_testconf_auth_failure(self, mocker):
        """Test testconf when authentication fails."""
        mocker.patch("ghss.commands.check_gh_auth", side_effect=typer.Exit(1))

        result = runner.invoke(app, ["testconf"])

        assert result.exit_code == 1

    def test_testconf_variable_not_found(self, mocker):
        """Test testconf when variable is not found after creation."""
        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")
        mocker.patch("ghss.commands.set_variable")

        # Mock list_variables to return empty list
        mock_list_variables = mocker.patch("ghss.commands.list_variables")
        mock_list_variables.return_value = {"variables": []}

        mocker.patch("ghss.commands.random.choices", return_value=list("abc12345"))
        mocker.patch("ghss.commands.time.sleep")

        result = runner.invoke(app, ["testconf"])

        assert result.exit_code == 1


class TestGet:
    """Tests for get command."""

    def test_get_success(self, mocker, tmp_path):
        """Test successful get command execution."""
        env_file = tmp_path / ".env"

        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")

        mock_list_variables = mocker.patch("ghss.commands.list_variables")
        mock_list_variables.return_value = {
            "variables": [
                {"name": "VAR1", "value": "value1"},
                {"name": "VAR2", "value": "value2"},
                {"name": "VAR3", "value": "value3"}
            ]
        }

        result = runner.invoke(app, ["get", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "Found 3 variable(s)" in result.stdout
        assert env_file.exists()

        content = env_file.read_text()
        assert "VAR1=value1\n" in content
        assert "VAR2=value2\n" in content
        assert "VAR3=value3\n" in content

    def test_get_no_variables(self, mocker, tmp_path):
        """Test get command when no variables exist."""
        env_file = tmp_path / ".env"

        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")

        mock_list_variables = mocker.patch("ghss.commands.list_variables")
        mock_list_variables.return_value = {"variables": []}

        result = runner.invoke(app, ["get", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "No variables found" in result.stdout
        assert not env_file.exists()

    def test_get_auth_failure(self, mocker):
        """Test get command when authentication fails."""
        mocker.patch("ghss.commands.check_gh_auth", side_effect=typer.Exit(1))

        result = runner.invoke(app, ["get"])

        assert result.exit_code == 1

    def test_get_default_file(self, mocker):
        """Test get command with default file name."""
        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")

        mock_list_variables = mocker.patch("ghss.commands.list_variables")
        mock_list_variables.return_value = {
            "variables": [{"name": "VAR1", "value": "value1"}]
        }
        
        mock_write = mocker.patch("ghss.commands.write_env_file")

        result = runner.invoke(app, ["get"])

        assert result.exit_code == 0
        mock_write.assert_called_once()
        # Check that default file ".env" was used
        assert mock_write.call_args[0][0] == ".env"


class TestSet:
    """Tests for set command."""

    def test_set_success(self, mocker, tmp_path):
        """Test successful set command execution."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=value2\n")

        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")
        
        mock_set_variable = mocker.patch("ghss.commands.set_variable")
        
        # Mock the confirmation prompt to return True
        mocker.patch("typer.confirm", return_value=True)

        result = runner.invoke(app, ["set", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "Found 2 variable(s) to set" in result.stdout
        assert "Successfully set 2 variable(s)" in result.stdout

        # Verify set_variable was called for each variable
        assert mock_set_variable.call_count == 2
        calls = mock_set_variable.call_args_list
        assert calls[0][0] == ("owner/repo", "KEY1", "value1")
        assert calls[1][0] == ("owner/repo", "KEY2", "value2")

    def test_set_cancelled(self, mocker, tmp_path):
        """Test set command when user cancels confirmation."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=value2\n")

        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")
        
        mock_set_variable = mocker.patch("ghss.commands.set_variable")
        
        # Mock the confirmation prompt to return False
        mocker.patch("typer.confirm", return_value=False)

        result = runner.invoke(app, ["set", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "Operation cancelled" in result.stdout
        # Verify set_variable was not called
        assert mock_set_variable.call_count == 0

    def test_set_no_variables(self, mocker, tmp_path):
        """Test set command when no variables in file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")

        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")

        result = runner.invoke(app, ["set", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "No variables found" in result.stdout

    def test_set_file_not_found(self, mocker, tmp_path):
        """Test set command when file doesn't exist."""
        non_existent = tmp_path / "nonexistent.env"

        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")

        result = runner.invoke(app, ["set", "-f", str(non_existent)])

        assert result.exit_code == 1
        # The error is shown in stderr, just check exit code
        assert result.exit_code == 1

    def test_set_auth_failure(self, mocker):
        """Test set command when authentication fails."""
        mocker.patch("ghss.commands.check_gh_auth", side_effect=typer.Exit(1))

        result = runner.invoke(app, ["set"])

        assert result.exit_code == 1

    def test_set_default_file(self, mocker, tmp_path):
        """Test set command with default file name."""
        # Create a .env file in the current directory
        import os

        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            env_file = tmp_path / ".env"
            env_file.write_text("KEY1=value1\n")

            mocker.patch("ghss.commands.check_gh_auth")
            mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")
            mocker.patch("ghss.commands.set_variable")
            mocker.patch("typer.confirm", return_value=True)

            result = runner.invoke(app, ["set"])

            assert result.exit_code == 0
            assert "Found 1 variable(s) to set" in result.stdout
        finally:
            os.chdir(original_dir)

    def test_set_filters_empty_values(self, mocker, tmp_path):
        """Test that set command filters out empty values."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=\nKEY3=value3\n")

        mocker.patch("ghss.commands.check_gh_auth")
        mocker.patch("ghss.commands.get_current_repo", return_value="owner/repo")

        mock_set_variable = mocker.patch("ghss.commands.set_variable")
        mocker.patch("typer.confirm", return_value=True)

        result = runner.invoke(app, ["set", "-f", str(env_file)])

        assert result.exit_code == 0
        # Should only set 2 variables (KEY1 and KEY3), not KEY2 which has empty value
        assert "Found 2 variable(s) to set" in result.stdout
        assert mock_set_variable.call_count == 2
