from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def load_module_from_path(module_name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_statement_module(scripts_dir: Path) -> ModuleType:
    return load_module_from_path("fnb_statement_to_sqlite_mod", scripts_dir / "fnb_statement_to_sqlite.py")


def get_chat_module(scripts_dir: Path) -> ModuleType:
    return load_module_from_path("fnb_chat_assistant_v2_mod", scripts_dir / "fnb_chat_assistant-v2.py")


def get_account_module(scripts_dir: Path) -> ModuleType:
    return load_module_from_path("account_analyzer_mod", scripts_dir / "account_analyzer.py")
