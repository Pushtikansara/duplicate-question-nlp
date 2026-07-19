# Backward-compatibility stub.
# This module has been moved to duplicate_question_app.models.embeddings.
# Please update imports to reference the new location.
from duplicate_question_app._models.embeddings import *  # noqa: F401, F403
from duplicate_question_app._models.embeddings import (  # noqa: F401
    _resolve_device,
    _get_threshold,
    _get_sigmoid_params,
)
