"""
Provider registry: look up providers by name.
"""

from typing import Dict, List, Type

from .base import BaseProvider
from .kimi import KimiProvider
from .deepseek import DeepSeekProvider
from .glm import GLMProvider
from .minimax import MiniMaxProvider
from .default import DefaultProvider


class ProviderRegistry:
    """Registry mapping provider names to provider classes."""

    _providers: Dict[str, Type[BaseProvider]] = {}

    @classmethod
    def register(cls, provider_class: Type[BaseProvider]) -> Type[BaseProvider]:
        """Register a provider class.

        Can be used as a decorator:
            @ProviderRegistry.register
            class MyProvider(BaseProvider):
                name = "my_provider"
                ...
        """
        cls._providers[provider_class.name] = provider_class
        return provider_class

    @classmethod
    def get(cls, name: str) -> BaseProvider:
        """Return a provider instance by name.

        Args:
            name: Provider name (e.g., 'kimi', 'dpsk', 'glm', 'default').

        Returns:
            A provider instance.

        Raises:
            ValueError: If the provider name is not registered.
        """
        if name not in cls._providers:
            available = ", ".join(sorted(cls._providers.keys()))
            raise ValueError(
                f"Unknown provider '{name}'. Available: {available}"
            )
        return cls._providers[name]()

    @classmethod
    def list_providers(cls) -> List[str]:
        """Return all registered provider names."""
        return sorted(cls._providers.keys())


# Register built-in providers
ProviderRegistry.register(KimiProvider)
ProviderRegistry.register(DeepSeekProvider)
ProviderRegistry.register(GLMProvider)
ProviderRegistry.register(MiniMaxProvider)
ProviderRegistry.register(DefaultProvider)


def get_provider(name: str) -> BaseProvider:
    """Convenience function: get a provider instance by name."""
    return ProviderRegistry.get(name)
