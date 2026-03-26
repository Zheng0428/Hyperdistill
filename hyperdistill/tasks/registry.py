"""
Task registry: look up tasks by name.

Tasks self-register via @TaskRegistry.register decorator.
All task modules are imported in __init__.py to trigger registration.
"""

from typing import Dict, List, Type

from .base import BaseTask


class TaskRegistry:
    """Registry mapping task names to task classes."""

    _tasks: Dict[str, Type[BaseTask]] = {}

    @classmethod
    def register(cls, task_class: Type[BaseTask]) -> Type[BaseTask]:
        """Register a task class. Use as a decorator on the class definition:

            @TaskRegistry.register
            class MyTask(BaseTask):
                name = "my_task"
                ...
        """
        cls._tasks[task_class.name] = task_class
        return task_class

    @classmethod
    def get(cls, name: str) -> BaseTask:
        """Return a task instance by name."""
        if name not in cls._tasks:
            available = ", ".join(sorted(cls._tasks.keys()))
            raise ValueError(
                f"Unknown task '{name}'. Available: {available}"
            )
        return cls._tasks[name]()

    @classmethod
    def list_tasks(cls) -> List[str]:
        """Return all registered task names."""
        return sorted(cls._tasks.keys())


def get_task(name: str) -> BaseTask:
    """Convenience function: get a task instance by name."""
    return TaskRegistry.get(name)
