"""
Async OpenAI client pool with concurrency expansion, random selection,
retry with client rotation, and optional hot-reload of config.
"""

import random
import time
import threading
import asyncio
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI

from .config import load_config
from .utils import log


class ClientPool:
    """Manages a pool of AsyncOpenAI clients.

    Features:
    - Expands clients based on per-API concurrency settings.
    - Random shuffle for load balancing.
    - Random client selection for each request.
    - Optional hot-reload from config file.
    """

    def __init__(
        self,
        api_configs: List[Dict[str, Any]],
        api_concurrencies: Optional[List[int]] = None,
        config_path: Optional[str] = None,
        reload_interval: int = 1800,  # 30 minutes
    ):
        """Initialize the client pool.

        Args:
            api_configs: List of API config dicts with 'api_key', 'base_url', 'model'.
            api_concurrencies: Concurrency count per API (expands client instances).
            config_path: If set, enables hot-reload from this config file.
            reload_interval: Seconds between config reload checks.
        """
        self.config_path = config_path
        self.reload_interval = reload_interval
        self._last_reload = time.time()
        self._reload_lock = threading.Lock()

        self._build_pool(api_configs, api_concurrencies)

    @staticmethod
    def _create_client(config: Dict[str, Any]) -> AsyncOpenAI:
        """Create an AsyncOpenAI client with proper auth for the endpoint.

        For standard OpenAI-compatible APIs (api_key starts with 'sk-'),
        uses the default Bearer token auth.

        For other platforms (e.g., PAI-EAS with base64 tokens), overrides
        the Authorization header to send the token directly without 'Bearer'.
        """
        api_key = config["api_key"]
        base_url = config["base_url"]

        if api_key.startswith("sk-"):
            # Standard Bearer auth
            return AsyncOpenAI(base_url=base_url, api_key=api_key)
        else:
            # Custom auth: send token directly without Bearer prefix
            # Use a dummy api_key to satisfy SDK validation,
            # then override the header
            return AsyncOpenAI(
                base_url=base_url,
                api_key="dummy",
                default_headers={"Authorization": api_key},
            )

    def _build_pool(
        self,
        api_configs: List[Dict[str, Any]],
        api_concurrencies: Optional[List[int]] = None,
    ) -> None:
        """Build the client pool from configs."""
        self.client_configs: List[Dict[str, Any]] = []

        if api_concurrencies:
            for config, count in zip(api_configs, api_concurrencies):
                for _ in range(count):
                    self.client_configs.append(dict(config))
        else:
            self.client_configs = [dict(c) for c in api_configs]

        random.shuffle(self.client_configs)

        self.clients: List[AsyncOpenAI] = [
            self._create_client(config)
            for config in self.client_configs
        ]

        log(f"Client pool initialized with {len(self.clients)} clients")

    def get_random(self) -> Tuple[AsyncOpenAI, Dict[str, Any]]:
        """Return a random (client, config) pair.

        Returns:
            A tuple of (AsyncOpenAI_client, config_dict).
        """
        idx = random.randint(0, len(self.clients) - 1)
        return self.clients[idx], self.client_configs[idx]

    @property
    def size(self) -> int:
        """Return the total number of client instances in the pool."""
        return len(self.clients)

    def reload_if_needed(self) -> None:
        """Check if config should be reloaded and do so if needed.

        This is safe to call frequently; it only reloads when
        `reload_interval` seconds have passed since the last reload.
        Requires `config_path` to be set at init time.
        """
        if not self.config_path:
            return

        current_time = time.time()
        if current_time - self._last_reload < self.reload_interval:
            return

        with self._reload_lock:
            # Double-check after acquiring lock
            if current_time - self._last_reload < self.reload_interval:
                return

            log("=" * 60)
            log("Reloading server configuration...")

            try:
                api_configs, api_concurrencies = load_config(self.config_path)

                if not api_configs:
                    log("No APIs found in config, keeping current pool")
                    return

                # Close old clients
                old_clients = self.clients
                for client in old_clients:
                    try:
                        if hasattr(client, "close"):
                            asyncio.create_task(client.close())
                    except Exception:
                        pass

                # Build new pool
                self._build_pool(api_configs, api_concurrencies)
                self._last_reload = current_time

                log(f"Configuration reloaded! Active clients: {len(self.clients)}")
                log("=" * 60)

            except Exception as e:
                log(f"Failed to reload configuration: {e}")
                log("Keeping current pool")
