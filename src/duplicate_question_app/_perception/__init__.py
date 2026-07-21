"""Cognitive Perception Engine — the universal entry point for ARES inference.

Raw Text -> Perception Engine -> CognitiveRepresentation -> Future Engines
"""

from __future__ import annotations

from duplicate_question_app._perception.cognitive_representation import (
    CognitiveRepresentation,
    Entity,
    LinguisticFeatures,
    Metadata,
    Negation,
    Sentence,
    Token,
    ValidationReport,
)
from duplicate_question_app._perception.config import PerceptionPipelineConfig
from duplicate_question_app._perception.language_detector import HeuristicLanguageDetector, LanguageDetector
from duplicate_question_app._perception.linguistic_orchestrator import (
    DefaultLinguisticOrchestrator,
    LinguisticOrchestrator,
)
from duplicate_question_app._perception.metadata_extractor import DefaultMetadataExtractor, MetadataExtractor
from duplicate_question_app._perception.normalizer import DefaultTextNormalizer, TextNormalizer
from duplicate_question_app._perception.pipeline import PerceptionPipeline, PipelineResult
from duplicate_question_app._perception.plugin_loader import DefaultPluginLoader, Plugin, PluginLoader
from duplicate_question_app._perception.structural_analyzer import DefaultStructuralAnalyzer, StructuralAnalyzer
from duplicate_question_app._perception.tokenizer_wrapper import Tokenizer, TokenizerFactory
from duplicate_question_app._perception.validator import DefaultValidator, TextValidator

__all__ = [
    "CognitiveRepresentation",
    "DefaultLinguisticOrchestrator",
    "DefaultMetadataExtractor",
    "DefaultPluginLoader",
    "DefaultStructuralAnalyzer",
    "DefaultTextNormalizer",
    "DefaultValidator",
    "Entity",
    "HeuristicLanguageDetector",
    "LanguageDetector",
    "LinguisticFeatures",
    "LinguisticOrchestrator",
    "Metadata",
    "MetadataExtractor",
    "Negation",
    "PerceptionPipeline",
    "PerceptionPipelineConfig",
    "PipelineResult",
    "Plugin",
    "PluginLoader",
    "Sentence",
    "StructuralAnalyzer",
    "TextNormalizer",
    "TextValidator",
    "Token",
    "Tokenizer",
    "TokenizerFactory",
    "ValidationReport",
]
