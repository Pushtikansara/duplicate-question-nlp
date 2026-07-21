from enum import IntEnum, auto


class PipelineEvent(IntEnum):
    PIPELINE_STARTED = auto()
    BEFORE_PERCEPTION = auto()
    AFTER_PERCEPTION = auto()
    BEFORE_ROUTING = auto()
    AFTER_ROUTING = auto()
    BEFORE_MEMORY_READ = auto()
    AFTER_MEMORY_READ = auto()
    BEFORE_SEMANTIC = auto()
    AFTER_SEMANTIC = auto()
    BEFORE_REASONING = auto()
    AFTER_REASONING = auto()
    BEFORE_DEBATE = auto()
    AFTER_DEBATE = auto()
    BEFORE_DECISION = auto()
    AFTER_DECISION = auto()
    BEFORE_MEMORY_WRITE = auto()
    AFTER_MEMORY_WRITE = auto()
    PIPELINE_COMPLETED = auto()
    PIPELINE_FAILED = auto()
