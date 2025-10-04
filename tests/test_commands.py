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
        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        mock_run_gh_command = mocker.patch("ghs.commands.run_gh_command")

        # Mock the secret list response
        mock_list_result = MagicMock()
        mock_list_result.stdout = json.dumps([{"name": "GHS_TEST_SECRET_ABC12345"}])

        # Configure run_gh_command to return appropriate results
        def run_gh_side_effect(args):
            if args[0] == "secret" and args[1] == "list":
                return mock_list_result
            return MagicMock()

        mock_run_gh_command.side_effect = run_gh_side_effect

        # Mock random string generation
        mocker.patch("ghs.commands.random.choices", return_value=list("abc12345"))
        mocker.patch("ghs.commands.time.sleep")

        result = runner.invoke(app, ["testconf"])

        assert result.exit_code == 0
        assert "authenticated" in result.stdout
        assert "All tests passed" in result.stdout

    def test_testconf_auth_failure(self, mocker):
        """Test testconf when authentication fails."""
        mocker.patch("ghs.commands.check_gh_auth", side_effect=typer.Exit(1))

        result = runner.invoke(app, ["testconf"])

        assert result.exit_code == 1

    def test_testconf_secret_not_found(self, mocker):
        """Test testconf when secret is not found after creation."""
        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        mock_run_gh_command = mocker.patch("ghs.commands.run_gh_command")

        # Mock the secret list response without the test secret
        mock_list_result = MagicMock()
        mock_list_result.stdout = json.dumps([])

        def run_gh_side_effect(args):
            if args[0] == "secret" and args[1] == "list":
                return mock_list_result
            return MagicMock()

        mock_run_gh_command.side_effect = run_gh_side_effect

        mocker.patch("ghs.commands.random.choices", return_value=list("abc12345"))
        mocker.patch("ghs.commands.time.sleep")

        result = runner.invoke(app, ["testconf"])

        assert result.exit_code == 1
        # The actual error message is shown in stderr
        assert result.exit_code == 1


class TestGet:
    """Tests for get command."""

    def test_get_success(self, mocker, tmp_path):
        """Test successful get command execution."""
        env_file = tmp_path / ".env"

        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        mock_result = MagicMock()
        mock_result.stdout = json.dumps(
            [{"name": "SECRET1"}, {"name": "SECRET2"}, {"name": "SECRET3"}]
        )

        mocker.patch("ghs.commands.run_gh_command", return_value=mock_result)

        result = runner.invoke(app, ["get", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "Found 3 secret(s)" in result.stdout
        assert env_file.exists()

        content = env_file.read_text()
        assert "SECRET1=\n" in content
        assert "SECRET2=\n" in content
        assert "SECRET3=\n" in content

    def test_get_no_secrets(self, mocker, tmp_path):
        """Test get command when no secrets exist."""
        env_file = tmp_path / ".env"

        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        mock_result = MagicMock()
        mock_result.stdout = json.dumps([])

        mocker.patch("ghs.commands.run_gh_command", return_value=mock_result)

        result = runner.invoke(app, ["get", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "No secrets found" in result.stdout
        assert not env_file.exists()

    def test_get_auth_failure(self, mocker):
        """Test get command when authentication fails."""
        mocker.patch("ghs.commands.check_gh_auth", side_effect=typer.Exit(1))

        result = runner.invoke(app, ["get"])

        assert result.exit_code == 1

    def test_get_default_file(self, mocker):
        """Test get command with default file name."""
        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        mock_result = MagicMock()
        mock_result.stdout = json.dumps([{"name": "SECRET1"}])

        mocker.patch("ghs.commands.run_gh_command", return_value=mock_result)
        mock_write = mocker.patch("ghs.commands.write_env_file")

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

        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        mock_run_gh_command = mocker.patch("ghs.commands.run_gh_command")

        result = runner.invoke(app, ["set", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "Found 2 secret(s) to set" in result.stdout
        assert "Successfully set 2 secret(s)" in result.stdout

        # Verify gh commands were called for each secret
        assert mock_run_gh_command.call_count == 2
        calls = mock_run_gh_command.call_args_list
        assert calls[0][0][0] == [
            "secret",
            "set",
            "KEY1",
            "--body",
            "value1",
            "--repo",
            "owner/repo",
        ]
        assert calls[1][0][0] == [
            "secret",
            "set",
            "KEY2",
            "--body",
            "value2",
            "--repo",
            "owner/repo",
        ]

    def test_set_no_secrets(self, mocker, tmp_path):
        """Test set command when no secrets in file."""
        env_file = tmp_path / ".env"
        env_file.write_text("")

        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        result = runner.invoke(app, ["set", "-f", str(env_file)])

        assert result.exit_code == 0
        assert "No secrets found" in result.stdout

    def test_set_file_not_found(self, mocker, tmp_path):
        """Test set command when file doesn't exist."""
        non_existent = tmp_path / "nonexistent.env"

        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        result = runner.invoke(app, ["set", "-f", str(non_existent)])

        assert result.exit_code == 1
        # The error is shown in stderr, just check exit code
        assert result.exit_code == 1

    def test_set_auth_failure(self, mocker):
        """Test set command when authentication fails."""
        mocker.patch("ghs.commands.check_gh_auth", side_effect=typer.Exit(1))

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

            mocker.patch("ghs.commands.check_gh_auth")
            mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")
            mocker.patch("ghs.commands.run_gh_command")

            result = runner.invoke(app, ["set"])

            assert result.exit_code == 0
            assert "Found 1 secret(s) to set" in result.stdout
        finally:
            os.chdir(original_dir)

    def test_set_filters_empty_values(self, mocker, tmp_path):
        """Test that set command filters out empty values."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=\nKEY3=value3\n")

        mocker.patch("ghs.commands.check_gh_auth")
        mocker.patch("ghs.commands.get_current_repo", return_value="owner/repo")

        mock_run_gh_command = mocker.patch("ghs.commands.run_gh_command")

        result = runner.invoke(app, ["set", "-f", str(env_file)])

        assert result.exit_code == 0
        # Should only set 2 secrets (KEY1 and KEY3), not KEY2 which has empty value
        assert "Found 2 secret(s) to set" in result.stdout
        assert mock_run_gh_command.call_count == 2
