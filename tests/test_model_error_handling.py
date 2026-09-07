"""Offline failures through the actual model adapter and conversation pipeline."""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
import requests

from src.adapters.llm.openai_compat import OpenAICompatLLM
from src.llm.errors import MODEL_FAILURE_REPLY, ModelGenerationError
from src.tools.tool_orchestrator import ToolOrchestrator

PRIVATE = 'SYNTHETIC_PRIVATE_PROMPT_871'
DETAIL = 'SYNTHETIC_PROVIDER_DETAIL_629'


def response(payload):
    return SimpleNamespace(content=b'json', json=Mock(return_value=payload),
                           raise_for_status=Mock())


def text_response(text):
    return response({'choices': [{'message': {'content': text}}]})


@pytest.fixture
def client(monkeypatch):
    import personality_prompt_builder
    monkeypatch.setattr(personality_prompt_builder, 'get_personality_prompt',
                        lambda *a, **kw: 'Synthetic system prompt.')
    adapter = OpenAICompatLLM({'llm': {'model': 'offline-test', 'timeout': 3}})
    adapter._session = Mock()
    return adapter


@pytest.mark.parametrize('failure', [
    requests.ConnectionError(DETAIL),
    requests.Timeout(DETAIL),
    requests.HTTPError(DETAIL),
    ValueError(DETAIL),
])
def test_adapter_raises_without_echoing_prompt_or_provider_detail(client, failure, caplog):
    caplog.set_level(logging.DEBUG)
    client._session.post.side_effect = failure
    with pytest.raises(ModelGenerationError) as caught:
        client.complete(PRIVATE)
    assert PRIVATE not in str(caught.value)
    assert DETAIL not in str(caught.value)
    assert PRIVATE not in caplog.text
    assert DETAIL not in caplog.text
    client._session.post.assert_called_once()


def test_http_failure_is_not_parsed_as_a_completion(client):
    failed = text_response(PRIVATE)
    failed.raise_for_status.side_effect = requests.HTTPError(DETAIL)
    client._session.post.return_value = failed
    with pytest.raises(ModelGenerationError):
        client.complete(PRIVATE)
    failed.json.assert_not_called()


@pytest.mark.parametrize('payload', [
    {}, None, [], {'choices': []}, {'choices': 'invalid'}, {'choices': [None]},
    {'choices': [{'message': {}}]},
    {'choices': [{'message': {'content': None}}]},
    {'choices': [{'message': {'content': ''}}]},
    {'choices': [{'message': {'content': ' \n\t '}}]},
    {'choices': [{'message': {'content': 42}}]},
    {'choices': [{'message': {'content': ['unsupported content parts']}}]},
])
def test_missing_or_unusable_model_response_is_a_failure(client, payload):
    client._session.post.return_value = response(payload)
    with pytest.raises(ModelGenerationError):
        client.complete(PRIVATE)


def test_invalid_json_is_a_failure(client):
    malformed = response(None)
    malformed.json.side_effect = ValueError(DETAIL)
    client._session.post.return_value = malformed
    with pytest.raises(ModelGenerationError):
        client.complete(PRIVATE)


@pytest.mark.parametrize('choice', [
    {'message': {'content': '  Answer\n\nwith paragraphs.  '}},
    {'text': '  Answer\n\nwith paragraphs.  '},
])
def test_success_preserves_response_and_request_contract(client, choice):
    client._session.post.return_value = response({'choices': [choice]})
    assert client.complete('hello', system_prompt='system') == 'Answer\n\nwith paragraphs.'
    call = client._session.post.call_args
    assert call.args[0].endswith('/v1/chat/completions')
    assert call.kwargs['timeout'] == 3
    assert call.kwargs['json']['messages'] == [
        {'role': 'system', 'content': 'system'}, {'role': 'user', 'content': 'hello'},
    ]


@pytest.mark.parametrize('value', [None, '', ' \n ', 42, '<|im_end|>'])
def test_orchestrator_does_not_accept_an_empty_or_invalid_answer(value):
    with pytest.raises(ModelGenerationError):
        asyncio.run(ToolOrchestrator().orchestrate('hello', lambda context: value))


def test_orchestrator_propagates_generation_failure_without_retry(caplog):
    generate = Mock(side_effect=RuntimeError(DETAIL))
    with pytest.raises(ModelGenerationError):
        asyncio.run(ToolOrchestrator().orchestrate('hello', generate))
    generate.assert_called_once()
    assert DETAIL not in caplog.text


def prepare_pipeline(pipeline, client, control=True):
    pipeline.llm = client
    pipeline.ab_test.assign_group = lambda *a: 'control' if control else 'treatment'
    pipeline.ab_test.is_control_group = lambda *a: control
    pipeline.research_manager.requires_research = lambda text: False
    pipeline._persist_turn = Mock(wraps=pipeline._persist_turn)
    pipeline._record_ab_metrics = Mock()
    pipeline._tag_response_for_next_turn = Mock()
    pipeline.personality_post_processor.process_response = AsyncMock(
        return_value={'response': 'unexpected postprocessing', 'adjustments': []})


@pytest.mark.parametrize('control', [True, False])
@pytest.mark.parametrize('after_tool', [False, True])
def test_failed_generation_is_not_saved_or_counted_as_success(
        isolated_pipeline, client, control, after_tool):
    from src.core.pipeline import State
    pipeline, _ = isolated_pipeline
    prepare_pipeline(pipeline, client, control)
    calculate = Mock(return_value='CALCULATION RESULT: 4')
    pipeline.tool_orchestrator.register_tool('math.calc', calculate)
    results = [requests.ConnectionError(DETAIL)]
    if after_tool:
        results.insert(0, text_response(json.dumps({'tool': 'math.calc', 'args': {'expression': '2+2'}})))
    client._session.post.side_effect = results
    pipeline.state = State.THINKING
    with ThreadPoolExecutor(max_workers=1) as pool:
        assert pool.submit(pipeline.think, 'Please calculate 2 + 2').result(timeout=10) == MODEL_FAILURE_REPLY
    assert pipeline.state == State.SPEAKING
    assert client._session.post.call_count == (2 if after_tool else 1)
    assert calculate.call_count == int(after_tool)
    pipeline._persist_turn.assert_not_called()
    pipeline._record_ab_metrics.assert_not_called()
    pipeline._tag_response_for_next_turn.assert_not_called()
    pipeline.personality_post_processor.process_response.assert_not_awaited()
    assert pipeline.context_manager.get_stats()['window_size'] == 0
    assert pipeline.semantic_memory.get_stats()['total_conversations'] == 0


def test_a_later_successful_turn_recovers_and_is_saved_once(isolated_pipeline, client):
    from src.core.pipeline import State
    pipeline, _ = isolated_pipeline
    prepare_pipeline(pipeline, client)
    client._session.post.side_effect = [requests.Timeout(DETAIL), text_response('The answer is 42.')]
    pipeline.state = State.THINKING
    assert pipeline.think('Hello Penny') == MODEL_FAILURE_REPLY
    pipeline.state = State.THINKING
    assert '42' in pipeline.think('Hello again Penny')
    pipeline._persist_turn.assert_called_once()
    pipeline._record_ab_metrics.assert_called_once()
    pipeline._tag_response_for_next_turn.assert_called_once()
    assert pipeline.context_manager.get_stats()['window_size'] == 1
    assert pipeline.semantic_memory.get_stats()['total_conversations'] == 1


@pytest.mark.parametrize('failure', [ModelGenerationError(), RuntimeError(DETAIL)])
def test_base_voice_pipeline_does_not_echo_user_input_on_model_failure(failure):
    from src.core.pipeline import PipelineLoop, State
    pipeline = PipelineLoop.__new__(PipelineLoop)
    pipeline.cfg = {}
    pipeline.telemetry = Mock()
    pipeline.llm = SimpleNamespace(complete=Mock(side_effect=failure))
    pipeline.state = State.THINKING
    assert pipeline.think(PRIVATE) == MODEL_FAILURE_REPLY
    assert pipeline.state == State.SPEAKING
    events = [call.args[0] for call in pipeline.telemetry.log_event.call_args_list]
    assert 'llm_error' in events
    assert 'thinking_complete' not in events
    assert DETAIL not in str(pipeline.telemetry.log_event.call_args_list)


@pytest.mark.parametrize('stage', ['sanitize', 'personality'])
def test_empty_postprocessed_reply_is_not_saved(isolated_pipeline, client, monkeypatch, stage):
    import chat_entry
    from src.core.pipeline import State
    pipeline, _ = isolated_pipeline
    prepare_pipeline(pipeline, client, control=stage == 'sanitize')
    client._session.post.return_value = text_response('Normal model response.')
    if stage == 'sanitize':
        monkeypatch.setattr(chat_entry, 'sanitize_output', lambda text: '')
    else:
        pipeline.personality_post_processor.process_response.return_value = {'response': '', 'adjustments': []}
    pipeline.state = State.THINKING
    assert pipeline.think('Hello Penny') == MODEL_FAILURE_REPLY
    pipeline._persist_turn.assert_not_called()
    pipeline._record_ab_metrics.assert_not_called()
