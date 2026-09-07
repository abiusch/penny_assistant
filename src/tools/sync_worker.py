"""Run one importable synchronous tool in an expendable Python process.

Invoked by tool_safety with a trusted function reference and JSON arguments.
This is a timeout boundary, not a sandbox for untrusted Python functions.
"""

import contextlib
import importlib
import json
from pathlib import Path
import sys


def main():
    # Launch by absolute file path so web-directory launches use the same code.
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    try:
        args, kwargs = json.load(sys.stdin)
        with contextlib.redirect_stdout(sys.stderr):
            target = importlib.import_module(sys.argv[1])
            for part in sys.argv[2].split('.'):
                target = getattr(target, part)
            # A directly decorated module-level function resolves to its wrapper.
            target = getattr(target, '_penny_timeout_target', target)
            result = target(*args, **kwargs)
        response = {'ok': True, 'result': result}
        encoded = json.dumps(response, allow_nan=False)
    except Exception as error:
        encoded = json.dumps({'ok': False, 'error': type(error).__name__,
                              'message': str(error)})
    sys.stdout.write(encoded)


if __name__ == '__main__':
    main()
