from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    """Load config"""
    with open(path) as f:
        return yaml.safe_load(f)
