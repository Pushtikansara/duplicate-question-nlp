from __future__ import annotations

from unittest.mock import patch

import pandas as pd
import pytest


class TestDatasetLoader:
    def test_load_quora_data_imports(self):
        from duplicate_question_app._dataset.loader import load_quora_data

        assert callable(load_quora_data)

    def test_get_quora_splits_imports(self):
        from duplicate_question_app._dataset.loader import get_quora_splits

        assert callable(get_quora_splits)

    @patch("duplicate_question_app._dataset.loader.pd.read_parquet")
    @patch("pathlib.Path.exists", return_value=True)
    def test_load_quora_data_calls_read_parquet(self, mock_exists, mock_read):
        mock_df = pd.DataFrame({"q1": ["a"], "q2": ["b"], "label": [1]})
        mock_read.return_value = mock_df
        from duplicate_question_app._dataset.loader import load_quora_data

        result = load_quora_data("fake_path.parquet")
        assert result is not None
        mock_read.assert_called_once()

    @patch("pathlib.Path.exists", return_value=True)
    @patch("duplicate_question_app._dataset.loader.pd.read_parquet")
    def test_load_quora_data_returns_dataframe(self, mock_read, mock_exists):
        mock_df = pd.DataFrame({"q1": ["a"], "q2": ["b"], "label": [1]})
        mock_read.return_value = mock_df
        from duplicate_question_app._dataset.loader import load_quora_data

        result = load_quora_data("fake.parquet")
        assert isinstance(result, pd.DataFrame)

    def test_load_quora_data_raises_on_missing(self):
        from duplicate_question_app._dataset.loader import load_quora_data

        with pytest.raises((FileNotFoundError, Exception)):
            load_quora_data("/nonexistent/path.parquet")

    @patch("pathlib.Path.exists", return_value=True)
    @patch("duplicate_question_app._dataset.loader.pd.read_parquet")
    def test_get_quora_splits_returns_tuple_with_splits(self, mock_read, mock_exists):
        n = 100
        df = pd.DataFrame(
            {
                "q1": [f"q1_{i}" for i in range(n)],
                "q2": [f"q2_{i}" for i in range(n)],
                "label": [i % 2 for i in range(n)],
            }
        )
        mock_read.return_value = df
        from duplicate_question_app._dataset.loader import get_quora_splits

        train, val, test = get_quora_splits(data_path="fake.parquet")
        assert isinstance(train, pd.DataFrame)
        assert isinstance(val, pd.DataFrame)
        assert isinstance(test, pd.DataFrame)

    @patch("pathlib.Path.exists", return_value=True)
    @patch("duplicate_question_app._dataset.loader.pd.read_parquet")
    def test_get_quora_splits_2_rows(self, mock_read, mock_exists):
        n = 20
        df = pd.DataFrame(
            {
                "q1": [f"q1_{i}" for i in range(n)],
                "q2": [f"q2_{i}" for i in range(n)],
                "label": [i % 2 for i in range(n)],
            }
        )
        mock_read.return_value = df
        from duplicate_question_app._dataset.loader import get_quora_splits

        train, val, test = get_quora_splits(data_path="fake.parquet")
        assert isinstance(train, pd.DataFrame)
        assert isinstance(val, pd.DataFrame)
        assert isinstance(test, pd.DataFrame)
