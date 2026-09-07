"""Importable, deterministic synchronous tools for process timeout tests."""

from pathlib import Path
import time


def wait_then_write(args):
    Path(args['started']).write_text('started')
    time.sleep(30)
    Path(args['finished']).write_text('finished')
    return 'finished'


def raise_error(args):
    if 'attempts' in args:
        with Path(args['attempts']).open('a') as record:
            record.write('attempt\n')
    if args.get('attribute_error'):
        raise AttributeError('synthetic attribute failure')
    raise ValueError('synthetic tool failure')


def noisy_result(args):
    print('tool diagnostic output')
    return {'value': args['value']}
