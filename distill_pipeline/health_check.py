"""
API health check module.

Tests each API endpoint with an actual inference request and generates
an 'active' config file containing only healthy endpoints.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional


def check_endpoint_health(
    base_url: str,
    api_key: str = "sk-123",
    model: Optional[str] = None,
    timeout: int = 30,
    verbose: bool = False,
) -> bool:
    """Check if a single API endpoint is healthy via actual inference.

    Args:
        base_url: API base URL.
        api_key: API key.
        model: Model name.
        timeout: Request timeout in seconds.
        verbose: Print debug info.

    Returns:
        True if the endpoint returns a valid chat completion response.
    """
    chat_url = base_url + "/chat/completions"
    request_data = {
        "model": model or "default",
        "messages": [{"role": "user", "content": "你好"}],
        "max_tokens": 10,
        "temperature": 0.7,
    }

    try:
        curl_cmd = [
            "curl", "-s",
            "--connect-timeout", "5",
            "--max-time", str(timeout),
            "-H", "Content-Type: application/json",
            "-H", f"Authorization: Bearer {api_key}",
            "-d", json.dumps(request_data),
            chat_url,
        ]

        result = subprocess.run(
            curl_cmd,
            capture_output=True,
            timeout=timeout + 5,
            text=True,
        )

        if result.returncode != 0:
            if verbose:
                print(f"  [DEBUG] curl failed: rc={result.returncode}")
                if result.stderr:
                    print(f"  [DEBUG] stderr: {result.stderr}")
            return False

        if verbose:
            print(f"  [DEBUG] Response: {result.stdout[:500]}")

        try:
            response = json.loads(result.stdout)
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    if verbose:
                        print(f"  [DEBUG] Content: {choice['message']['content']}")
                    return True

            if "error" in response:
                if verbose:
                    print(f"  [DEBUG] Error: {response['error']}")
                return False

        except json.JSONDecodeError as e:
            if verbose:
                print(f"  [DEBUG] JSON decode failed: {e}")
            return False

        return False

    except Exception as e:
        if verbose:
            print(f"  [DEBUG] Exception: {e}")
        return False


def run_health_check(
    config_path: str,
    output_path: Optional[str] = None,
    verbose: bool = False,
) -> str:
    """Run health check on all API endpoints in a config file.

    Tests each endpoint and generates an 'active' config containing only
    healthy endpoints.

    Args:
        config_path: Path to the API config file.
        output_path: Output path for active config. If None, auto-generated.
        verbose: Print debug info.

    Returns:
        Path to the generated active config file.

    Raises:
        SystemExit: If no endpoints are available.
    """
    config_file = Path(config_path)

    # Auto-generate output path
    if output_path is None:
        stem = config_file.stem
        suffix = config_file.suffix
        active_config_file = config_file.parent / f"{stem}.active{suffix}"
    else:
        active_config_file = Path(output_path)

    print("=" * 60)
    print("API Health Check")
    print("=" * 60)
    print(f"Config: {config_file}")
    print(f"Output: {active_config_file}")
    print()

    # Load config
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)

    apis = config.get("apis", [])

    # Support both formats
    concurrencies = config.get("api_concurrencies", None)
    if concurrencies is None:
        concurrencies = [api.get("concurrency", 1) for api in apis]

    if not apis:
        print("Error: No APIs found in config")
        sys.exit(1)

    print(f"Found {len(apis)} endpoints")
    print()

    # Test each endpoint
    active_apis = []
    active_concurrencies = []

    for i, api in enumerate(apis):
        base_url = api.get("base_url", "")
        api_key = api.get("api_key", "sk-123")
        model = api.get("model")
        print(f"[{i+1}/{len(apis)}] Testing {base_url} ... ", end="", flush=True)

        if check_endpoint_health(base_url, api_key, model, verbose=verbose):
            print("OK")
            active_apis.append(api)
            active_concurrencies.append(
                concurrencies[i] if i < len(concurrencies) else 1
            )
        else:
            print("FAILED")

    print()
    print("=" * 60)
    print(f"Active: {len(active_apis)} / {len(apis)}")
    print("=" * 60)
    print()

    if not active_apis:
        print("Error: No active API endpoints!")
        sys.exit(1)

    # Build active config (new format)
    for i, api in enumerate(active_apis):
        api["concurrency"] = active_concurrencies[i]

    active_config = {"apis": active_apis}

    # Write active config
    with open(active_config_file, "w", encoding="utf-8") as f:
        json.dump(active_config, f, indent=2, ensure_ascii=False)

    print(f"Active config saved to: {active_config_file}")
    print()

    for i, api in enumerate(active_apis):
        c = api.get("concurrency", 1)
        print(f"  [{i+1}] {api['base_url']} (concurrency: {c})")
    print()
    print("Health check completed")

    return str(active_config_file)
