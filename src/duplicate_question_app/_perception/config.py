"""Configuration models for the Cognitive Perception Engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class NormalizerConfig:
    expand_abbreviations: bool = True
    fix_typos: bool = True
    strip_html: bool = True
    strip_urls: bool = True
    strip_emails: bool = True
    strip_emoji: bool = True
    normalize_unicode: bool = True
    lowercase: bool = True


@dataclass(frozen=True)
class LanguageDetectorConfig:
    fallback_language: str = "en"
    confidence_threshold: float = 0.5
    supported_languages: tuple[str, ...] = ("en",)


@dataclass(frozen=True)
class TokenizerConfig:
    strategy: Literal["whitespace", "regex", "wordpiece"] = "whitespace"
    max_length: int = 512
    truncation: bool = True
    lowercase: bool = True


@dataclass(frozen=True)
class StructuralAnalyzerConfig:
    detect_sentences: bool = True
    detect_paragraphs: bool = True
    detect_sections: bool = True
    max_sentences: int = 100


@dataclass(frozen=True)
class LinguisticOrchestratorConfig:
    enable_entity_extraction: bool = True
    enable_negation_detection: bool = True
    enable_contradiction_detection: bool = False
    enable_lexical_analysis: bool = True
    enable_intent_detection: bool = True


@dataclass(frozen=True)
class MetadataExtractorConfig:
    detect_length: bool = True
    detect_question_type: bool = True
    detect_sentiment: bool = False


@dataclass(frozen=True)
class ValidatorConfig:
    min_text_length: int = 1
    max_text_length: int = 10000
    require_non_empty: bool = True


@dataclass(frozen=True)
class PluginLoaderConfig:
    plugin_dirs: tuple[str, ...] = ()
    auto_register: bool = True


@dataclass(frozen=True)
class PerceptionPipelineConfig:
    normalizer: NormalizerConfig = field(default_factory=NormalizerConfig)
    language_detector: LanguageDetectorConfig = field(default_factory=LanguageDetectorConfig)
    tokenizer: TokenizerConfig = field(default_factory=TokenizerConfig)
    structural_analyzer: StructuralAnalyzerConfig = field(default_factory=StructuralAnalyzerConfig)
    linguistic_orchestrator: LinguisticOrchestratorConfig = field(default_factory=LinguisticOrchestratorConfig)
    metadata_extractor: MetadataExtractorConfig = field(default_factory=MetadataExtractorConfig)
    validator: ValidatorConfig = field(default_factory=ValidatorConfig)
    plugin_loader: PluginLoaderConfig = field(default_factory=PluginLoaderConfig)
