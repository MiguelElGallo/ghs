"""Unit tests for env_utils module."""

import pytest
import typer

from ghss.env_utils import load_env_file, write_env_file


class TestLoadEnvFile:
    """Tests for load_env_file function."""

    def test_load_env_file_success(self, tmp_path):
        """Test loading a valid .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=value2\nKEY3=value3\n")

        result = load_env_file(str(env_file))

        assert result == {
            "KEY1": "value1",
            "KEY2": "value2",
            "KEY3": "value3",
        }

    def test_load_env_file_filters_empty_values(self, tmp_path):
        """Test that empty values are filtered out."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=\nKEY3=value3\n")

        result = load_env_file(str(env_file))

        assert result == {
            "KEY1": "value1",
            "KEY3": "value3",
        }

    def test_load_env_file_filters_empty_keys(self, tmp_path):
        """Test that empty keys are filtered out."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\n=value2\nKEY3=value3\n")

        result = load_env_file(str(env_file))

        assert result == {
            "KEY1": "value1",
            "KEY3": "value3",
        }

    def test_load_env_file_not_found(self, tmp_path):
        """Test loading a non-existent file raises typer.Exit."""
        non_existent_file = tmp_path / "nonexistent.env"

        with pytest.raises(typer.Exit) as exc_info:
            load_env_file(str(non_existent_file))

        assert exc_info.value.exit_code == 1

    def test_load_env_file_empty_file(self, tmp_path):
        """Test loading an empty file returns empty dict."""
        env_file = tmp_path / ".env"
        env_file.write_text("")

        result = load_env_file(str(env_file))

        assert result == {}

    def test_load_env_file_with_comments(self, tmp_path):
        """Test that comments are ignored."""
        env_file = tmp_path / ".env"
        env_file.write_text("# Comment\nKEY1=value1\n# Another comment\nKEY2=value2\n")

        result = load_env_file(str(env_file))

        assert result == {
            "KEY1": "value1",
            "KEY2": "value2",
        }


class TestWriteEnvFile:
    """Tests for write_env_file function."""

    def test_write_env_file_success(self, tmp_path):
        """Test writing variables to a .env file."""
        env_file = tmp_path / ".env"
        variables = [
            {"name": "VAR1", "value": "value1"},
            {"name": "VAR2", "value": "value2"},
            {"name": "VAR3", "value": "value3"},
        ]

        write_env_file(str(env_file), variables)

        content = env_file.read_text()
        assert content == "VAR1=value1\nVAR2=value2\nVAR3=value3\n"

    def test_write_env_file_empty_list(self, tmp_path):
        """Test writing empty variables list creates empty file."""
        env_file = tmp_path / ".env"
        variables = []

        write_env_file(str(env_file), variables)

        content = env_file.read_text()
        assert content == ""

    def test_write_env_file_overwrites_existing(self, tmp_path):
        """Test that writing overwrites existing file."""
        env_file = tmp_path / ".env"
        env_file.write_text("OLD_CONTENT=old_value\n")

        variables = [{"name": "NEW_VAR", "value": "new_value"}]
        write_env_file(str(env_file), variables)

        content = env_file.read_text()
        assert content == "NEW_VAR=new_value\n"

    def test_write_env_file_single_variable(self, tmp_path):
        """Test writing a single variable."""
        env_file = tmp_path / ".env"
        variables = [{"name": "SINGLE_VAR", "value": "single_value"}]

        write_env_file(str(env_file), variables)

        content = env_file.read_text()
        assert content == "SINGLE_VAR=single_value\n"
    
    def test_write_env_file_empty_value(self, tmp_path):
        """Test writing a variable with empty value."""
        env_file = tmp_path / ".env"
        variables = [{"name": "EMPTY_VAR", "value": ""}]

        write_env_file(str(env_file), variables)

        content = env_file.read_text()
        assert content == "EMPTY_VAR=\n"
