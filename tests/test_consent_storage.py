"""Consent enforcement and deletion recovery against isolated real stores."""

import json
import pickle
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
import threading
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

FIELDS = {'emotion', 'emotion_confidence', 'sentiment', 'sentiment_score'}
EMOTION = {'emotion': 'sadness', 'emotion_confidence': 0.9,
           'sentiment': 'negative', 'sentiment_score': -0.8, 'research_used': False}


def seed(p):
    p.consent_manager.grant_consent()
    p.semantic_memory.add_conversation_turn('Synthetic conversation', 'Keep this reply', context=EMOTION)
    p.context_manager.add_turn('Synthetic conversation', 'Keep this reply', metadata=EMOTION)
    from src.memory.emotional_continuity import EmotionalThread
    thread = EmotionalThread('sadness', 0.9, 'synthetic check-in', datetime.now(), 'seed')
    p.emotional_continuity.threads.append(thread)
    p.personality_snapshots.create_snapshot({'formality': 0.5}, [thread.to_dict()], 1)


def test_default_optout_strips_emotion_at_durable_boundary(isolated_pipeline):
    p, _ = isolated_pipeline
    p.semantic_memory.add_conversation_turn('Keep words about sadness', 'Keep this reply', context=EMOTION)
    stored = next(iter(p.semantic_memory.vector_store.id_to_metadata.values()))
    assert not FIELDS.intersection(stored['context'])
    assert stored['user_input'] == 'Keep words about sadness'
    assert stored['context']['research_used'] is False


def test_default_optout_strips_pipeline_cache_metadata(isolated_pipeline):
    p, _ = isolated_pipeline
    from src.core.pipeline import State
    p.llm = SimpleNamespace(complete=lambda *a, **kw: 'Synthetic reply')
    p.research_manager.requires_research = lambda text: False
    p.state = State.THINKING
    p.think('Hello Penny')
    assert not FIELDS.intersection(p.context_manager.get_context_window()[0]['metadata'])


def test_revoke_delete_removes_all_tracking_copies_and_survives_restart(offline_pipeline_factory):
    p = offline_pipeline_factory()
    seed(p)
    p.consent_manager.revoke_consent(delete_data=True)
    assert not p.emotional_continuity.threads
    assert not FIELDS.intersection(p.context_manager.get_context_window()[0]['metadata'])
    assert all(not s.emotional_threads for s in p.personality_snapshots.snapshots)
    restarted = offline_pipeline_factory()
    row = restarted.semantic_memory.semantic_search('Synthetic')[0]
    assert row['user_input'] == 'Synthetic conversation'
    assert row['assistant_response'] == 'Keep this reply'
    assert not FIELDS.intersection(row['context'])
    assert restarted.semantic_memory.vector_store.size() == 1
    assert all(not s.emotional_threads for s in restarted.personality_snapshots.snapshots)
    assert not restarted.consent_manager.is_tracking_enabled()


def test_deletion_without_a_store_handler_cannot_report_success(tmp_path):
    from src.memory.consent_manager import ConsentManager
    manager = ConsentManager(tmp_path / 'consent.json')
    with pytest.raises(RuntimeError, match='deletion'):
        manager.revoke_consent(delete_data=True)


def test_consent_change_updates_live_continuity(isolated_pipeline, monkeypatch):
    p, _ = isolated_pipeline
    monkeypatch.setattr(p.emotion_detector_v2, 'detect_intensity', lambda text: 0.95)
    p.consent_manager.grant_consent()
    p._process_emotion('Synthetic intense emotion')
    assert len(p.emotional_continuity.threads) == 1


def disk_records(p):
    with p.semantic_memory.vector_store.metadata_path.open('rb') as source:
        return list(pickle.load(source)['id_to_metadata'].values())


def test_optin_retains_encrypted_labels_and_revoke_without_delete_keeps_old_disk_data(isolated_pipeline):
    p, _ = isolated_pipeline
    seed(p)
    original = disk_records(p)[0]
    assert original['context']['emotion'] != EMOTION['emotion']
    assert p.semantic_memory.semantic_search('Synthetic')[0]['context']['emotion'] == 'sadness'
    p.consent_manager.revoke_consent(delete_data=False)
    p.semantic_memory.add_conversation_turn('New ordinary words', 'New ordinary reply', context=EMOTION)
    rows = disk_records(p)
    assert rows[0] == original
    assert not FIELDS.intersection(rows[1]['context'])
    assert not FIELDS.intersection(p.semantic_memory.semantic_search('Synthetic')[0]['context'])


@pytest.mark.parametrize('failed_store', ['metadata', 'snapshot'])
def test_failed_deletion_stays_pending_and_restart_retries(offline_pipeline_factory, monkeypatch, failed_store):
    p = offline_pipeline_factory()
    seed(p)
    from src.memory import vector_store
    from src.personality import personality_snapshots
    module = vector_store if failed_store == 'metadata' else personality_snapshots
    original_write = module.atomic_write
    def fail(*args, **kwargs):
        raise OSError('synthetic disk failure')
    monkeypatch.setattr(module, 'atomic_write', fail)
    with pytest.raises(OSError, match='synthetic'):
        p.consent_manager.revoke_consent(delete_data=True)
    assert p.consent_manager.get_preferences()['emotional_deletion_pending'] is True
    assert not p.consent_manager.is_tracking_enabled()
    with pytest.raises(RuntimeError, match='pending'):
        p.consent_manager.grant_consent()
    monkeypatch.setattr(module, 'atomic_write', original_write)
    restarted = offline_pipeline_factory()
    assert restarted.consent_manager.get_preferences()['emotional_deletion_pending'] is False
    assert all(not FIELDS.intersection(row['context']) for row in disk_records(restarted))
    assert all(not s.emotional_threads for s in restarted.personality_snapshots.snapshots)
    assert any(event['event_type'] == 'emotional_data_deleted'
               for event in restarted.consent_manager.get_audit_log())


def test_corrupt_snapshot_prevents_false_deletion_success_and_can_be_retried(
        offline_pipeline_factory):
    p = offline_pipeline_factory()
    seed(p)
    snapshot = p.personality_snapshots.storage_path / 'snapshot_v99.json'
    snapshot.write_text('{invalid synthetic JSON')
    with pytest.raises(ValueError):
        p.consent_manager.revoke_consent(delete_data=True)
    with pytest.raises(ValueError):
        offline_pipeline_factory()
    assert p.consent_manager.get_preferences()['emotional_deletion_pending'] is True
    snapshot.write_text(json.dumps({'version': 99, 'timestamp': datetime.now().isoformat(),
                                    'personality_state': {}, 'emotional_threads': [], 'conversation_count': 1}))
    restarted = offline_pipeline_factory()
    assert not restarted.consent_manager.get_preferences()['emotional_deletion_pending']


def test_consent_write_failure_is_reported_and_never_claims_deletion(isolated_pipeline, monkeypatch):
    p, _ = isolated_pipeline
    seed(p)
    from src.memory import consent_manager
    before = p.consent_manager.storage_path.read_bytes()
    def fail(*args):
        raise OSError('synthetic consent write failure')
    monkeypatch.setattr(consent_manager, 'atomic_write', fail)
    with pytest.raises(RuntimeError, match='not confirmed'):
        p.consent_manager.revoke_consent(delete_data=True)
    assert p.consent_manager.storage_path.read_bytes() == before
    assert not p.consent_manager.is_tracking_enabled()
    assert not any(event['event_type'] == 'emotional_data_deleted'
                   for event in p.consent_manager.get_audit_log())


def test_older_instance_cannot_restore_deleted_metadata_even_after_regrant(offline_pipeline_factory):
    p = offline_pipeline_factory()
    seed(p)
    old = offline_pipeline_factory()
    old_snapshot = old.personality_snapshots.get_latest()
    old.context_manager.add_turn('Old cached words', 'reply', metadata=EMOTION)
    p.consent_manager.revoke_consent(delete_data=True)
    p.consent_manager.grant_consent()
    assert not old.personality_snapshots.rollback_to_version(1).emotional_threads
    old.semantic_memory.add_conversation_turn('New opted-in words', 'reply', context=EMOTION)
    old.personality_snapshots._save_snapshot(old_snapshot)
    assert not FIELDS.intersection(disk_records(old)[0]['context'])
    assert 'emotion' in disk_records(old)[1]['context']
    assert not old.context_manager.get_emotional_trajectory()
    assert json.loads((old.personality_snapshots.storage_path / 'snapshot_v1.json').read_text())['emotional_threads'] == []


def test_delete_is_idempotent_and_preserves_vectors_keys_and_unrelated_files(isolated_pipeline):
    p, _ = isolated_pipeline
    seed(p)
    unchanged = [p.semantic_memory.vector_store.index_path, p.semantic_memory.encryption.key_file,
                 Path(p.db_path)]
    marker = Path(p.data_dir) / 'unrelated.txt'
    marker.write_text('leave me alone')
    unchanged.append(marker)
    before = {path: path.read_bytes() for path in unchanged}
    p.consent_manager.revoke_consent(delete_data=True)
    p.consent_manager.revoke_consent(delete_data=True)
    assert all(path.read_bytes() == content for path, content in before.items())
    assert p.semantic_memory.vector_store.size() == 1
    assert disk_records(p)[0]['assistant_response'] == 'Keep this reply'


def test_revoke_during_generation_is_checked_at_persistence(isolated_pipeline):
    p, _ = isolated_pipeline
    from src.core.pipeline import State
    p.consent_manager.grant_consent()
    def complete(*args, **kwargs):
        p.consent_manager.revoke_consent(delete_data=True)
        return 'Synthetic normal reply'
    p.llm = SimpleNamespace(complete=complete)
    p.research_manager.requires_research = lambda text: False
    p.state = State.THINKING
    assert 'Synthetic normal reply' in p.think('Hello Penny')
    assert not FIELDS.intersection(disk_records(p)[0]['context'])
    assert not FIELDS.intersection(p.context_manager.get_context_window()[0]['metadata'])


def test_threaded_write_finishes_before_deletion_returns(isolated_pipeline, monkeypatch):
    p, _ = isolated_pipeline
    seed(p)
    entered = threading.Event()
    release = threading.Event()
    revoke_started = threading.Event()
    store = p.semantic_memory.vector_store
    save = store.save
    def paused_save():
        entered.set()
        assert release.wait(5)
        save()
    monkeypatch.setattr(store, 'save', paused_save)
    def revoke():
        revoke_started.set()
        p.consent_manager.revoke_consent(delete_data=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        write = pool.submit(p.semantic_memory.add_conversation_turn, 'Concurrent words', 'reply', context=EMOTION)
        try:
            assert entered.wait(5)
            deletion = pool.submit(revoke)
            assert revoke_started.wait(5)
            assert not deletion.done()
        finally:
            release.set()
        write.result(timeout=5)
        deletion.result(timeout=5)
    assert all(not FIELDS.intersection(row['context']) for row in disk_records(p))


@pytest.mark.parametrize('data', ['{invalid', '[]', '{"preferences": []}'])
def test_corrupt_consent_fails_closed_before_pipeline_opens_stores(offline_pipeline_factory, tmp_path, data):
    root = tmp_path / 'corrupt-consent'
    root.mkdir()
    (root / 'user_consent.json').write_text(data)
    with pytest.raises(RuntimeError, match='tracking is disabled'):
        offline_pipeline_factory(data_dir=root)
    assert sorted(path.name for path in root.iterdir()) == ['user_consent.json']


def test_completion_record_failure_retries_already_redacted_data(offline_pipeline_factory, monkeypatch):
    p = offline_pipeline_factory()
    seed(p)
    from src.memory import consent_manager
    write = consent_manager.atomic_write
    def fail_completion(path, data):
        if not json.loads(data)['preferences']['emotional_deletion_pending']:
            raise OSError('synthetic completion failure')
        write(path, data)
    monkeypatch.setattr(consent_manager, 'atomic_write', fail_completion)
    with pytest.raises(RuntimeError, match='not confirmed'):
        p.consent_manager.revoke_consent(delete_data=True)
    assert p.consent_manager.get_preferences()['emotional_deletion_pending']
    assert not FIELDS.intersection(disk_records(p)[0]['context'])
    monkeypatch.setattr(consent_manager, 'atomic_write', write)
    restarted = offline_pipeline_factory()
    assert not restarted.consent_manager.get_preferences()['emotional_deletion_pending']


def test_atomic_record_failure_preserves_original_and_removes_temp_file(tmp_path, monkeypatch):
    from src.memory import storage_io
    path = tmp_path / 'record.json'
    path.write_bytes(b'original synthetic bytes')
    def fail(*args):
        raise OSError('synthetic replace failure')
    monkeypatch.setattr(storage_io.os, 'replace', fail)
    with pytest.raises(OSError):
        storage_io.atomic_write(path, b'new synthetic bytes')
    assert path.read_bytes() == b'original synthetic bytes'
    assert list(tmp_path.iterdir()) == [path]


def test_other_process_write_is_serialized_with_deletion(isolated_pipeline):
    p, _ = isolated_pipeline
    seed(p)
    repo = Path(__file__).resolve().parents[1]
    script = '''
import sys
from src.memory.consent_manager import ConsentManager
from src.memory.vector_store import VectorStore
manager = ConsentManager(sys.argv[1])
store = VectorStore(storage_path=sys.argv[2], consent_manager=manager)
with manager.guard():
    print('LOCKED', flush=True)
    assert sys.stdin.readline().strip() == 'release'
    store.save()
'''
    env = dict(os.environ, PYTHONPATH=os.pathsep.join([str(repo), str(repo / 'src')]))
    child = subprocess.Popen([sys.executable, '-c', script, str(p.consent_manager.storage_path),
                              str(p.semantic_memory.vector_store.storage_path)],
                             env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    started = threading.Event()
    def revoke():
        started.set()
        p.consent_manager.revoke_consent(delete_data=True)
    try:
        assert child.stdout.readline().strip() == 'LOCKED'
        with ThreadPoolExecutor(max_workers=1) as pool:
            deletion = pool.submit(revoke)
            try:
                assert started.wait(5)
                assert not deletion.done()
            finally:
                output, error = child.communicate('release\n', timeout=10)
            deletion.result(timeout=5)
        assert child.returncode == 0, output + error
        assert not FIELDS.intersection(disk_records(p)[0]['context'])
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=5)
