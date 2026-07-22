"""DomainDetector — detects the domain or topic area of text.

Uses keyword heuristics to classify text into domains like:
  - programming/software
  - data-science/machine-learning
  - devops/infrastructure
  - mathematics/statistics
  - science
  - general
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

from duplicate_question_app._config.logging_setup import get_logger

log = get_logger(__name__)

_DOMAIN_KEYWORDS: dict[str, list[tuple[re.Pattern, float]]] = {
    "programming": [
        (re.compile(r"\b(python|java|javascript|typescript|go|rust|c\+\+|ruby|php)\b", re.IGNORECASE), 1.0),
        (re.compile(r"\b(code|function|class|variable|loop|array|object|method|syntax|compile)\b", re.IGNORECASE), 0.7),
        (re.compile(r"\b(debug|error|exception|bug|stack.?trace|traceback)\b", re.IGNORECASE), 0.6),
        (re.compile(r"\b(api|library|framework|module|package|dependency|import)\b", re.IGNORECASE), 0.6),
        (re.compile(r"\b(install|setup|config|build|deploy|run|execute)\b", re.IGNORECASE), 0.5),
    ],
    "data-science": [
        (
            re.compile(
                r"\b(machine.?learning|deep.?learning|neural.?network|ai|artificial.intelligence)\b", re.IGNORECASE
            ),
            1.0,
        ),
        (
            re.compile(
                r"\b(data|dataset|training|model|feature|label|prediction|classification|regression)\b", re.IGNORECASE
            ),
            0.8,
        ),
        (re.compile(r"\b(tensorflow|pytorch|keras|scikit|sklearn|numpy|pandas)\b", re.IGNORECASE), 0.9),
        (re.compile(r"\b(accuracy|precision|recall|f1|auc|loss|gradient|optimizer|epoch|batch)\b", re.IGNORECASE), 0.7),
    ],
    "devops": [
        (re.compile(r"\b(docker|kubernetes|k8s|terraform|ansible|jenkins|ci/cd|pipeline)\b", re.IGNORECASE), 1.0),
        (re.compile(r"\b(deploy|deployment|server|cloud|aws|azure|gcp|infrastructure)\b", re.IGNORECASE), 0.7),
        (re.compile(r"\b(monitor|alert|log|metric|prometheus|grafana|elk)\b", re.IGNORECASE), 0.6),
    ],
    "mathematics": [
        (re.compile(r"\b(equation|formula|theorem|proof|derivative|integral|matrix|vector)\b", re.IGNORECASE), 0.9),
        (re.compile(r"\b(probability|statistics|distribution|variance|correlation|regression)\b", re.IGNORECASE), 0.8),
        (re.compile(r"\b(calculate|compute|solve|algebra|calculus|geometry|function)\b", re.IGNORECASE), 0.7),
    ],
    "science": [
        (re.compile(r"\b(experiment|hypothesis|theory|study|research|analysis|observation)\b", re.IGNORECASE), 0.7),
        (re.compile(r"\b(physics|chemistry|biology|astronomy|neuroscience|genetics)\b", re.IGNORECASE), 0.9),
        (re.compile(r"\b(lab|measurement|data|sample|control|variable|result)\b", re.IGNORECASE), 0.6),
    ],
}


class DomainDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> tuple[str | None, float]: ...


class DefaultDomainDetector(DomainDetector):
    def __init__(self) -> None:
        self._logger = get_logger(f"{__name__}.DefaultDomainDetector")

    def detect(self, text: str) -> tuple[str | None, float]:
        if not text or not text.strip():
            return None, 0.0
        scores: dict[str, float] = {}
        for domain, patterns in _DOMAIN_KEYWORDS.items():
            score = 0.0
            for pattern, weight in patterns:
                matches = pattern.findall(text)
                score += len(matches) * weight
            if score > 0:
                scores[domain] = score
        if not scores:
            return "general", 0.3
        best = max(scores, key=lambda k: scores[k])
        max_score = scores[best]
        total = sum(scores.values())
        confidence = max_score / total if total > 0 else 0.0
        confidence = min(1.0, confidence * 0.8 + 0.2)
        return best, confidence
