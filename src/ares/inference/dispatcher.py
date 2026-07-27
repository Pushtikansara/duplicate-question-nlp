from __future__ import annotations

import time
from typing import Any

import numpy as np

from ares._config import get_app_paths, get_config
from ares._result import PredictionResult
from ares.model_loader import get_model_info, load_model
from ares.model_registry import ModelBackend, find_entry, list_models


class InferenceDispatcher:
    _label_mapping = {0: "Non-Duplicate", 1: "Duplicate"}

    @staticmethod
    def predict(
        model_name: str,
        question1: str,
        question2: str,
        threshold: float | None = None,
    ) -> PredictionResult:
        paths = get_app_paths()
        entry = find_entry(model_name, paths)
        if entry is None:
            raise ValueError(f"Unknown model: '{model_name}'. Available: {', '.join(list_models())}")

        if entry.backend == ModelBackend.ENSEMBLE:
            from ares.fusion import FusionEngine

            engine = FusionEngine()
            return engine.fuse(question1, question2, threshold=threshold)

        start = time.perf_counter()
        result = _run_backend_prediction(entry, model_name, question1, question2, threshold)
        elapsed = (time.perf_counter() - start) * 1000

        return PredictionResult(
            predicted_label=result["predicted_label"],
            prediction=result["prediction"],
            confidence=result["confidence"],
            prob_duplicate=result["prob_duplicate"],
            prob_non_duplicate=result["prob_non_duplicate"],
            model_name=model_name,
            latency_ms=elapsed,
            selected_model=model_name,
            executed_model=model_name,
            backend=result["backend"],
            artifact_path=result.get("artifact_path"),
            tokenizer=result.get("tokenizer"),
            inference_function=result.get("inference_function"),
            execution_time_ms=elapsed,
            raw_logits=result.get("raw_logits"),
            softmax=result.get("softmax"),
            predicted_class_id=result["predicted_label"],
            label_mapping=InferenceDispatcher._label_mapping,
            final_label=result["prediction"],
            threshold=result.get("threshold", 0.5),
        )

    @staticmethod
    def predict_with_diagnostics(
        model_name: str,
        question1: str,
        question2: str,
    ) -> dict[str, Any]:
        result = InferenceDispatcher.predict(model_name, question1, question2)
        load_info = get_model_info(model_name)
        return {
            "prediction": result.to_dict(),
            "model_info": load_info,
        }

    @staticmethod
    def list_models() -> list[str]:
        return list_models()

    @staticmethod
    def get_backend_for_model(model_name: str) -> str:
        entry = find_entry(model_name)
        if entry is None:
            return "unknown"
        return entry.backend.value

    @staticmethod
    def validate_model(model_name: str) -> None:
        entry = find_entry(model_name)
        if entry is None:
            raise ValueError(f"Unknown model: '{model_name}'")


def _run_backend_prediction(entry: Any, model_name: str, q1: str, q2: str, threshold: float | None) -> dict[str, Any]:
    backend = entry.backend

    if backend == ModelBackend.CLASSICAL_ML:
        return _predict_classical(entry, q1, q2, threshold)
    elif backend == ModelBackend.TRANSFORMER:
        return _predict_transformer(entry, q1, q2, threshold)
    elif backend == ModelBackend.BI_ENCODER:
        return _predict_bi_encoder(entry, q1, q2, threshold)
    elif backend == ModelBackend.CROSS_ENCODER:
        return _predict_cross_encoder(entry, q1, q2, threshold)
    else:
        raise ValueError(f"Unsupported backend: {backend}")


def _get_threshold(entry: Any, override: float | None) -> float:
    if override is not None:
        return override
    inf_cfg = get_config("inference") or {}
    thresholds = inf_cfg.get("per_model_thresholds", {})
    return float(thresholds.get(entry.display_name, inf_cfg.get("default_threshold", 0.5)))


def _predict_classical(entry: Any, q1: str, q2: str, threshold: float | None) -> dict[str, Any]:
    from duplicate_question_app._preprocessing import normalize_question

    loaded = load_model(entry.display_name)
    clf = loaded["classifier"]
    vectorizer = loaded["vectorizer"]

    q1_norm = normalize_question(q1, expand_abbrevs=True, fix_typos=True)
    q2_norm = normalize_question(q2, expand_abbrevs=True, fix_typos=True)

    combined = q1_norm + " " + q2_norm
    X = vectorizer.transform([combined])
    decision_th = _get_threshold(entry, threshold)

    if hasattr(clf, "predict_proba"):
        proba = clf.predict_proba(X)[0]
        prob_dup = float(proba[1]) if len(proba) > 1 else float(clf.predict(X)[0])
    else:
        pred = clf.predict(X)[0]
        prob_dup = float(pred)
        if hasattr(clf, "decision_function"):
            decision = clf.decision_function(X)[0]
            prob_dup = 1.0 / (1.0 + np.exp(-decision))

    prob_non = 1.0 - prob_dup
    predicted_label = int(prob_dup >= decision_th)
    prediction = InferenceDispatcher._label_mapping[predicted_label]
    confidence = max(prob_dup, prob_non)

    return {
        "predicted_label": predicted_label,
        "prediction": prediction,
        "confidence": confidence,
        "prob_duplicate": prob_dup,
        "prob_non_duplicate": prob_non,
        "backend": "ClassicalMLBackend",
        "artifact_path": entry.artifact_path,
        "tokenizer": "TfidfVectorizer",
        "inference_function": "sklearn.linear_model/svm.predict",
        "threshold": decision_th,
        "raw_logits": [prob_non, prob_dup],
        "softmax": [prob_non, prob_dup],
    }


def _predict_transformer(entry: Any, q1: str, q2: str, threshold: float | None) -> dict[str, Any]:
    import torch

    from duplicate_question_app._preprocessing import normalize_question

    loaded = load_model(entry.display_name)
    model = loaded["model"]
    tokenizer = loaded["tokenizer"]
    device = loaded["device"]

    inf_cfg = get_config("inference") or {}
    max_length = inf_cfg.get("max_length", 128)
    decision_th = _get_threshold(entry, threshold)

    q1_norm = normalize_question(q1, expand_abbrevs=True, fix_typos=True)
    q2_norm = normalize_question(q2, expand_abbrevs=True, fix_typos=True)

    inputs = tokenizer(
        q1_norm,
        q2_norm,
        max_length=max_length,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits[0].cpu().tolist()
        probabilities = torch.softmax(outputs.logits, dim=1)[0].cpu().tolist()

    prob_non = float(probabilities[0])
    prob_dup = float(probabilities[1])
    predicted_label = int(prob_dup >= decision_th)
    prediction = InferenceDispatcher._label_mapping[predicted_label]
    confidence = max(prob_non, prob_dup)

    return {
        "predicted_label": predicted_label,
        "prediction": prediction,
        "confidence": confidence,
        "prob_duplicate": prob_dup,
        "prob_non_duplicate": prob_non,
        "backend": "TransformerBackend",
        "artifact_path": entry.artifact_path,
        "tokenizer": "AutoTokenizer",
        "inference_function": "transformers.AutoModelForSequenceClassification.forward",
        "threshold": decision_th,
        "raw_logits": logits,
        "softmax": probabilities,
    }


def _predict_bi_encoder(entry: Any, q1: str, q2: str, threshold: float | None) -> dict[str, Any]:
    import numpy as np

    from duplicate_question_app._preprocessing import normalize_question

    loaded = load_model(entry.display_name)
    model = loaded["model"]
    use_e5_prefix = loaded.get("use_e5_prefix", False)

    inf_cfg = get_config("inference") or {}
    sigmoid_params = inf_cfg.get("sigmoid_params", {})
    default_sigmoid = (15.0, 0.50)
    name = entry.internal_id
    params_map = {
        "e5_ft": sigmoid_params.get("E5-quora-finetuned", [10.0, 0.73]),
        "e5": sigmoid_params.get("E5-base-v2", [8.0, 0.82]),
        "bge": sigmoid_params.get("BGE-base-en-v1.5", [15.6755, 0.8591]),
        "mpnet": sigmoid_params.get("MPNet-base-v2", [11.5976, 0.8133]),
    }
    steepness, midpoint = params_map.get(name, default_sigmoid)
    if isinstance(steepness, list):
        steepness, midpoint = steepness[0], steepness[1]
    decision_th = _get_threshold(entry, threshold)

    q1_norm = normalize_question(q1, expand_abbrevs=True, fix_typos=True)
    q2_norm = normalize_question(q2, expand_abbrevs=True, fix_typos=True)

    q1_enc = f"query: {q1_norm}" if use_e5_prefix else q1_norm
    q2_enc = f"passage: {q2_norm}" if use_e5_prefix else q2_norm

    emb1 = model.encode(q1_enc, normalize_embeddings=True)
    emb2 = model.encode(q2_enc, normalize_embeddings=True)

    similarity = float(np.dot(emb1, emb2))
    prob_dup = 1.0 / (1.0 + np.exp(-steepness * (similarity - midpoint)))
    prob_non = 1.0 - prob_dup
    predicted_label = int(prob_dup >= decision_th)
    prediction = InferenceDispatcher._label_mapping[predicted_label]
    confidence = max(prob_non, prob_dup)

    return {
        "predicted_label": predicted_label,
        "prediction": prediction,
        "confidence": confidence,
        "prob_duplicate": prob_dup,
        "prob_non_duplicate": prob_non,
        "backend": "EmbeddingBackend",
        "artifact_path": entry.artifact_path,
        "tokenizer": "SentenceTransformer.tokenizer",
        "inference_function": "sentence_transformers.SentenceTransformer.encode + cosine_similarity + sigmoid",
        "threshold": decision_th,
        "raw_logits": [similarity],
        "softmax": [prob_non, prob_dup],
    }


def _predict_cross_encoder(entry: Any, q1: str, q2: str, threshold: float | None) -> dict[str, Any]:
    import numpy as np

    from duplicate_question_app._preprocessing import normalize_question

    loaded = load_model(entry.display_name)
    model = loaded["model"]

    decision_th = _get_threshold(entry, threshold)

    q1_norm = normalize_question(q1, expand_abbrevs=True, fix_typos=True)
    q2_norm = normalize_question(q2, expand_abbrevs=True, fix_typos=True)

    scores = model.predict([(q1_norm, q2_norm)], apply_softmax=True)[0]

    if isinstance(scores, (list, np.ndarray)) and len(scores) >= 3:
        contra = float(scores[0])
        entail = float(scores[2])
        denom = contra + entail
        prob_dup = entail / denom if denom > 0.01 else 0.5
        raw_logits = [contra, float(scores[1]), entail]
        softmax_out = [float(s) for s in scores]
    elif isinstance(scores, (list, np.ndarray)) and len(scores) == 2:
        prob_dup = float(scores[1])
        raw_logits = [float(s) for s in scores]
        softmax_out = raw_logits[:]
    else:
        prob_dup = max(0.0, min(1.0, (float(scores[0]) + 1) / 2))
        raw_logits = [float(scores[0])]
        softmax_out = raw_logits[:]

    prob_non = 1.0 - prob_dup
    predicted_label = int(prob_dup >= decision_th)
    prediction = InferenceDispatcher._label_mapping[predicted_label]
    confidence = max(prob_non, prob_dup)

    return {
        "predicted_label": predicted_label,
        "prediction": prediction,
        "confidence": confidence,
        "prob_duplicate": prob_dup,
        "prob_non_duplicate": prob_non,
        "backend": "CrossEncoderBackend",
        "artifact_path": entry.artifact_path,
        "tokenizer": "CrossEncoder.tokenizer",
        "inference_function": "sentence_transformers.CrossEncoder.predict",
        "threshold": decision_th,
        "raw_logits": raw_logits,
        "softmax": softmax_out,
    }
