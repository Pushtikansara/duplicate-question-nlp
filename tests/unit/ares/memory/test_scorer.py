from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ares.memory import MemoryScorer


class TestMemoryScorer:
    def test_score_by_recency_fresh(self) -> None:
        scorer = MemoryScorer()
        score = scorer.score_by_recency(datetime.now(timezone.utc))
        assert score > 0.99

    def test_score_by_recency_old(self) -> None:
        scorer = MemoryScorer()
        old = datetime.now(timezone.utc) - timedelta(days=30)
        score = scorer.score_by_recency(old, decay_hours=24.0)
        assert score < 0.01

    def test_score_by_access_count_zero(self) -> None:
        scorer = MemoryScorer()
        assert scorer.score_by_access_count(0) == 0.0

    def test_score_by_access_count_max(self) -> None:
        scorer = MemoryScorer()
        assert scorer.score_by_access_count(100) == 1.0
        assert scorer.score_by_access_count(200) == 1.0

    def test_score_by_frequency(self) -> None:
        scorer = MemoryScorer()
        score = scorer.score_by_frequency(10, time_span_hours=1.0)
        assert 0.0 < score <= 1.0

    def test_score_by_frequency_zero_span(self) -> None:
        scorer = MemoryScorer()
        assert scorer.score_by_frequency(10, time_span_hours=0) == 0.0

    def test_combined_score(self) -> None:
        scorer = MemoryScorer()
        score = scorer.combined_score(recency=0.8, frequency=0.6, base_quality=0.9)
        assert 0.0 <= score <= 1.0
        expected = 0.4 * 0.8 + 0.3 * 0.6 + 0.3 * 0.9
        assert score == pytest.approx(expected)

    def test_combined_score_default_weights(self) -> None:
        scorer = MemoryScorer()
        score = scorer.combined_score()
        assert score == 0.3  # 0.4*0 + 0.3*0 + 0.3*1
