"""Conversation identity survives restart in isolated, synthetic vector stores."""

from datetime import datetime
from types import SimpleNamespace

import numpy as np
import pytest


@pytest.fixture
def memory_factory(tmp_path, monkeypatch):
    from src.memory import semantic_memory
    from src.memory.consent_manager import ConsentManager

    # Equal embeddings deliberately exercise tied similarity scores.
    generator = SimpleNamespace(embedding_dim=4, encode=lambda text: np.ones(4, dtype='float32'))
    monkeypatch.setattr(semantic_memory, 'get_embedding_generator', lambda: generator)

    def create():
        return semantic_memory.SemanticMemory(
            embedding_dim=4, encrypt_sensitive=False,
            storage_path=str(tmp_path / 'embeddings' / 'vector_store'),
            consent_manager=ConsentManager(tmp_path / 'user_consent.json'),
        )
    return create


def test_restart_restores_count_and_lookup_without_rewriting_store(memory_factory):
    memory = memory_factory()
    when = datetime(2026, 1, 2, 3, 4, 5)
    memory.add_conversation_turn('Synthetic question', 'Synthetic reply', turn_id='first', timestamp=when)
    memory.add_conversation_turn('Another question', 'Another reply', turn_id='second')
    paths = [memory.vector_store.index_path, memory.vector_store.metadata_path]
    original = {path: path.read_bytes() for path in paths}

    restarted = memory_factory()

    assert restarted.get_stats()['total_conversations'] == 2
    assert restarted.get_conversation_by_id('first') == {
        'turn_id': 'first', 'user_input': 'Synthetic question',
        'assistant_response': 'Synthetic reply', 'timestamp': when.isoformat(),
    }
    assert restarted.get_conversation_by_id('second')['assistant_response'] == 'Another reply'
    assert {path: path.read_bytes() for path in paths} == original


def test_add_after_restart_preserves_existing_identity(memory_factory):
    memory = memory_factory()
    memory.add_conversation_turn('First question', 'First reply', turn_id='first')
    restarted = memory_factory()
    restarted.add_conversation_turn('Second question', 'Second reply', turn_id='second')
    assert restarted.get_stats()['total_conversations'] == 2
    again = memory_factory()
    assert again.get_stats()['total_conversations'] == 2
    assert again.get_conversation_by_id('first')['assistant_response'] == 'First reply'
    assert again.get_conversation_by_id('second')['assistant_response'] == 'Second reply'


def test_delete_by_id_after_restart_stays_deleted(memory_factory):
    memory = memory_factory()
    memory.add_conversation_turn('Remove question', 'Remove reply', turn_id='remove')
    memory.add_conversation_turn('Keep question', 'Keep reply', turn_id='keep')
    restarted = memory_factory()
    restarted.delete_conversation('remove')
    again = memory_factory()
    assert again.get_conversation_by_id('remove') is None
    assert again.get_stats()['total_conversations'] == 1
    assert again.get_conversation_by_id('keep')['assistant_response'] == 'Keep reply'


def test_restart_skips_metadata_without_a_turn_id(memory_factory):
    memory = memory_factory()
    memory.vector_store.add(np.ones((2, 4), dtype='float32'), metadata=[{}, {'turn_id': None}])
    memory.add_conversation_turn('Valid question', 'Valid reply', turn_id='valid')
    restarted = memory_factory()
    assert restarted.get_stats()['total_conversations'] == 1
    assert restarted.get_conversation_by_id('valid')['assistant_response'] == 'Valid reply'
    assert restarted.get_conversation_by_id('unknown') is None


def test_empty_and_cleared_stores_restart_empty(memory_factory):
    memory = memory_factory()
    assert memory.get_stats()['total_conversations'] == 0
    memory.add_conversation_turn('Synthetic question', 'Synthetic reply', turn_id='first')
    memory.clear()
    restarted = memory_factory()
    assert restarted.get_stats()['total_conversations'] == 0
    assert restarted.get_conversation_by_id('first') is None


@pytest.mark.parametrize('restart', [False, True])
def test_similar_conversations_excludes_source_by_identity_with_tied_scores(memory_factory, restart):
    memory = memory_factory()
    for turn_id in ['first', 'second', 'third']:
        memory.add_conversation_turn('Synthetic question', 'Synthetic reply', turn_id=turn_id)
    if restart:
        memory = memory_factory()
    for turn_id in ['first', 'second', 'third']:
        results = memory.find_similar_conversations(turn_id, k=2)
        assert {result['turn_id'] for result in results} == {'first', 'second', 'third'} - {turn_id}
    assert memory.find_similar_conversations('missing') == []
