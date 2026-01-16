"""
Unit tests for factual query classifier heuristics.
"""

import pytest

from factual_research_manager import FactualQueryClassifier


@pytest.fixture()
def classifier() -> FactualQueryClassifier:
    return FactualQueryClassifier()


def test_requires_research_detects_company_request(classifier: FactualQueryClassifier):
    query = "What does Kuri robotics do nowadays?"
    assert classifier.requires_research(query) is True


def test_requires_research_detects_year_reference(classifier: FactualQueryClassifier):
    query = "Give me Tesla revenue numbers for 2023"
    assert classifier.requires_research(query) is True


def test_financial_topic_detection(classifier: FactualQueryClassifier):
    query = "Should I invest in emerging market ETFs right now?"
    assert classifier.is_financial_topic(query) is True


def test_extract_entities_returns_capitalized_terms(classifier: FactualQueryClassifier):
    query = "Tell me about OpenAI's collaboration with Microsoft and Tesla"
    entities = classifier.extract_entities(query)
    assert "OpenAI" in entities
    assert "Microsoft" in entities
    assert "Tesla" in entities
