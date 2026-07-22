from __future__ import annotations

import pytest

from ares.cli.utils.validation import (
    validate_directory,
    validate_env_var,
    validate_file,
    validate_float_range,
    validate_non_empty_string,
    validate_path,
    validate_positive_int,
)


class TestValidation:
    def test_validate_path_existing(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        result = validate_path(f)
        assert result == f.resolve()

    def test_validate_path_not_existing(self):
        with pytest.raises(FileNotFoundError):
            validate_path("/nonexistent/path/12345")

    def test_validate_path_must_exist_false(self, tmp_path):
        p = tmp_path / "doesnt_exist_yet"
        result = validate_path(p, must_exist=False)
        assert result == p.resolve()

    def test_validate_file_existing(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")
        result = validate_file(f)
        assert result == f.resolve()

    def test_validate_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_file("/nonexistent/file.txt")

    def test_validate_file_is_directory(self, tmp_path):
        with pytest.raises(ValueError, match="Not a file"):
            validate_file(tmp_path)

    def test_validate_directory_existing(self, tmp_path):
        result = validate_directory(tmp_path)
        assert result == tmp_path.resolve()

    def test_validate_directory_not_found(self):
        with pytest.raises(FileNotFoundError):
            validate_directory("/nonexistent/dir")

    def test_validate_directory_is_file(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("data")
        with pytest.raises(ValueError, match="Not a directory"):
            validate_directory(f)

    def test_validate_env_var_not_set(self):
        result = validate_env_var("__DOES_NOT_EXIST_12345__")
        assert result is None

    def test_validate_env_var_set(self, monkeypatch):
        monkeypatch.setenv("TEST_VAR", "hello")
        result = validate_env_var("TEST_VAR")
        assert result == "hello"

    def test_validate_positive_int_valid(self):
        assert validate_positive_int(5) == 5

    def test_validate_positive_int_zero(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_int(0)

    def test_validate_positive_int_negative(self):
        with pytest.raises(ValueError, match="must be positive"):
            validate_positive_int(-1)

    def test_validate_positive_int_string(self):
        assert validate_positive_int("10") == 10

    def test_validate_positive_int_invalid_string(self):
        with pytest.raises(ValueError, match="must be an integer"):
            validate_positive_int("abc")

    def test_validate_float_range_valid(self):
        assert validate_float_range(0.5) == 0.5

    def test_validate_float_range_min(self):
        with pytest.raises(ValueError):
            validate_float_range(-0.1)

    def test_validate_float_range_max(self):
        with pytest.raises(ValueError):
            validate_float_range(1.5)

    def test_validate_float_range_custom(self):
        assert validate_float_range(5, 0, 10) == 5

    def test_validate_float_range_invalid(self):
        with pytest.raises(ValueError, match="must be a float"):
            validate_float_range("abc")

    def test_validate_non_empty_string_valid(self):
        assert validate_non_empty_string("hello") == "hello"

    def test_validate_non_empty_string_empty(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_non_empty_string("")

    def test_validate_non_empty_string_whitespace(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_non_empty_string("   ")

    def test_validate_non_empty_string_int(self):
        assert validate_non_empty_string(42) == "42"
