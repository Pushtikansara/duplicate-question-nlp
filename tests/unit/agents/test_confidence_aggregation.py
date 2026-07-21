from __future__ import annotations

from duplicate_question_app._agents.confidence_aggregation import (
    MaxAggregation,
    MeanAggregation,
    MinAggregation,
    ProductAggregation,
)


class TestMeanAggregation:
    def setup_method(self):
        self.strategy = MeanAggregation()

    def test_empty(self):
        assert self.strategy.aggregate([]) == 0.0

    def test_single(self):
        assert self.strategy.aggregate([0.8]) == 0.8

    def test_mean(self):
        from pytest import approx

        assert self.strategy.aggregate([0.8, 1.0, 0.6]) == approx(0.8)

    def test_with_weights(self):
        result = self.strategy.aggregate([0.8, 0.6], weights=[2.0, 1.0])
        expected = (0.8 * 2.0 + 0.6 * 1.0) / 3.0
        assert result == expected

    def test_zero_weights(self):
        result = self.strategy.aggregate([0.8, 0.6], weights=[0.0, 0.0])
        assert result == 0.7  # falls back to unweighted mean


class TestMinAggregation:
    def setup_method(self):
        self.strategy = MinAggregation()

    def test_empty(self):
        assert self.strategy.aggregate([]) == 0.0

    def test_min(self):
        assert self.strategy.aggregate([0.8, 0.4, 0.9]) == 0.4

    def test_weights_ignored(self):
        assert self.strategy.aggregate([0.8, 0.4], weights=[100.0, 0.0]) == 0.4


class TestMaxAggregation:
    def setup_method(self):
        self.strategy = MaxAggregation()

    def test_empty(self):
        assert self.strategy.aggregate([]) == 0.0

    def test_max(self):
        assert self.strategy.aggregate([0.3, 0.9, 0.5]) == 0.9


class TestProductAggregation:
    def setup_method(self):
        self.strategy = ProductAggregation()

    def test_empty(self):
        assert self.strategy.aggregate([]) == 0.0

    def test_product(self):
        assert self.strategy.aggregate([0.8, 0.5, 0.6]) == 0.24

    def test_zero_product(self):
        assert self.strategy.aggregate([0.8, 0.0, 0.6]) == 0.0
