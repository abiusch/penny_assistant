"""Offline probes for the September 6 review, not a production regression suite.

Run with: .venv/bin/python docs/reviews/2026-09-06_review_probes.py
Assertions deliberately confirm the reviewed defects at the audit's git
revision, even after fixes land. Extracted methods are compiled unchanged from
that revision, avoiding full-pipeline import side effects. Production regression
tests instead assert desired behavior against the current code.
No real model, network, audio, or user database is accessed.
"""
import ast
import asyncio
import importlib.util
import json
import logging
import os
from pathlib import Path
import sys
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import Mock
import time

ROOT = Path(__file__).resolve().parents[2]
SOURCE_REVISION = 'dc416fa'
logging.basicConfig(level=logging.CRITICAL)


def read_source(relative):
    return subprocess.check_output(
        ['git', 'show', f'{SOURCE_REVISION}:{relative}'], cwd=ROOT, text=True)


def load_file(relative, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(read_source(relative), str(ROOT / relative), 'exec'), module.__dict__)
    return module


def extract(relative, cls, method, extra=None):
    tree = ast.parse(read_source(relative))
    parent = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls)
    node = next(n for n in parent.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == method)
    namespace = dict(asyncio=asyncio, time=time, logger=logging.getLogger('probe'))
    namespace.update(extra or {})
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(ROOT / relative), 'exec'), namespace)
    return namespace[method]


def main():
    print(f'Reproducing the audit snapshot at {SOURCE_REVISION}')
    orchestrator = load_file('src/tools/tool_orchestrator.py', 'review_orchestrator')
    parser = orchestrator.ToolCallParser()
    nested = '<|channel|>commentary<|message|>{"tool":"math.calc","args":{"expression":"2+2"}}'
    assert isinstance(parser.parse(nested), orchestrator.FinalAnswer)
    print('CONFIRMED: advertised nested tool call is parsed as a final answer')

    build = extract('research_first_pipeline.py', 'ResearchFirstPipeline', '_build_and_generate')
    prompts, executions = [], []
    def llm_complete(prompt, **kwargs):
        prompts.append(prompt)
        return '<|channel|>calculator<|message|>{"expression":"2+2"}'
    engine = orchestrator.ToolOrchestrator(max_iterations=3)
    engine.register_tool('math.calc', lambda args: executions.append(args) or 'UNIQUE_TOOL_RESULT_4')
    instance = SimpleNamespace(
        llm=SimpleNamespace(complete=llm_complete), tool_orchestrator=engine,
        context_manager=SimpleNamespace(get_stats=lambda: {}),
        tool_registry=SimpleNamespace(get_tool_manifest=lambda: ''),
    )
    ctx = SimpleNamespace(is_control=True, emotion_result=None, emotional_context='',
                          research_required=False, research_result=None, research_context='',
                          tone='neutral', conversation_context='', semantic_results=[])
    response = build(instance, 'You are Penny.', 'Calculate two plus two', ctx)
    assert len(executions) == 3 and len(set(prompts)) == 1
    assert all('UNIQUE_TOOL_RESULT_4' not in p for p in prompts)
    assert 'rephrase' in response
    print('CONFIRMED: real prompt builder repeats identical prompt and tool execution 3 times; tool result never reaches LLM')

    safety = load_file('src/tools/tool_safety.py', 'review_safety')
    wrapped = safety.SafeToolWrapper().wrap_tool('math.calc', lambda args: '4')
    with ThreadPoolExecutor(max_workers=1) as pool:
        try:
            pool.submit(wrapped, {'expression': '2+2'}).result()
        except ValueError as error:
            assert 'signal only works in main thread' in str(error)
            print('CONFIRMED: valid calculator call fails in a request-style worker thread')
        else:
            raise AssertionError('Expected Unix signal failure; probe is intended for macOS/Linux')

    persist = extract('research_first_pipeline.py', 'ResearchFirstPipeline', '_persist_turn')
    captured = []
    memory = SimpleNamespace(add_conversation_turn=lambda **kw: captured.append(kw),
                             get_stats=lambda: {'total_conversations': 1})
    instance = SimpleNamespace(
        consent_manager=SimpleNamespace(is_tracking_enabled=lambda: False),
        context_manager=SimpleNamespace(add_turn=lambda **kw: None),
        semantic_memory=memory, hebbian=None,
        _update_personality_from_conversation=lambda *args: None,
        personality_snapshots=SimpleNamespace(should_snapshot=lambda count: False),
    )
    emotion = SimpleNamespace(primary_emotion='sadness', confidence=0.9,
                              sentiment='negative', sentiment_score=-0.7)
    persist(instance, 'Synthetic input', 'Synthetic answer', emotion, False, False,
            'treatment', time.time(), None)
    assert captured[0]['context']['emotion'] == 'sadness'
    print('CONFIRMED: persistence receives emotion metadata with tracking consent disabled')

    consent_module = load_file('src/memory/consent_manager.py', 'review_consent')
    with tempfile.TemporaryDirectory() as tmp:
        manager = consent_module.ConsentManager(str(Path(tmp) / 'consent.json'))
        marker = Path(tmp) / 'synthetic_emotion_record.json'
        marker.write_text('{"emotion":"sadness"}')
        manager.grant_consent()
        manager.revoke_consent(delete_data=True)
        assert marker.exists() and not manager.is_tracking_enabled()
    print('CONFIRMED: revoke_consent(delete_data=True) only updates preferences/audit; no deletion is wired')

    complete = extract('src/adapters/llm/openai_compat.py', 'OpenAICompatLLM', 'complete')
    session = SimpleNamespace(post=Mock(side_effect=RuntimeError('synthetic outage')))
    instance = SimpleNamespace(_session=session, _chat_url=lambda: 'https://invalid.example',
                               api_key='synthetic', model='synthetic', temperature=0.5,
                               presence_penalty=0, frequency_penalty=0, max_tokens=10, timeout=1)
    # Stub optional prompt import before invoking the actual adapter method.
    previous = sys.modules.get('personality_prompt_builder')
    sys.modules['personality_prompt_builder'] = SimpleNamespace(get_personality_prompt=lambda *a, **k: '')
    try:
        result = complete(instance, 'SYNTHETIC_PRIVATE_MEMORY', system_prompt='test')
    finally:
        if previous is None:
            del sys.modules['personality_prompt_builder']
        else:
            sys.modules['personality_prompt_builder'] = previous
    assert 'SYNTHETIC_PRIVATE_MEMORY' in result and '[llm error]' in result
    print('CONFIRMED: LLM failure returns the complete input prompt as response text')

    # Exercise actual save/load methods using a minimal fake index backend.
    # This verifies control flow on I/O failures, not FAISS performance/format.
    save = extract('src/memory/vector_store.py', 'VectorStore', 'save',
                   {'faiss': SimpleNamespace(write_index=Mock(side_effect=OSError('synthetic disk failure')))})
    store = SimpleNamespace(index=SimpleNamespace(ntotal=1), index_path='unused')
    assert save(store) is None
    print('CONFIRMED: vector save swallows disk error and returns no failure signal')

    registry = load_file('src/llm/registry.py', 'review_llm_registry')
    original = Path.cwd()
    try:
        os.chdir(ROOT)
        root_config = registry.load_llm_config()
        os.chdir(ROOT / 'web_interface')
        web_config = registry.load_llm_config()
    finally:
        os.chdir(original)
    assert root_config.get('llm') and web_config == {'llm': {}}
    print('CONFIRMED: documented web-directory launch misses the root LLM config')
    print('All 8 offline defect probes reproduced; production pipeline was never constructed.')


if __name__ == '__main__':
    main()
