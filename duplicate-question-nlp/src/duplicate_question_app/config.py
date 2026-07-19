# Backward-compatibility stub.
# This module has been moved to duplicate_question_app._config.
# Please update imports to reference the new location.
from duplicate_question_app._config.settings import *  # noqa: F401, F403
from duplicate_question_app._config.loader import (  # noqa: F401
    get_env,
    clear_config_cache,
    load_all_configs,
)
from duplicate_question_app._config.exceptions import (  # noqa: F401
    DuplicateQuestionAppError,
    ConfigurationError,
    ModelNotFoundError,
    ModelNotReadyError,
    InferenceError,
    DataError,
    DatasetNotFoundError,
    TrainingError,
    CalibrationError,
    EnsembleError,
    RegistryError,
    EvaluationError,
    PreprocessingError,
    ArtifactError,
    LinguistError,
)
