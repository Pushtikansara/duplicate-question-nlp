from __future__ import annotations

from typing import Any

import yaml

from ares.adaptive.config_loader import load_adaptive_config
from ares.orchestration.prediction_service import build_default_prediction_service
from tests.unit.adaptive.conftest import FakeEngine, make_assessment

LR = "TF-IDF + Logistic Regression (Week 2)"


def write_adaptive_config(config_dir, enabled: bool = True) -> dict[str, Any]:
    cfg = dict(load_adaptive_config())
    cfg["enabled"] = enabled
    cfg.pop("warmup", None)
    (config_dir / "adaptive_routing.yaml").write_text(yaml.safe_dump(cfg))
    return cfg


class FakeAnalyzer:
    def analyze(self, question1: str, question2: str, **kwargs: Any):
        return make_assessment("easy", 0.1, "low", recommended_strategy="fast_lexical")


def test_adaptive_trace_sections_merged(tmp_path):
    write_adaptive_config(tmp_path)
    engine = FakeEngine(behaviors={LR: (1, 0.95, 0.95, 5.0)})
    service = build_default_prediction_service(tmp_path, engine=engine)

    result = service.predict("what is the capital of france", "what is the capital of france")
    trace = result.to_dict().get("orchestration_trace")

    adaptive = (trace or {}).get("adaptive_routing")
    assert adaptive is not None, "adaptive routing sections should be merged into the trace"
    for section in ("routing", "execution", "adaptive", "evidence", "budget", "final"):
        assert section in adaptive, f"missing trace section {section}"
    assert adaptive["routing"]["selected_model"] == LR
    assert adaptive["final"]["final_model"] == LR
    assert adaptive["final"]["final_strategy"] == "fast_lexical"


def test_adaptive_disabled_no_sections(tmp_path):
    write_adaptive_config(tmp_path, enabled=False)
    engine = FakeEngine(behaviors={LR: (1, 0.95, 0.95, 5.0)})
    service = build_default_prediction_service(tmp_path, engine=engine)

    result = service.predict("A", "B")
    trace = result.to_dict().get("orchestration_trace")
    assert (trace or {}).get("adaptive_routing") is None
