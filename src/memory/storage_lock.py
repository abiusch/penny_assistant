"""Shared reentrant locks for cooperating storage users (thread and process)."""

from contextlib import contextmanager
from pathlib import Path
import os
import threading

_locks = {}
_locks_guard = threading.Lock()


class _StoreLock:
    """Reentrant thread lock plus an OS-released advisory process lock."""
    def __init__(self):
        self.thread = threading.RLock()
        self.depth = threading.local()

    @contextmanager
    def hold(self, path):
        with self.thread:
            depth = getattr(self.depth, 'value', 0)
            if depth:
                self.depth.value = depth + 1
                try:
                    yield
                finally:
                    self.depth.value = depth
                return
            # A stable sidecar is necessary: locking the data inode would stop
            # protecting it when an atomic update replaces the file.
            with open(path.with_name('.' + path.name + '.lock'), 'a+b') as lock_file:
                if os.name == 'nt':
                    import msvcrt
                    lock_file.seek(0, os.SEEK_END)
                    if lock_file.tell() == 0:
                        lock_file.write(b'0')
                        lock_file.flush()
                    lock_file.seek(0)
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock_file, fcntl.LOCK_EX)
                self.depth.value = 1
                try:
                    yield
                finally:
                    self.depth.value = 0
                    if os.name == 'nt':
                        lock_file.seek(0)
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    else:
                        fcntl.flock(lock_file, fcntl.LOCK_UN)

def get_store_lock(path):
    """Use the resolved file identity so relative/absolute aliases share a lock."""
    identity = str(Path(path).resolve())
    with _locks_guard:
        return _locks.setdefault(identity, _StoreLock())
