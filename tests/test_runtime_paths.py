"""Launch-directory and independent-store regression tests, entirely offline."""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from cryptography.fernet import InvalidToken


@pytest.mark.parametrize('launch', ['root', 'web_interface', 'elsewhere'])
def test_config_override_is_shared_by_both_loaders(tmp_path, monkeypatch, launch):
    from src.llm.registry import load_llm_config
    from core.llm_router import load_config
    from core.personality import _load_config as load_personality_config
    config = tmp_path / 'selected.json'
    expected = {'llm': {'model': 'synthetic-selected-model'}}
    config.write_text(json.dumps(expected))
    directory = tmp_path / launch
    directory.mkdir()
    (directory / 'penny_config.json').write_text(json.dumps({'llm': {'model': 'decoy'}}))
    monkeypatch.setenv('PENNY_CONFIG', str(config))
    monkeypatch.chdir(directory)
    assert load_llm_config() == expected
    assert load_config() == expected
    assert load_personality_config() == expected


def test_injected_store_reaches_all_pipeline_dependencies(isolated_pipeline):
    pipeline, directory = isolated_pipeline
    root = Path(directory)
    db = root / 'personality_tracking.db'
    assert Path(pipeline.personality_prompt_builder.db_path) == db
    assert Path(pipeline.personality_post_processor.db_path) == db
    assert Path(pipeline.consent_manager.storage_path) == root / 'user_consent.json'
    assert Path(pipeline.ab_test.db_path) == root / 'personality.db'
    assert pipeline.semantic_memory.encryption.key_file == root / '.encryption_key'


def test_personality_cache_does_not_cross_database_boundaries(tmp_path, monkeypatch):
    from personality_tracker import PersonalityTracker
    from src.personality import personality_state_cache
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(personality_state_cache, '_cache', personality_state_cache.PersonalityStateCache())
    first = PersonalityTracker(str(tmp_path / 'first.db'))
    second = PersonalityTracker(str(tmp_path / 'second.db'))
    import sqlite3
    with sqlite3.connect(second.db_path) as conn:
        conn.execute("UPDATE personality_dimensions SET current_value = '0.9' WHERE dimension = 'communication_formality'")
    first_state = asyncio.run(first.get_current_personality_state())
    second_state = asyncio.run(second.get_current_personality_state())
    assert first_state['communication_formality'].current_value == 0.5
    assert second_state['communication_formality'].current_value == 0.9
    assert asyncio.run(first.update_personality_dimension('communication_formality', 0.7, 0.0, 'synthetic'))
    same_store = PersonalityTracker(first.db_path)
    assert asyncio.run(same_store.get_current_personality_state())['communication_formality'].current_value == 0.7
    assert asyncio.run(second.get_current_personality_state())['communication_formality'].current_value == 0.9


@pytest.fixture
def scratch_project(tmp_path, monkeypatch):
    from src import runtime_paths
    project = tmp_path / 'project'
    project.mkdir()
    monkeypatch.setattr(runtime_paths, 'PROJECT_ROOT', project)
    monkeypatch.delenv('PENNY_CONFIG', raising=False)
    monkeypatch.delenv('PENNY_DATA_DIR', raising=False)
    return project


@pytest.mark.parametrize('launch', ['.', 'web_interface', '../unrelated'])
def test_defaults_ignore_launch_directory_and_decoy_config(scratch_project, monkeypatch, launch):
    from src.runtime_paths import RuntimePaths, load_runtime_config
    project = scratch_project
    expected = {'llm': {'model': 'project-model'}}
    (project / 'penny_config.json').write_text(json.dumps(expected))
    directory = (project / launch).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    if directory != project:
        (directory / 'penny_config.json').write_text('{"llm":{"model":"decoy"}}')
    monkeypatch.chdir(directory)
    paths = RuntimePaths.resolve()
    assert paths.config == project / 'penny_config.json'
    assert paths.data == project / 'data'
    assert paths.personality_db == project / 'data/personality_tracking.db'
    assert load_runtime_config() == expected
    assert not (directory / 'data').exists()


def test_precedence_and_relative_overrides_are_project_relative(scratch_project, monkeypatch):
    from src.runtime_paths import RuntimePaths, load_runtime_config
    project = scratch_project
    legacy = project / 'config'
    legacy.mkdir()
    (legacy / 'penny_config.json').write_text('{"selected":"legacy"}')
    assert load_runtime_config()['selected'] == 'legacy'
    (project / 'penny_config.json').write_text('{"selected":"root"}')
    assert load_runtime_config()['selected'] == 'root'
    (project / 'override.json').write_text('{"selected":"environment"}')
    monkeypatch.setenv('PENNY_CONFIG', 'override.json')
    monkeypatch.setenv('PENNY_DATA_DIR', 'alternate-data')
    assert load_runtime_config()['selected'] == 'environment'
    assert load_runtime_config('penny_config.json')['selected'] == 'root'
    paths = RuntimePaths.resolve(data_dir='explicit-data', db_path='db/custom.db')
    assert paths.data == project / 'explicit-data'
    assert paths.personality_db == project / 'db/custom.db'
    assert RuntimePaths.resolve().data == project / 'alternate-data'


@pytest.mark.parametrize('content', [None, '{invalid json', '[]'])
def test_invalid_selected_config_never_falls_back(scratch_project, monkeypatch, content):
    from src.llm.registry import load_llm_config
    from core.llm_router import load_config
    (scratch_project / 'penny_config.json').write_text('{"llm":{"model":"fallback"}}')
    selected = scratch_project / 'selected.json'
    if content is not None:
        selected.write_text(content)
    monkeypatch.setenv('PENNY_CONFIG', str(selected))
    for loader in (load_config, load_llm_config):
        with pytest.raises((FileNotFoundError, ValueError)):
            loader()


def test_separate_legacy_web_store_requires_selection_without_moving_it(scratch_project, monkeypatch):
    from src.runtime_paths import data_path
    legacy = scratch_project / 'web_interface/data'
    legacy.mkdir(parents=True)
    marker = legacy / 'existing-store.txt'
    marker.write_text('synthetic existing data')
    with pytest.raises(ValueError, match='PENNY_DATA_DIR'):
        data_path()
    monkeypatch.setenv('PENNY_DATA_DIR', str(legacy))
    assert data_path() == legacy
    assert marker.read_text() == 'synthetic existing data'
    assert not (scratch_project / 'data').exists()


def test_existing_web_symlink_is_preserved(scratch_project):
    from src.runtime_paths import data_path
    root = scratch_project / 'data'
    root.mkdir()
    web = scratch_project / 'web_interface'
    web.mkdir()
    (web / 'data').symlink_to(root, target_is_directory=True)
    assert data_path() == root
    assert (web / 'data').is_symlink()


def test_independent_pipelines_keep_consent_keys_and_ab_state_separate(
        offline_pipeline_factory, tmp_path):
    first = offline_pipeline_factory(data_dir=tmp_path / 'first')
    second = offline_pipeline_factory(data_dir=tmp_path / 'second')
    first.consent_manager.grant_consent()
    assert not second.consent_manager.is_tracking_enabled()
    assert first.ab_test is not second.ab_test
    assert first.ab_test.db_path != second.ab_test.db_path
    assert first.semantic_memory.encryption.key_file != second.semantic_memory.encryption.key_file
    ciphertext = first.semantic_memory.encryption.encrypt('synthetic-secret')
    with pytest.raises(InvalidToken):
        second.semantic_memory.encryption.decrypt(ciphertext)
    first.semantic_memory.add_conversation_turn('synthetic question', 'synthetic reply')
    assert second.semantic_memory.get_stats()['total_conversations'] == 0


def test_text_observer_uses_pipeline_store_without_creating_cwd_data(
        isolated_pipeline, tmp_path, monkeypatch):
    from personality_observer import PersonalityObserver
    pipeline, _ = isolated_pipeline
    launch = tmp_path / 'text-launch'
    launch.mkdir()
    monkeypatch.chdir(launch)
    observer = PersonalityObserver(db_path=pipeline.db_path)
    for tracker in (observer.slang_tracker, observer.context_engine,
                    observer.effectiveness_analyzer, observer.personality_tracker):
        assert Path(tracker.db_path) == Path(pipeline.db_path)
    assert not (launch / 'data').exists()


def test_invalid_config_fails_before_pipeline_creates_storage(offline_pipeline_factory, tmp_path):
    target = tmp_path / 'must-not-be-created'
    with pytest.raises(FileNotFoundError):
        offline_pipeline_factory(config_path=tmp_path / 'missing.json', data_dir=target)
    assert not target.exists()


@pytest.mark.parametrize('key_content', [None, b'', b'invalid synthetic key'])
def test_existing_store_never_gets_a_replacement_key(offline_pipeline_factory, tmp_path, key_content):
    target = tmp_path / 'existing-store'
    vectors = target / 'embeddings'
    vectors.mkdir(parents=True)
    index = vectors / 'vector_store.index'
    index.write_bytes(b'synthetic existing store; must not be opened')
    key = target / '.encryption_key'
    if key_content is not None:
        key.write_bytes(key_content)
    original = {str(p): p.read_bytes() for p in target.rglob('*') if p.is_file()}
    with pytest.raises((FileNotFoundError, ValueError), match='key'):
        offline_pipeline_factory(data_dir=target)
    assert {str(p): p.read_bytes() for p in target.rglob('*') if p.is_file()} == original


# Fresh interpreters also exercise import layout and adapter-side personality
# loading. Only audio, embeddings, emotion inference and HTTP are replaced.
LAUNCH_PROBE = r'''
import json
from types import SimpleNamespace
from unittest.mock import Mock, patch
import numpy as np
import research_first_pipeline as module
from core.stt.factory import STTFactory
from core.tts.factory import TTSFactory
from src.memory.embedding_generator import EmbeddingGenerator
from src.core.pipeline import State
with patch.object(STTFactory, 'create', lambda cfg: SimpleNamespace(config=cfg)), \
     patch.object(TTSFactory, 'create', lambda cfg: SimpleNamespace(config=cfg)), \
     patch.object(EmbeddingGenerator, 'encode', lambda self, text, **kw: np.ones(384 if isinstance(text, str) else (len(text), 384), dtype='float32')), \
     patch.object(module, 'EmotionDetectorV2', lambda: SimpleNamespace(detect_emotion=lambda text: {'dominant_emotion':'neutral','confidence':1.0,'all_scores':{'neutral':1.0}}, detect_intensity=lambda text: 0.0)), \
     patch('requests.Session.post', return_value=SimpleNamespace(content=b'json', raise_for_status=Mock(), json=lambda: {'choices':[{'message':{'content':'Synthetic reply.'}}]})):
    p = module.ResearchFirstPipeline()
    try:
        # This probe verifies encrypted metadata recovery, so opt in explicitly.
        p.consent_manager.grant_consent()
        p.research_manager.requires_research = lambda text: False
        p.ab_test.assign_group = lambda *args: 'control'
        p.ab_test.is_control_group = lambda *args: True
        before = p.semantic_memory.vector_store.size()
        assert p.semantic_memory.get_stats()['total_conversations'] == before
        if before:
            found = p.semantic_memory.semantic_search('Synthetic', k=1)[0]
            assert found['user_input'] == 'Hello Penny'
            assert found['context']['emotion'] == 'neutral'
            assert p.semantic_memory.get_conversation_by_id(found['turn_id'])['user_input'] == 'Hello Penny'
        p.state = State.THINKING
        assert 'Synthetic reply.' in p.think('Hello Penny')
        assert p.semantic_memory.get_stats()['total_conversations'] == before + 1
        print('PROBE_RESULT=' + json.dumps({'model':p.llm.model, 'config':str(p.paths.config), 'data':p.data_dir, 'before':before, 'after':p.semantic_memory.vector_store.size(), 'stt_model':p.stt.config['llm']['model']}))
    finally:
        p.research_manager.shutdown()
'''


@pytest.mark.timeout(60)
def test_fresh_launches_share_store_and_recover_after_restart(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    config = tmp_path / 'selected.json'
    config.write_text(json.dumps({'llm': {'provider': 'openai_compatible', 'model': 'synthetic-model'}}))
    data = tmp_path / 'selected-data'
    env = dict(os.environ, PENNY_CONFIG=str(config), PENNY_DATA_DIR=str(data),
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1', PENNY_DISABLE_HEALTH_LOOP='1',
               PYTHONPATH=os.pathsep.join([str(repo), str(repo / 'src')]))
    key = None
    for index, launch in enumerate(['root', 'web_interface', 'unrelated']):
        cwd = tmp_path / launch
        cwd.mkdir()
        (cwd / 'penny_config.json').write_text('{"llm":{"model":"decoy"}}')
        result = subprocess.run([sys.executable, '-c', LAUNCH_PROBE], cwd=cwd, env=env,
                                text=True, capture_output=True, timeout=18)
        assert result.returncode == 0, result.stdout + result.stderr
        record = json.loads(next(line.split('=', 1)[1] for line in result.stdout.splitlines()
                                 if line.startswith('PROBE_RESULT=')))
        assert record == {'model': 'synthetic-model', 'stt_model': 'synthetic-model',
                          'config': str(config), 'data': str(data), 'before': index, 'after': index + 1}
        current_key = (data / '.encryption_key').read_bytes()
        assert key is None or current_key == key
        key = current_key
        assert not (cwd / 'data').exists()
