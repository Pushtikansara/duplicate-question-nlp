from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
import yaml


TEST_CONFIGS: dict[str, dict[str, Any]] = {
    "app": {
        "default_model": "E5-base-v2",
        "default_threshold": 0.5,
        "default_device": "cpu",
    },
    "paths": {
        "data_dir": "data",
        "models_dir": "models",
        "results_dir": "outputs",
        "notebooks_dir": "notebooks",
        "week3_model_dir": "models/saved_transformer_model",
        "week4_model_dir": "models/week4_improved_model",
        "transformer_results_dir": "outputs/transformer_model",
        "week4_results_dir": "outputs/week4_improvement",
        "baseline_results_dir": "outputs/baseline_model",
        "bge_model_dir": "models/bge_base_en_v1_5",
        "e5_model_dir": "models/e5_base_v2",
        "mpnet_model_dir": "models/mpnet_base_v2",
        "deberta_model_dir": "models/deberta_v3_cross_encoder",
        "finetuned_e5_dir": "models/e5-quora-finetuned",
        "finetuned_bge_dir": "models/bge-quora-finetuned",
        "finetuned_cross_encoder_dir": "models/cross-encoder-quora",
    },
    "models": {
        "model_choices": [
            "TF-IDF + Logistic Regression (Week 2)",
            "TF-IDF + Linear SVM (Week 2)",
            "DistilBERT (Week 3)",
            "Improved DistilBERT (Week 4)",
            "BGE-base-en-v1.5",
            "E5-base-v2",
            "E5-quora-finetuned",
            "MPNet-base-v2",
            "DeBERTa-v3 Cross-Encoder",
            "Cross-Encoder-Quora (Trained)",
            "Semantic Ensemble",
        ],
        "model_version_short": {
            "TF-IDF + Logistic Regression (Week 2)": "week2_lr",
            "TF-IDF + Linear SVM (Week 2)": "week2_svm",
            "DistilBERT (Week 3)": "week3",
            "Improved DistilBERT (Week 4)": "week4",
            "BGE-base-en-v1.5": "bge",
            "E5-base-v2": "e5",
            "E5-quora-finetuned": "e5_ft",
            "MPNet-base-v2": "mpnet",
            "DeBERTa-v3 Cross-Encoder": "deberta",
            "Cross-Encoder-Quora (Trained)": "ce_quora",
            "Semantic Ensemble": "ensemble",
        },
        "backends": {
            "transformer_models": ["DistilBERT (Week 3)", "Improved DistilBERT (Week 4)"],
            "sentence_transformer_models": ["BGE-base-en-v1.5", "E5-base-v2", "E5-quora-finetuned", "MPNet-base-v2"],
            "cross_encoder_models": ["DeBERTa-v3 Cross-Encoder", "Cross-Encoder-Quora (Trained)"],
            "finetuned_embedding_models": ["E5-quora-finetuned"],
        },
        "hub_names": {
            "bge": "BAAI/bge-base-en-v1.5",
            "e5": "intfloat/e5-base-v2",
            "mpnet": "sentence-transformers/all-mpnet-base-v2",
            "deberta": "cross-encoder/deberta-v3-base",
        },
        "lr_heads": {
            "E5-quora-finetuned": "e5_ft_lr_head.pkl",
            "BGE-quora-finetuned": "bge_ft_lr_head.pkl",
            "bge": "bge_lr_head.pkl",
            "e5": "e5_lr_head.pkl",
            "mpnet": "mpnet_lr_head.pkl",
        },
    },
    "inference": {
        "default_threshold": 0.5,
        "models": {
            "BGE-base-en-v1.5": {"threshold": 0.463, "sigmoid_steepness": 15.6755, "sigmoid_midpoint": 0.8591},
            "E5-base-v2": {"threshold": 0.480, "sigmoid_steepness": 34.6141, "sigmoid_midpoint": 0.8897},
            "E5-quora-finetuned": {"threshold": 0.50, "sigmoid_steepness": 15.0, "sigmoid_midpoint": 0.50},
            "MPNet-base-v2": {"threshold": 0.480, "sigmoid_steepness": 11.5976, "sigmoid_midpoint": 0.8133},
            "DeBERTa-v3 Cross-Encoder": {"threshold": 0.50, "sigmoid_steepness": 15.0, "sigmoid_midpoint": 0.50},
            "Cross-Encoder-Quora (Trained)": {"threshold": 0.50, "sigmoid_steepness": 15.0, "sigmoid_midpoint": 0.50},
        },
        "batch_size": 32,
        "max_length": 128,
        "auto_device": "cpu",
    },
    "dataset": {
        "train_file": "train-00000-of-00001-c3f24d739a9067e4.parquet",
        "test_file": "test-00000-of-00001-33935d3cc0ae7f4b.parquet",
        "val_file": "val-00000-of-00001-6b615184b4f17f7a.parquet",
        "full_file": "quora_duplicate_questions_full.parquet",
        "q1_col": "question1",
        "q2_col": "question2",
        "label_col": "is_duplicate",
        "id_col": "id",
        "hard_negative_mining": {
            "embedding_top_k": 50,
            "lexical_top_k": 50,
        },
    },
    "evaluation": {
        "ece_bins": 15,
        "baseline_models": ["week2_lr", "week2_svm"],
    },
    "training": {
        "seed": 42,
        "splits": {"train": 0.8, "val": 0.1, "test": 0.1},
        "transformer": {
            "learning_rate": 2e-5,
            "batch_size": 16,
            "epochs": 3,
        },
        "embedding": {
            "learning_rate": 1e-4,
            "batch_size": 32,
            "epochs": 10,
        },
        "mlp": {
            "learning_rate": 1e-3,
            "batch_size": 32,
            "epochs": 50,
        },
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S",
        "console": {"enabled": True, "level": "INFO"},
        "file": {"enabled": False},
    },
}


@pytest.fixture
def temp_config_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_dir = Path(tmpdir)
        for name, cfg in TEST_CONFIGS.items():
            filepath = config_dir / f"{name}.yaml"
            with open(filepath, "w") as f:
                yaml.dump(cfg, f)
        yield config_dir


@pytest.fixture
def isolated_project_root(temp_config_dir: Path) -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "configs").mkdir()
        for name, cfg in TEST_CONFIGS.items():
            filepath = root / "configs" / f"{name}.yaml"
            with open(filepath, "w") as f:
                yaml.dump(cfg, f)
        (root / "src").mkdir()
        (root / "data").mkdir()
        (root / "models").mkdir()
        (root / "outputs").mkdir()
        yield root


@pytest.fixture
def mock_model_weights() -> MagicMock:
    mock = MagicMock()
    mock.return_value = {"logits": [[0.3, 0.7]]}
    return mock


@pytest.fixture
def mock_sentence_transformer():
    with patch("duplicate_question_app._models.embeddings.SentenceTransformer") as mock_st:
        instance = MagicMock()
        instance.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_st.return_value = instance
        yield mock_st


@pytest.fixture
def mock_torch_device():
    with patch("torch.device") as mock_dev:
        mock_dev.return_value = "cpu"
        yield mock_dev


@pytest.fixture
def env_with_overrides():
    old = {}
    vars_to_set = {
        "DQD_DEFAULT_MODEL": "test-model",
        "DQD_DEFAULT_THRESHOLD": "0.75",
        "DQD_BATCH_SIZE": "64",
        "DQD_LOG_LEVEL": "DEBUG",
    }
    for k, v in vars_to_set.items():
        old[k] = os.environ.get(k)
        os.environ[k] = v
    yield
    for k in vars_to_set:
        if old[k] is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = old[k]


import os


@pytest.fixture
def mock_transformers_model():
    with patch("duplicate_question_app._inference.transformer.AutoTokenizer") as mock_tok:
        with patch("duplicate_question_app._inference.transformer.AutoModelForSequenceClassification") as mock_model:
            tok_instance = MagicMock()
            tok_instance.return_value = {"input_ids": [[0, 1, 2]], "attention_mask": [[1, 1, 1]]}
            tok_instance.decode.return_value = "decoded"
            mock_tok.from_pretrained.return_value = tok_instance

            model_instance = MagicMock()
            model_instance.return_value.logits = [[0.3, 0.7]]
            model_instance.config.id2label = {0: "NON_DUPLICATE", 1: "DUPLICATE"}
            mock_model.from_pretrained.return_value = model_instance
            yield mock_tok, mock_model
