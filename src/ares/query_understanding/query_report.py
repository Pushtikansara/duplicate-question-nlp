from __future__ import annotations

from ares.query_understanding.entity_report import EntityReport
from ares.query_understanding.query_models import QueryAnalysis


class QueryReport:
    def generate(self, analysis: QueryAnalysis) -> str:
        lines = []
        lines.append("=" * 64)
        lines.append("  QUERY UNDERSTANDING REPORT")
        lines.append("=" * 64)
        lines.append("")

        self._write_pair_info(lines, analysis)
        self._write_question_types(lines, analysis)
        self._write_entity_analysis(lines, analysis)
        self._write_properties(lines, "Question 1", analysis.metadata_1, analysis)
        self._write_properties(lines, "Question 2", analysis.metadata_2, analysis)
        self._write_similarity(lines, analysis)
        self._write_complexity(lines, analysis)
        self._write_readability(lines, analysis)
        self._write_processing(lines, analysis)

        return "\n".join(lines)

    def generate_short(self, analysis: QueryAnalysis) -> str:
        lines = []
        lines.append(f"Q1: {analysis.original_question_1[:80]}")
        lines.append(f"Q2: {analysis.original_question_2[:80]}")
        qt = analysis.question_type
        lines.append(f"  Types: {qt.question_1_type}/{qt.question_2_type} ({qt.pair_type})")
        lines.append(f"  Words: {analysis.metadata_1.word_count}/{analysis.metadata_2.word_count}")
        lines.append(f"  Overlap: {analysis.similarity.word_overlap_ratio:.1%}")
        lines.append(f"  Language: {analysis.metadata_1.language}/{analysis.metadata_2.language}")
        lines.append(f"  Complexity: {analysis.complexity_1.overall:.2f}/{analysis.complexity_2.overall:.2f}")
        if analysis.metadata_1.contains_urls or analysis.metadata_2.contains_urls:
            lines.append("  Contains URLs")
        if analysis.metadata_1.contains_code or analysis.metadata_2.contains_code:
            lines.append("  Contains code")
        if analysis.metadata_1.contains_emoji or analysis.metadata_2.contains_emoji:
            lines.append("  Contains emoji")
        entity_section = EntityReport().generate_short(analysis.entity_analysis)
        if entity_section:
            lines.append(f"  {entity_section.replace(chr(10), '  ')}")
        lines.append(f"  Processing: {analysis.processing_time_ms:.1f}ms")
        return "\n".join(lines)

    def _write_entity_analysis(self, lines: list[str], analysis: QueryAnalysis) -> None:
        section = EntityReport().generate_section(analysis.entity_analysis)
        lines.append(section)

    def _write_question_types(self, lines: list[str], analysis: QueryAnalysis) -> None:
        qt = analysis.question_type
        lines.append("  Question Types")
        lines.append(f"    Q1 Type: {qt.question_1_type}")
        lines.append(f"    Q2 Type: {qt.question_2_type}")
        lines.append(f"    Pair Type: {qt.pair_type}")
        lines.append(f"    Confidence: {qt.classification_confidence:.4f}")
        lines.append("")

    def _write_pair_info(self, lines: list[str], analysis: QueryAnalysis) -> None:
        lines.append("  Question Pair")
        lines.append(f"    Q1: {analysis.original_question_1}")
        lines.append(f"    Q2: {analysis.original_question_2}")
        lines.append(f"    N1: {analysis.normalized_question_1}")
        lines.append(f"    N2: {analysis.normalized_question_2}")
        lines.append("")

    def _write_metadata_section(self, lines: list[str], label: str, tag: str, analysis: QueryAnalysis) -> None:
        meta = analysis.metadata_1 if tag == "1" else analysis.metadata_2
        lines.append(f"  Basic Properties ({label})")
        items = [
            ("Length", f"{meta.length} chars ({meta.word_count} words, {meta.sentence_count} sentences)"),
            ("Avg Word Length", f"{meta.avg_word_length:.2f} chars"),
            ("Language", meta.language),
            ("Capitalization", f"{meta.capitalization_ratio:.1%} uppercase"),
            ("Repeated Chars", f"{meta.repeated_char_ratio:.4f}"),
            ("Stopword Ratio", f"{meta.stopword_ratio:.1%}"),
        ]
        self._write_flagged_items(lines, meta, items)
        lines.append("")

    def _write_properties(self, lines: list[str], label: str, meta, analysis: QueryAnalysis) -> None:
        lines.append(f"  {label}")
        lines.append(f"    Length: {meta.length} chars")
        lines.append(f"    Words: {meta.word_count}")
        lines.append(f"    Sentences: {meta.sentence_count}")
        lines.append(f"    Avg Word Length: {meta.avg_word_length:.2f}")
        lines.append(f"    Language: {meta.language}")
        lines.append(f"    Capitalization Ratio: {meta.capitalization_ratio:.2%}")
        lines.append(f"    Repeated Char Ratio: {meta.repeated_char_ratio:.4f}")
        lines.append(f"    Stopword Ratio: {meta.stopword_ratio:.1%}")

        flags = []
        if meta.contains_numbers:
            flags.append("numbers")
        if meta.contains_dates:
            flags.append("dates")
        if meta.contains_urls:
            flags.append("URLs")
        if meta.contains_email:
            flags.append("email")
        if meta.contains_code:
            flags.append("code")
        if meta.contains_emoji:
            flags.append("emoji")
        if meta.contains_special_chars:
            flags.append("special chars")
        if flags:
            lines.append(f"    Contains: {', '.join(flags)}")
        lines.append("")

    def _write_similarity(self, lines: list[str], analysis: QueryAnalysis) -> None:
        sim = analysis.similarity
        lines.append("  Similarity Features")
        lines.append(f"    Length Difference: {sim.length_difference} chars")
        lines.append(f"    Word Overlap: {sim.word_overlap_ratio:.1%}")
        lines.append(f"    Character Overlap: {sim.char_overlap_ratio:.1%}")
        lines.append(f"    Unique Word Ratio (Q1): {sim.unique_word_ratio:.1%}")
        lines.append(f"    Question Ratio (Q1/Q2): {sim.question_ratio:.2f}")
        lines.append(f"    Stopword Overlap: {sim.stopword_overlap_ratio:.1%}")
        lines.append(f"    Punctuation Similarity: {sim.punctuation_similarity:.2%}")
        lines.append(f"    Capitalization Similarity: {sim.capitalization_similarity:.2%}")

        shared = []
        if sim.numeric_overlap:
            shared.append("numbers")
        if sim.contains_same_url:
            shared.append("URLs")
        if sim.contains_same_email:
            shared.append("email")
        if sim.contains_same_code:
            shared.append("code")
        if shared:
            lines.append(f"    Both contain: {', '.join(shared)}")
        lines.append("")

    def _write_complexity(self, lines: list[str], analysis: QueryAnalysis) -> None:
        lines.append("  Complexity Scores")
        for label, comp in [("Q1", analysis.complexity_1), ("Q2", analysis.complexity_2)]:
            lines.append(
                f"    {label}: Overall={comp.overall:.2f} "
                f"Lexical={comp.lexical:.2f} "
                f"Syntactic={comp.syntactic:.2f} "
                f"Technical={comp.technical:.2f}"
            )
        lines.append("")

    def _write_readability(self, lines: list[str], analysis: QueryAnalysis) -> None:
        lines.append("  Readability")
        for label, read in [("Q1", analysis.readability_1), ("Q2", analysis.readability_2)]:
            fre = read.flesch_reading_ease
            level = self._readability_level(fre)
            lines.append(f"    {label}: Flesch={fre:.1f} ({level}), Complex words={read.complex_word_count}")
        lines.append("")

    def _write_processing(self, lines: list[str], analysis: QueryAnalysis) -> None:
        lines.append("  Processing")
        lines.append(f"    Timestamp: {analysis.timestamp}")
        lines.append(f"    Duration: {analysis.processing_time_ms:.2f}ms")
        lines.append(f"    Version: {analysis.version}")
        lines.append("")
        lines.append("=" * 64)

    def _write_flagged_items(self, lines: list[str], meta, items: list[tuple[str, str]]) -> None:
        for label, value in items:
            lines.append(f"    {label}: {value}")

    def _readability_level(self, fre: float) -> str:
        if fre >= 90:
            return "Very Easy"
        elif fre >= 80:
            return "Easy"
        elif fre >= 70:
            return "Fairly Easy"
        elif fre >= 60:
            return "Standard"
        elif fre >= 50:
            return "Fairly Difficult"
        elif fre >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
