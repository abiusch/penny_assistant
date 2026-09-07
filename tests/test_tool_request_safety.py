"""Real request-thread execution and enforceable tool limits, without services."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock

import pytest

from src.tools.tool_registry import ToolRegistry
from src.tools.tool_safety import (
    SafeToolWrapper, ToolTimeoutError, ToolValidationError, ToolRateLimitError,
    ToolSafetyError, RateLimiter, get_safe_tool_wrapper, with_timeout,
)
from tests.tool_worker_fixtures import wait_then_write, raise_error, noisy_result


@pytest.fixture(autouse=True)
def reset_global_limits():
    get_safe_tool_wrapper().reset_rate_limits()
    yield
    get_safe_tool_wrapper().reset_rate_limits()


def in_request_thread(func, *args):
    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(func, *args).result(timeout=10)


def test_registered_calculator_runs_in_request_thread():
    registry = ToolRegistry()
    result = in_request_thread(registry.get_tool('math.calc'), {'expression': '347 * 29'})
    assert '347 * 29 = 10063' in result


def test_validation_does_not_modify_process_alarm(monkeypatch):
    import signal
    change_signal = Mock(side_effect=AssertionError('must not change process signals'))
    calculate = SafeToolWrapper().wrap_tool('math.calc', noisy_result)
    with pytest.raises(ToolValidationError):
        with monkeypatch.context() as patch:
            patch.setattr(signal, 'signal', change_signal)
            calculate({'expression': 'import os'})
    change_signal.assert_not_called()


def test_sync_timeout_stops_and_reaps_worker(tmp_path, monkeypatch):
    import subprocess
    real_popen = subprocess.Popen
    children = []
    def record_child(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child
    monkeypatch.setattr(subprocess, 'Popen', record_child)
    started, finished = tmp_path / 'started', tmp_path / 'finished'
    with pytest.raises(ToolTimeoutError):
        in_request_thread(with_timeout(2)(wait_then_write),
                          {'started': str(started), 'finished': str(finished)})
    assert started.exists(), 'The tool must actually start before its deadline.'
    assert len(children) == 1
    assert children[0].returncode is not None, 'Worker must be reaped before returning.'
    assert children[0].returncode != 0
    assert not finished.exists()


@pytest.mark.parametrize('attribute_error', [False, True])
def test_sync_exception_returns_without_retry(tmp_path, attribute_error):
    attempts = tmp_path / 'attempts'
    error = AttributeError if attribute_error else ValueError
    with pytest.raises(error, match='synthetic'):
        in_request_thread(with_timeout(2)(raise_error),
                          {'attempts': str(attempts), 'attribute_error': attribute_error})
    assert attempts.read_text().splitlines() == ['attempt']


def test_worker_diagnostics_do_not_corrupt_result():
    assert in_request_thread(with_timeout(2)(noisy_result), {'value': 4}) == {'value': 4}


def test_async_timeout_still_cancels_tool():
    cancelled = []
    async def slow_tool(args):
        try:
            await asyncio.sleep(30)
        finally:
            cancelled.append(True)
    with pytest.raises(ToolTimeoutError):
        asyncio.run(with_timeout(0.01)(slow_tool)({}))
    assert cancelled == [True]


def test_disabled_code_never_starts_a_worker(monkeypatch):
    import subprocess
    start_worker = Mock(side_effect=AssertionError('disabled code must not execute'))
    monkeypatch.setattr(subprocess, 'Popen', start_worker)
    with pytest.raises(ToolValidationError, match='disabled'):
        in_request_thread(ToolRegistry().get_tool('code.execute'), {'code': 'print(4)'})
    start_worker.assert_not_called()


def test_rate_limit_is_shared_across_request_workers():
    wrapper = SafeToolWrapper(timeout_seconds=5, max_calls_per_minute=5)
    calculate = wrapper.wrap_tool('math.calc', ToolRegistry()._raw_tools['math.calc'])
    barrier = Barrier(12)
    def request():
        barrier.wait(timeout=5)
        try:
            assert '2 + 2 = 4' in calculate({'expression': '2 + 2'})
            return True
        except ToolRateLimitError:
            return False
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(lambda _: request(), range(12)))
    assert sum(results) == 5
    assert wrapper.rate_limiter.get_remaining_calls('math.calc') == 0


def test_rate_limit_recovers_after_window(monkeypatch):
    import src.tools.tool_safety as safety
    clock = Mock(return_value=100)
    monkeypatch.setattr(safety.time, 'monotonic', clock)
    limiter = RateLimiter(max_calls=1, window_seconds=60)
    assert limiter.check_rate_limit('math.calc')
    assert not limiter.check_rate_limit('math.calc')
    clock.return_value = 160
    assert limiter.get_remaining_calls('math.calc') == 1
    assert limiter.check_rate_limit('math.calc')


def test_worker_runs_from_web_directory(monkeypatch):
    from pathlib import Path
    monkeypatch.chdir(Path(__file__).resolve().parents[1] / 'web_interface')
    result = in_request_thread(ToolRegistry().get_tool('math.calc'), {'equation': '2 + 2'})
    assert '2 + 2 = 4' in result


def test_nonimportable_sync_tool_fails_without_unbounded_fallback():
    called = []
    def local_tool(args):
        called.append(True)
    with pytest.raises(ToolSafetyError, match='importable'):
        with_timeout(2)(local_tool)({})
    assert not called


@pytest.mark.parametrize(('expression', 'expected'), [
    ('347 * 29', '10063'),
    ('0.15 * 847293', '127093.95'),
    ('(7 + 5) / 4', '3.0'),
    ('17 // 5 + 17 % 5', '5'),
    ('abs(-4) + round(2.345, 2)', '6.35'),
    ('pow(2, 8)', '256'),
    ('pow(2, 8, 7)', '4'),
    ('sum((1, 2, 3), 4)', '10'),
    ('min((4, 1, 2)) + max(1, 2, 4)', '5'),
    ('2 ** -3', '0.125'),
])
def test_bounded_calculator_preserves_arithmetic(expression, expected):
    from src.tools.calculator import calculate
    assert calculate({'expression': expression}) == f'CALCULATION RESULT:\n{expression} = {expected}'


@pytest.mark.parametrize('expression', [
    '9 ** 999999999',
    'pow(2, pow(2, 100))',
    'round(1.5, 99999999)',
    '(1, 2) * 99999999',
    '1e309',
    '1 / 0',
    '(2).__class__',
    'sum(x for x in (1, 2))',
    "__import__('os')",
    '+'.join(['1'] * 70),
    '-' * 30 + '1',
    '1' * 201,
])
def test_expensive_or_non_arithmetic_expressions_are_rejected(expression):
    # Even raw arithmetic (without the registry's validator) must be bounded.
    # Exercise the real worker too: a broken bound cannot hang the test process.
    from src.tools.calculator import calculate
    result = in_request_thread(with_timeout(2)(calculate), {'expression': expression})
    assert result.startswith('ERROR: Calculation failed:')
