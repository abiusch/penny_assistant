"""Competing writers use synthetic stores; never open live conversation data."""
import os
from pathlib import Path
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from unittest.mock import Mock

import numpy as np
import pytest

from src.memory.errors import MemoryStorageError
from src.memory.vector_store import VectorStore


def open_store(path, manager=None):
    return VectorStore(4, str(path), consent_manager=manager)


def append(store, name):
    return store.add(np.ones(4, dtype='float32'), [{'turn_id': name}])


def pair_bytes(store):
    return store.index_path.read_bytes(), store.metadata_path.read_bytes()


@pytest.mark.parametrize('operation', ['add', 'save', 'clear', 'delete'])
@pytest.mark.parametrize('with_consent', [False, True])
def test_stale_writer_preserves_newer_conversations(tmp_path, operation, with_consent):
    from src.memory.consent_manager import ConsentManager
    manager = ConsentManager(tmp_path / 'consent.json') if with_consent else None
    current = open_store(tmp_path / 'vectors', manager)
    append(current, 'original')
    stale = open_store(current.storage_path, manager)
    append(current, 'newer')
    before = pair_bytes(current)
    mutations = {'add': lambda: append(stale, 'outdated'), 'save': stale.save,
                 'clear': stale.clear, 'delete': lambda: stale.delete([0])}
    with pytest.raises(MemoryStorageError, match='changed on disk'):
        mutations[operation]()
    assert pair_bytes(current) == before
    assert stale.index.ntotal == 1  # Rejected before modifying the old snapshot.
    assert stale.id_to_metadata[0]['turn_id'] == 'original'
    with pytest.raises(MemoryStorageError):
        stale.search(np.ones(4, dtype='float32'))
    stale.load()
    assert append(stale, 'after-reload') == [2]
    assert [row['turn_id'] for row in open_store(current.storage_path).id_to_metadata.values()] == [
        'original', 'newer', 'after-reload']


def test_two_empty_instances_cannot_replace_first_saved_history(tmp_path):
    first = open_store(tmp_path / 'vectors')
    second = open_store(first.storage_path)
    append(first, 'first-save')
    before = pair_bytes(first)
    with pytest.raises(MemoryStorageError):
        append(second, 'stale-empty')
    assert pair_bytes(first) == before


def test_equal_shape_metadata_change_is_not_overwritten(tmp_path):
    first = open_store(tmp_path / 'vectors')
    append(first, 'original')
    second = open_store(first.storage_path)
    first.id_to_metadata[0]['turn_id'] = 'corrected'
    first.save()
    before = pair_bytes(first)
    with pytest.raises(MemoryStorageError):
        second.save()
    assert pair_bytes(first) == before


def test_equal_shape_index_change_is_not_overwritten(tmp_path):
    first = open_store(tmp_path / 'vectors')
    append(first, 'original')
    second = open_store(first.storage_path)
    first.index.reset()
    first.index.add(np.array([[1, 0, 0, 0]], dtype='float32'))
    first.save()
    before = pair_bytes(first)
    with pytest.raises(MemoryStorageError):
        second.save()
    assert pair_bytes(first) == before


def test_relative_path_keeps_its_identity_after_working_directory_changes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = open_store('vectors')
    append(store, 'first')
    elsewhere = tmp_path / 'elsewhere'
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    append(store, 'second')
    assert open_store(tmp_path / 'vectors').size() == 2
    assert list(elsewhere.iterdir()) == []


def test_external_pair_removal_is_not_treated_as_new_empty_store(tmp_path):
    store = open_store(tmp_path / 'vectors')
    append(store, 'retained')
    store.index_path.unlink()
    store.metadata_path.unlink()
    with pytest.raises(MemoryStorageError):
        store.save()
    assert not store.index_path.exists()
    assert not store.metadata_path.exists()


def test_separate_process_writers_do_not_lose_successful_turns(tmp_path):
    store = open_store(tmp_path / 'vectors')
    append(store, 'original')
    script = '''
import sys
import numpy as np
from src.memory.vector_store import VectorStore
from src.memory.errors import MemoryStorageError
store = VectorStore(4, sys.argv[1])
print('READY', flush=True)
assert sys.stdin.readline().strip() == 'go'
try:
    store.add(np.ones(4, dtype='float32'), [{'turn_id': sys.argv[2]}])
    print('SAVED', flush=True)
except MemoryStorageError:
    print('CONFLICT', flush=True)
'''
    repo = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(repo), str(repo / 'src')]))
    children = []
    try:
        for name in ('one', 'two'):
            children.append(subprocess.Popen(
                [sys.executable, '-c', script, str(store.storage_path), name],
                env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True))
        for child in children:
            assert child.stdout.readline().strip() == 'READY'
        for child in children:
            child.stdin.write('go\n')
            child.stdin.flush()
        results = [child.communicate(timeout=15) for child in children]
        assert all(child.returncode == 0 for child in children), results
        assert sorted(output.strip() for output, _ in results) == ['CONFLICT', 'SAVED']
        saved_name = ('one', 'two')[next(i for i, (out, _) in enumerate(results) if out.strip() == 'SAVED')]
        assert [row['turn_id'] for row in open_store(store.storage_path).id_to_metadata.values()] == [
            'original', saved_name]
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=5)


def test_startup_waits_for_inflight_pair_replacement(tmp_path, monkeypatch):
    from src.memory import vector_store
    store = open_store(tmp_path / 'vectors')
    append(store, 'original')
    index_written = threading.Event()
    release = threading.Event()
    reader_started = threading.Event()
    write = vector_store.atomic_write

    def paused_write(path, data):
        write(path, data)
        if path == store.index_path:
            index_written.set()
            assert release.wait(5)

    def read():
        reader_started.set()
        return open_store(store.storage_path)

    monkeypatch.setattr(vector_store, 'atomic_write', paused_write)
    with ThreadPoolExecutor(max_workers=2) as pool:
        writer = pool.submit(append, store, 'newer')
        try:
            assert index_written.wait(5)
            reader = pool.submit(read)
            assert reader_started.wait(5)
            # A completed read here would expose the temporary mismatched pair.
            from concurrent.futures import wait
            assert not wait([reader], timeout=0.1).done
        finally:
            release.set()
        writer.result(timeout=5)
        assert reader.result(timeout=5).size() == 2


def test_threads_sharing_one_instance_keep_all_successful_turns(tmp_path):
    store = open_store(tmp_path / 'vectors')
    with ThreadPoolExecutor(max_workers=4) as pool:
        ids = list(pool.map(lambda i: append(store, str(i))[0], range(8)))
    reopened = open_store(store.storage_path)
    assert sorted(ids) == list(range(8))
    assert {row['turn_id'] for row in reopened.id_to_metadata.values()} == {str(i) for i in range(8)}


def test_stale_privacy_cleanup_preserves_newer_turns_without_blessing_old_writer(tmp_path):
    current = open_store(tmp_path / 'vectors')
    current.add(np.ones(4, dtype='float32'), [{'turn_id': 'original', 'context': {'emotion': 'sad'}}])
    stale = open_store(current.storage_path)
    current.add(np.ones(4, dtype='float32'), [{'turn_id': 'newer', 'context': {'emotion': 'happy'}}])
    stale.delete_emotional_metadata()
    redacted = open_store(current.storage_path)
    assert [row['turn_id'] for row in redacted.id_to_metadata.values()] == ['original', 'newer']
    assert all('emotion' not in row['context'] for row in redacted.id_to_metadata.values())
    before = pair_bytes(redacted)
    with pytest.raises(MemoryStorageError):
        stale.save()
    assert pair_bytes(redacted) == before


def test_current_privacy_cleanup_allows_owner_to_keep_saving(tmp_path):
    current = open_store(tmp_path / 'vectors')
    current.add(np.ones(4, dtype='float32'), [{'turn_id': 'original', 'context': {'emotion': 'sad'}}])
    current.delete_emotional_metadata()
    assert append(current, 'newer') == [1]
    assert 'emotion' not in open_store(current.storage_path).get_by_id(0)['context']


@pytest.mark.parametrize('failure', ['lock', 'fingerprint'])
def test_coordination_failure_is_typed_and_preserves_disk(tmp_path, monkeypatch, failure):
    store = open_store(tmp_path / 'vectors')
    append(store, 'original')
    before = pair_bytes(store)
    if failure == 'lock':
        @contextmanager
        def fail(*args):
            raise PermissionError('SYNTHETIC_PRIVATE_DETAIL')
            yield
        monkeypatch.setattr(store._store_lock, 'hold', fail)
    else:
        monkeypatch.setattr(store, '_disk_generation', Mock(side_effect=PermissionError('SYNTHETIC_PRIVATE_DETAIL')))
    with pytest.raises(MemoryStorageError) as caught:
        append(store, 'unconfirmed')
    assert 'SYNTHETIC_PRIVATE_DETAIL' not in str(caught.value)
    assert pair_bytes(store) == before
    with pytest.raises(MemoryStorageError):
        store.size()


def test_pipeline_reports_conflict_without_losing_other_pipeline_turn(offline_pipeline_factory):
    from src.core.pipeline import State
    stale = offline_pipeline_factory()
    current = offline_pipeline_factory()
    current.semantic_memory.add_conversation_turn('Newer saved words', 'Retain reply', turn_id='newer')
    before = pair_bytes(current.semantic_memory.vector_store)
    stale.research_manager.requires_research = lambda text: False
    stale.ab_test.assign_group = lambda *args: 'control'
    stale.ab_test.is_control_group = lambda *args: True
    stale.llm.complete = Mock(return_value='A useful synthetic reply.')
    stale._update_personality_from_conversation = Mock()
    stale._record_ab_metrics = Mock()
    stale._tag_response_for_next_turn = Mock()
    stale.state = State.THINKING
    reply = stale.think('Hello Penny')
    assert 'A useful synthetic reply.' in reply and "couldn't confirm" in reply
    assert stale.context_manager.get_stats()['window_size'] == 0
    stale._update_personality_from_conversation.assert_not_called()
    stale._record_ab_metrics.assert_not_called()
    stale._tag_response_for_next_turn.assert_not_called()
    assert pair_bytes(current.semantic_memory.vector_store) == before
    restarted = offline_pipeline_factory()
    assert restarted.semantic_memory.turn_id_to_vector_id == {'newer': 0}
