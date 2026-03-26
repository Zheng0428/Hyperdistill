import importlib
import pkgutil
from pathlib import Path

from .registry import TaskRegistry, get_task

# Auto-import all task modules in this directory to trigger @TaskRegistry.register decorators.
# Adding a new task only requires creating a new task_*.py (or any *.py) file here.
_skip = {"__init__", "base", "registry"}
for _mod in pkgutil.iter_modules([str(Path(__file__).parent)]):
    if _mod.name not in _skip:
        importlib.import_module(f".{_mod.name}", package=__name__)

__all__ = ["TaskRegistry", "get_task"]
