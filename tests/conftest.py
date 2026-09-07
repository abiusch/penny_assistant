"""Explicit offline fixtures for full-pipeline contract tests."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def offline_pipeline_factory(tmp_path, monkeypatch):
    """Construct the real pipeline with scratch storage and no model/audio I/O.

    Patch expensive dependencies BEFORE construction, not afterwards. Keep real
    context, vector persistence, personality, judgment, and prompt generation.
    Embedding values are deterministic stand-ins, not a semantic-quality test.
    """
    real_data = Path(__file__).resolve().parents[1] / 'data'
    def real_file_state():
        return {str(path): (path.stat().st_size, path.stat().st_mtime_ns)
                for path in real_data.rglob('*') if path.is_file()
                and not str(path).endswith(('-wal', '-shm'))}
    original_files = real_file_state()

    import numpy as np
    import research_first_pipeline as module
    from core.stt.factory import STTFactory
    from core.tts.factory import TTSFactory
    from src.memory.embedding_generator import EmbeddingGenerator
    from src.personality import personality_state_cache

    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
    (tmp_path / 'penny_config.json').write_text(json.dumps({
        'llm': {'provider': 'openai_compatible', 'model': 'offline-test',
                'base_url': 'http://127.0.0.1:1/v1', 'api_key': 'test'},
    }))
    monkeypatch.setenv('PENNY_CONFIG', str(tmp_path / 'penny_config.json'))
    monkeypatch.setenv('PENNY_DATA_DIR', str(tmp_path / 'data'))
    monkeypatch.setattr(STTFactory, 'create', lambda config: SimpleNamespace())
    monkeypatch.setattr(TTSFactory, 'create', lambda config: SimpleNamespace())
    monkeypatch.setattr(module, 'EmotionDetectorV2', lambda: SimpleNamespace(
        detect_emotion=lambda text: {'dominant_emotion': 'neutral', 'confidence': 1.0,
                                     'all_scores': {'neutral': 1.0}},
        detect_intensity=lambda text: 0.0,
    ))
    monkeypatch.setattr(EmbeddingGenerator, 'encode',
                        lambda self, text, **kwargs: np.ones(
                            384 if isinstance(text, str) else (len(text), 384), dtype='float32'))
    monkeypatch.setattr(personality_state_cache, '_cache', personality_state_cache.PersonalityStateCache())

    pipelines = []
    def create(**kwargs):
        pipeline = module.ResearchFirstPipeline(**kwargs)
        pipelines.append(pipeline)
        return pipeline
    try:
        yield create
    finally:
        for pipeline in pipelines:
            pipeline.research_manager.shutdown()
        assert real_file_state() == original_files, 'Pipeline test modified production data'


@pytest.fixture
def isolated_pipeline(offline_pipeline_factory):
    pipeline = offline_pipeline_factory()
    return pipeline, pipeline.data_dir
