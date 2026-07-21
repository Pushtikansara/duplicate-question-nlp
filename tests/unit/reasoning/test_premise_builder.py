from __future__ import annotations

from duplicate_question_app._reasoning.premise_builder import DefaultPremiseBuilder
from duplicate_question_app._semantic.representation import SemanticConcept, SemanticRepresentation


class TestPremiseBuilder:
    def setup_method(self):
        self.builder = DefaultPremiseBuilder()

    def _make_rep(
        self,
        concepts=None,
        entities=None,
        actions=None,
        objects=None,
        attributes=None,
        relationships=None,
        intent=None,
        domain=None,
        ambiguities=None,
        constraints=None,
    ):
        return SemanticRepresentation(
            concepts=concepts or [],
            entities=entities or [],
            actions=actions or [],
            objects=objects or [],
            attributes=attributes or [],
            relationships=relationships or [],
            intent_summary=intent,
            domain=domain,
            ambiguities=ambiguities or [],
            constraints=constraints or [],
        )

    def test_empty_representation(self):
        rep = self._make_rep()
        premises = self.builder.extract(rep, "test")
        assert len(premises) == 0

    def test_concept_premises(self):
        rep = self._make_rep(
            concepts=[
                SemanticConcept(id="c1", label="python", normalized_form="python", confidence=0.95),
                SemanticConcept(id="c2", label="programming", normalized_form="programming", confidence=0.85),
            ]
        )
        premises = self.builder.extract(rep, "test")
        concept_premises = [p for p in premises if p.category == "concept"]
        assert len(concept_premises) == 2
        assert concept_premises[0].source == "test"
        assert concept_premises[0].confidence == 0.95

    def test_entity_premises(self):
        rep = self._make_rep(
            entities=[
                {"entity_id": "e1", "text": "Python", "type": "language", "confidence": 0.9},
            ]
        )
        premises = self.builder.extract(rep, "test")
        entity_premises = [p for p in premises if p.category == "entity"]
        assert len(entity_premises) == 1
        assert "Python" in entity_premises[0].text

    def test_intent_and_domain_premises(self):
        rep = self._make_rep(intent="asking for definition", domain="programming")
        premises = self.builder.extract(rep, "test")
        intent_premises = [p for p in premises if p.category == "intent"]
        domain_premises = [p for p in premises if p.category == "domain"]
        assert len(intent_premises) == 1
        assert len(domain_premises) == 1
        assert "asking for definition" in intent_premises[0].text

    def test_ambiguity_premises(self):
        from duplicate_question_app._semantic.representation import AmbiguityEntry

        rep = self._make_rep(
            ambiguities=[
                AmbiguityEntry(type="word_sense", description="bank could mean river or financial", confidence=0.7),
            ]
        )
        premises = self.builder.extract(rep, "test")
        amb_premises = [p for p in premises if p.category == "ambiguity"]
        assert len(amb_premises) == 1
        assert "word_sense" in amb_premises[0].text

    def test_premise_has_id_and_provenance(self):
        rep = self._make_rep(
            concepts=[
                SemanticConcept(id="c1", label="test", normalized_form="test", confidence=0.9),
            ]
        )
        premises = self.builder.extract(rep, "test")
        assert premises[0].id
        assert premises[0].provenance
