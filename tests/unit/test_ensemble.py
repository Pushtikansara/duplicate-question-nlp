from __future__ import annotations

import numpy as np


class TestEnsembleV1:
    def test_adaptive_weights_imports(self):
        from duplicate_question_app._ensemble.v1 import compute_adaptive_weights

        assert callable(compute_adaptive_weights)

    def test_get_adaptive_ensemble_prediction_imports(self):
        from duplicate_question_app._ensemble.v1 import get_adaptive_ensemble_prediction

        assert callable(get_adaptive_ensemble_prediction)

    def test_compute_adaptive_weights_returns_weights(self):
        from duplicate_question_app._ensemble.v1 import compute_adaptive_weights

        result = compute_adaptive_weights("How to code?", "How to write code?")
        assert result is not None


class TestEnsembleV2:
    def test_embedding_cache_imports(self):
        from duplicate_question_app._ensemble.v2 import EmbeddingCache

        cache = EmbeddingCache()
        assert cache is not None

    def test_embedding_cache_put_get(self):
        from duplicate_question_app._ensemble.v2 import EmbeddingCache

        cache = EmbeddingCache()
        emb = np.array([0.1, 0.2, 0.3])
        cache.put("test_model", "test text", emb)
        result = cache.get("test_model", "test text")
        assert result is not None
        assert np.allclose(result, emb)

    def test_embedding_cache_miss(self):
        from duplicate_question_app._ensemble.v2 import EmbeddingCache

        cache = EmbeddingCache()
        result = cache.get("nonexistent", "text")
        assert result is None

    def test_adaptive_ensemble_predict_imports(self):
        from duplicate_question_app._ensemble.v2 import adaptive_ensemble_predict

        assert callable(adaptive_ensemble_predict)


class TestAgreement:
    def test_collect_all_votes_imports(self):
        from duplicate_question_app._ensemble.agreement import collect_all_votes

        assert callable(collect_all_votes)

    def test_analyze_agreement_imports(self):
        from duplicate_question_app._ensemble.agreement import analyze_agreement

        assert callable(analyze_agreement)

    def test_model_vote_instantiation(self):
        from duplicate_question_app._ensemble.agreement import ModelVote

        vote = ModelVote(
            model_name="test",
            predicted_label=1,
            prob_duplicate=0.8,
            confidence=0.8,
            threshold=0.5,
            latency_ms=10.0,
        )
        assert vote.model_name == "test"
        assert vote.predicted_label == 1
