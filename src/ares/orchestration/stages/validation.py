from __future__ import annotations

from typing import Any

from ares.orchestration.constants import DEFAULT_MAX_QUESTION_LENGTH, STAGE_INPUT_VALIDATION
from ares.orchestration.context import PipelineState, PredictionInput
from ares.orchestration.exceptions import InputValidationError
from ares.orchestration.interfaces import PipelineStage
from ares.orchestration.metadata import OrchestrationMetadata

_WHITESPACE = "\t\n\r\v\f"


class InputValidationStage(PipelineStage):
    """Validates the prediction input before any analysis runs.

    Enforces the routing-engine contract (non-empty, printable, bounded
    length) plus a threshold sanity range. Rejects malformed input with
    ``InputValidationError``.
    """

    name = STAGE_INPUT_VALIDATION

    def __init__(self, max_question_length: int = DEFAULT_MAX_QUESTION_LENGTH) -> None:
        self.max_question_length = max_question_length

    def run(
        self,
        input: PredictionInput,
        state: PipelineState,
        metadata: OrchestrationMetadata,
    ) -> None:
        self._validate_question(input.question1, "question1")
        self._validate_question(input.question2, "question2")
        threshold = input.request_params.threshold
        if threshold is not None and not (0.0 <= threshold <= 1.0):
            raise InputValidationError(f"Threshold must be within [0.0, 1.0], got {threshold!r}")

    def _validate_question(self, question: Any, field: str) -> None:
        if not isinstance(question, str) or not question.strip():
            raise InputValidationError(f"{field} must be a non-empty string")
        if len(question) > self.max_question_length:
            raise InputValidationError(f"{field} exceeds maximum length of {self.max_question_length} characters")
        for character in question:
            if ord(character) < 32 and character not in _WHITESPACE:
                raise InputValidationError(f"{field} contains non-printable characters")
