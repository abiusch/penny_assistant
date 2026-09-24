"""Fault injection against isolated real FAISS stores; no live user data."""
import pickle
from unittest.mock import Mock

import numpy as np
import pytest

from src.memory.vector_store import VectorStore
from src.memory.errors import MemoryStorageError


@pytest.fixture
def store(tmp_path):
    memory = VectorStore(embedding_dim=4, storage_path=str(tmp_path / 'vectors'))
    memory.add(np.ones(4, dtype='float32'), [{'turn_id': 'retained'}])
    return memory


def reopen(store):
    return VectorStore(embedding_dim=4, storage_path=str(store.storage_path))


@pytest.mark.parametrize('damage', ['missing_index', 'missing_metadata', 'index', 'metadata'])
def test_invalid_store_refuses_startup_without_rewriting_files(store, damage):
    target = store.index_path if 'index' in damage else store.metadata_path
    if damage.startswith('missing'):
        target.unlink()
    else:
        target.write_bytes(b'synthetic corruption')
    before = {p: p.read_bytes() for p in [store.index_path, store.metadata_path] if p.exists()}
    with pytest.raises(RuntimeError, match='memory store'):
        reopen(store)
    assert {p: p.read_bytes() for p in before} == before
    assert target.exists() is (not damage.startswith('missing'))


@pytest.mark.parametrize('damage', ['next_id', 'dimension', 'metadata_type', 'bad_id', 'record_type'])
def test_inconsistent_metadata_refuses_startup(store, damage):
    data = pickle.loads(store.metadata_path.read_bytes())
    if damage == 'next_id':
        data['next_id'] = 2
    elif damage == 'dimension':
        data['embedding_dim'] = 7
    elif damage == 'metadata_type':
        data['id_to_metadata'] = []
    elif damage == 'bad_id':
        data['id_to_metadata'][5] = {}
    else:
        data['id_to_metadata'][0] = 'not a record'
    store.metadata_path.write_bytes(pickle.dumps(data))
    with pytest.raises(RuntimeError, match='memory store'):
        reopen(store)


def test_wrong_embedding_dimension_refuses_existing_store(store):
    with pytest.raises(RuntimeError, match='memory store'):
        VectorStore(embedding_dim=8, storage_path=str(store.storage_path))


@pytest.mark.parametrize('failed_file', ['index', 'metadata'])
def test_save_failure_is_reported_and_store_blocks_further_operations(store, monkeypatch, failed_file):
    from src.memory import vector_store
    write = vector_store.atomic_write
    failed_path = store.index_path if failed_file == 'index' else store.metadata_path
    old_failed_bytes = failed_path.read_bytes()
    def fail(path, data):
        if path == failed_path:
            raise OSError('SYNTHETIC_PRIVATE_DISK_DETAIL')
        return write(path, data)
    monkeypatch.setattr(vector_store, 'atomic_write', fail)
    with pytest.raises(RuntimeError, match='not confirmed') as caught:
        store.add(np.ones(4, dtype='float32'), [{'turn_id': 'unconfirmed'}])
    assert 'SYNTHETIC_PRIVATE' not in str(caught.value)
    assert failed_path.read_bytes() == old_failed_bytes
    for operation in [store.save, store.clear, lambda: store.delete([0]),
                      lambda: store.add(np.ones(4, dtype='float32')),
                      lambda: store.search(np.ones(4, dtype='float32')),
                      lambda: store.get_by_id(0), store.get_stats, store.size]:
        with pytest.raises(RuntimeError, match='memory store'):
            operation()
    monkeypatch.setattr(vector_store, 'atomic_write', write)
    if failed_file == 'index':
        # The old pair is intact and a validated reload permits use again.
        store.load()
        assert store.size() == 1
        assert store.get_by_id(0)['turn_id'] == 'retained'
    else:
        # Individually atomic files are not an atomic pair: refuse mixed counts.
        with pytest.raises(RuntimeError, match='memory store'):
            reopen(store)


def test_failed_reload_does_not_replace_in_memory_state(store):
    original_index = store.index
    original_metadata = store.id_to_metadata
    store.metadata_path.write_bytes(b'broken')
    with pytest.raises(RuntimeError, match='memory store'):
        store.load()
    assert store.index is original_index
    assert store.id_to_metadata is original_metadata
    with pytest.raises(RuntimeError, match='memory store'):
        store.save()


def test_pipeline_discloses_failed_save_without_success_hooks(isolated_pipeline, monkeypatch):
    from src.core.pipeline import State
    from src.memory import vector_store
    p, _ = isolated_pipeline
    p.research_manager.requires_research = lambda text: False
    p.ab_test.assign_group = lambda *args: 'control'
    p.ab_test.is_control_group = lambda *args: True
    p.llm.complete = Mock(return_value='A useful synthetic reply.')
    p._update_personality_from_conversation = Mock()
    p._record_ab_metrics = Mock()
    p._tag_response_for_next_turn = Mock()
    def fail(*args):
        raise OSError('SYNTHETIC_PRIVATE_DISK_DETAIL')
    monkeypatch.setattr(vector_store, 'atomic_write', fail)
    p.state = State.THINKING
    reply = p.think('Hello Penny')
    assert 'A useful synthetic reply.' in reply
    assert 'couldn\'t confirm' in reply
    assert 'SYNTHETIC_PRIVATE' not in reply
    assert p.state == State.SPEAKING
    assert p.context_manager.get_stats()['window_size'] == 0
    p._update_personality_from_conversation.assert_not_called()
    p._record_ab_metrics.assert_not_called()
    p._tag_response_for_next_turn.assert_not_called()


def test_serialization_failure_preserves_both_files(store, monkeypatch):
    from src.memory import vector_store
    before = {p: p.read_bytes() for p in [store.index_path, store.metadata_path]}
    def fail(*args):
        raise ValueError('synthetic serialization failure')
    monkeypatch.setattr(vector_store.pickle, 'dumps', fail)
    with pytest.raises(MemoryStorageError, match='not confirmed'):
        store.add(np.ones(4, dtype='float32'), [{'turn_id': 'unconfirmed'}])
    assert {p: p.read_bytes() for p in before} == before


@pytest.mark.parametrize('operation', ['clear', 'delete'])
def test_destructive_operations_report_failure_without_reuse(store, monkeypatch, operation):
    from src.memory import vector_store
    before = {p: p.read_bytes() for p in [store.index_path, store.metadata_path]}
    def fail(*args):
        raise OSError('synthetic disk failure')
    monkeypatch.setattr(vector_store, 'atomic_write', fail)
    with pytest.raises(MemoryStorageError, match='not confirmed'):
        store.clear() if operation == 'clear' else store.delete([0])
    assert {p: p.read_bytes() for p in before} == before
    with pytest.raises(MemoryStorageError):
        store.search(np.ones(4, dtype='float32'))


def test_pipeline_failed_memory_startup_closes_research_manager(offline_pipeline_factory, monkeypatch):
    import research_first_pipeline as module
    p = offline_pipeline_factory()
    p.semantic_memory.add_conversation_turn('Synthetic question', 'Synthetic reply')
    p.semantic_memory.vector_store.metadata_path.write_bytes(b'broken')
    manager = Mock()
    monkeypatch.setattr(module, 'ResearchManager', lambda: manager)
    with pytest.raises(MemoryStorageError, match='memory store'):
        offline_pipeline_factory()
    manager.shutdown.assert_called_once()
