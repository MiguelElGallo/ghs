"""Unit tests for gh_utils module."""

from unittest.mock import MagicMock

import pytest
import typer

from ghss.gh_utils import check_gh_auth, get_current_repo, run_gh_command


class TestRunGhCommand:
    """Tests for run_gh_command function."""

    def test_run_gh_command_success(self, mocker):
        """Test successful gh command execution."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success output"
        mock_result.stderr = ""

        mock_run = mocker.patch("subprocess.run", return_value=mock_result)

        result = run_gh_command(["secret", "list"])

        assert result.returncode == 0
        assert result.stdout == "success output"
        mock_run.assert_called_once_with(
            ["gh", "secret", "list"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_run_gh_command_failure_with_check(self, mocker):
        """Test gh command failure when check=True."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"

        mocker.patch("subprocess.run", return_value=mock_result)

        with pytest.raises(typer.Exit) as exc_info:
            run_gh_command(["secret", "list"], check=True)

        assert exc_info.value.exit_code == 1

    def test_run_gh_command_failure_without_check(self, mocker):
        """Test gh command failure when check=False."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error message"

        mocker.patch("subprocess.run", return_value=mock_result)

        result = run_gh_command(["secret", "list"], check=False)

        assert result.returncode == 1
        assert result.stderr == "error message"

    def test_run_gh_command_with_multiple_args(self, mocker):
        """Test gh command with multiple arguments."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""

        mock_run = mocker.patch("subprocess.run", return_value=mock_result)

        run_gh_command(
            ["secret", "set", "KEY", "--body", "value", "--repo", "owner/repo"]
        )

        mock_run.assert_called_once_with(
            ["gh", "secret", "set", "KEY", "--body", "value", "--repo", "owner/repo"],
            capture_output=True,
            text=True,
            check=False,
        )


class TestCheckGhAuth:
    """Tests for check_gh_auth function."""

    def test_check_gh_auth_success(self, mocker):
        """Test successful authentication check."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        mocker.patch("subprocess.run", return_value=mock_result)

        # Should not raise any exception
        check_gh_auth()

    def test_check_gh_auth_failure(self, mocker):
        """Test failed authentication check."""
        mock_result = MagicMock()
        mock_result.returncode = 1

        mocker.patch("subprocess.run", return_value=mock_result)

        with pytest.raises(typer.Exit) as exc_info:
            check_gh_auth()

        assert exc_info.value.exit_code == 1

    def test_check_gh_auth_calls_correct_command(self, mocker):
        """Test that check_gh_auth calls the correct command."""
        mock_result = MagicMock()
        mock_result.returncode = 0

        mock_run = mocker.patch("subprocess.run", return_value=mock_result)

        check_gh_auth()

        mock_run.assert_called_once_with(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            check=False,
        )


class TestGetCurrentRepo:
    """Tests for get_current_repo function."""

    def test_get_current_repo_success(self, mocker):
        """Test getting current repository."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "owner/repo\n"

        mock_run_gh_command = mocker.patch(
            "ghss.gh_utils.run_gh_command", return_value=mock_result
        )

        result = get_current_repo()

        assert result == "owner/repo"
        mock_run_gh_command.assert_called_once_with(
            ["repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"]
        )

    def test_get_current_repo_strips_whitespace(self, mocker):
        """Test that repository name is stripped of whitespace."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "  owner/repo  \n"

        mocker.patch("ghss.gh_utils.run_gh_command", return_value=mock_result)

        result = get_current_repo()

        assert result == "owner/repo"

    def test_get_current_repo_failure(self, mocker):
        """Test handling of failure to get repository."""
        mocker.patch("ghss.gh_utils.run_gh_command", side_effect=typer.Exit(1))

        with pytest.raises(typer.Exit) as exc_info:
            get_current_repo()

        assert exc_info.value.exit_code == 1
