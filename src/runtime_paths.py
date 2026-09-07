"""Stable paths for the source-checkout runtime; never change the process cwd."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def project_path(value):
    """Resolve relative paths against the project, including explicit overrides."""
    path = Path(value).expanduser()
    return (path if path.is_absolute() else PROJECT_ROOT / path).resolve()


def config_path(explicit=None):
    """Explicit path > PENNY_CONFIG > root config > legacy config/ fallback.

    An invalid override must fail when read, rather than select a different file.
    """
    selected = explicit if explicit is not None else os.environ.get('PENNY_CONFIG')
    if selected is not None:
        return project_path(selected)
    primary = PROJECT_ROOT / 'penny_config.json'
    if primary.exists():
        return primary
    return PROJECT_ROOT / 'config' / 'penny_config.json'


def load_runtime_config(explicit=None):
    with config_path(explicit).open(encoding='utf-8') as source:
        config = json.load(source)
    if not isinstance(config, dict):
        raise ValueError('Penny configuration must be a JSON object')
    return config


def data_path(explicit=None):
    """Explicit directory > PENNY_DATA_DIR > project data; no migration."""
    selected = explicit if explicit is not None else os.environ.get('PENNY_DATA_DIR')
    root = project_path(selected if selected is not None else 'data')
    # Older web launches could create a second store. Refuse to silently choose
    # one when both exist; an explicit selection is required. Symlinks are fine.
    legacy = PROJECT_ROOT / 'web_interface' / 'data'
    if selected is None and legacy.is_dir() and legacy.resolve() != root:
        if any(legacy.iterdir()):
            raise ValueError('Separate web data found. Set PENNY_DATA_DIR to the store '
                             'you intend to use; existing data has not been moved.')
    return root


@dataclass(frozen=True)
class RuntimePaths:
    config: Path
    data: Path
    personality_db: Path

    @classmethod
    def resolve(cls, *, config=None, data_dir=None, db_path=None):
        data = data_path(data_dir)
        db = project_path(db_path) if db_path is not None else data / 'personality_tracking.db'
        return cls(config_path(config), data, db)
