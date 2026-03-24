#!/usr/bin/env python3
"""
Provider 端到端测试脚本。

自动扫描 configs/ 下的配置文件（config_{provider}.json），
匹配已注册的 Provider，对每个端点执行真实推理请求，
验证 Provider 的 build_request_params() 和 extract_response() 是否正确工作。

用法:
  # 测试所有已注册的 provider（自动匹配 configs/config_{name}.json）
  python -m distill_pipeline.providers.test_providers

  # 只测试指定 provider
  python -m distill_pipeline.providers.test_providers --provider kimi minimax

  # 指定配置文件目录
  python -m distill_pipeline.providers.test_providers --config-dir /path/to/configs

  # 指定单个配置文件测试某个 provider
  python -m distill_pipeline.providers.test_providers --provider kimi --config /path/to/config.json

  # 详细输出（显示完整 response）
  python -m distill_pipeline.providers.test_providers --verbose

  # 自定义 prompt
  python -m distill_pipeline.providers.test_providers --prompt "Write a hello world in Python"
"""

import argparse
import asyncio
import json
import sys
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from openai import AsyncOpenAI

# 确保能找到 distill_pipeline 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from distill_pipeline.providers.registry import ProviderRegistry, get_provider
from distill_pipeline.config import load_config


# ============================================================
# 颜色输出
# ============================================================

class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def ok(msg: str) -> str:
    return f"{Colors.GREEN}PASS{Colors.RESET} {msg}"


def fail(msg: str) -> str:
    return f"{Colors.RED}FAIL{Colors.RESET} {msg}"


def warn(msg: str) -> str:
    return f"{Colors.YELLOW}WARN{Colors.RESET} {msg}"


def info(msg: str) -> str:
    return f"{Colors.CYAN}INFO{Colors.RESET} {msg}"


def bold(msg: str) -> str:
    return f"{Colors.BOLD}{msg}{Colors.RESET}"


def dim(msg: str) -> str:
    return f"{Colors.DIM}{msg}{Colors.RESET}"


# ============================================================
# 核心测试逻辑
# ============================================================

async def test_single_endpoint(
    provider_name: str,
    provider,
    api_config: Dict[str, Any],
    prompt: str = "你好，请用一句话介绍你自己。",
    timeout: int = 60,
    verbose: bool = False,
) -> Dict[str, Any]:
    """测试单个端点的 Provider 配置。

    Returns:
        包含测试结果的字典：
        {
            "provider": str,
            "base_url": str,
            "model": str,
            "success": bool,
            "content": str | None,
            "thinking": str | None,
            "error": str | None,
            "latency_ms": float,
        }
    """
    base_url = api_config.get("base_url", "")
    api_key = api_config.get("api_key", "sk-123")
    model = api_config.get("model", "default")

    result = {
        "provider": provider_name,
        "base_url": base_url,
        "model": model,
        "success": False,
        "content": None,
        "thinking": None,
        "error": None,
        "latency_ms": 0,
    }

    try:
        client = AsyncOpenAI(base_url=base_url, api_key=api_key)

        # Step 1: 用 Provider 构建请求参数
        messages = [{"role": "user", "content": prompt}]
        params = provider.build_request_params(
            messages=messages,
            model=model,
            temperature=0.7,
            top_p=0.95,
            timeout=timeout,
        )

        if verbose:
            # 打印请求参数（隐藏敏感信息）
            safe_params = dict(params)
            safe_params["messages"] = [{"role": "user", "content": prompt[:50] + "..."}]
            print(f"    {dim('Request params:')} {json.dumps(safe_params, ensure_ascii=False, default=str)}")

        # Step 2: 发送请求
        start_time = time.time()
        response = await client.chat.completions.create(**params)
        latency_ms = (time.time() - start_time) * 1000
        result["latency_ms"] = round(latency_ms, 1)

        # Step 3: 用 Provider 解析响应
        content, thinking = provider.extract_response(response)
        result["content"] = content
        result["thinking"] = thinking
        result["success"] = bool(content)

        await client.close()

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"

    return result


async def test_provider(
    provider_name: str,
    config_path: str,
    prompt: str = "你好，请用一句话介绍你自己。",
    timeout: int = 60,
    verbose: bool = False,
    max_endpoints: int = 0,
) -> List[Dict[str, Any]]:
    """测试一个 Provider 的所有端点。

    Args:
        provider_name: Provider 名称。
        config_path: 配置文件路径。
        prompt: 测试用的 prompt。
        timeout: 超时秒数。
        verbose: 是否详细输出。
        max_endpoints: 最多测试几个端点（0 = 不限）。

    Returns:
        每个端点的测试结果列表。
    """
    # 加载 Provider
    try:
        provider = get_provider(provider_name)
    except ValueError as e:
        print(f"  {fail(str(e))}")
        return []

    # 加载配置
    try:
        api_configs, api_concurrencies = load_config(config_path)
    except Exception as e:
        print(f"  {fail(f'Config load error: {e}')}")
        return []

    # 去重端点（按 base_url）
    seen_urls = set()
    unique_configs = []
    for cfg in api_configs:
        url = cfg.get("base_url", "")
        if url not in seen_urls:
            seen_urls.add(url)
            unique_configs.append(cfg)

    if max_endpoints > 0:
        unique_configs = unique_configs[:max_endpoints]

    print(f"  Config:    {config_path}")
    print(f"  Endpoints: {len(unique_configs)} unique (of {len(api_configs)} total)")
    print(f"  Extra body: {provider.build_extra_body()}")
    print()

    results = []
    for i, api_config in enumerate(unique_configs):
        base_url = api_config.get("base_url", "")
        model = api_config.get("model", "?")
        concurrency = api_config.get("concurrency", 1)

        print(f"  [{i+1}/{len(unique_configs)}] {base_url}")
        print(f"           model={model}, concurrency={concurrency}")

        r = await test_single_endpoint(
            provider_name=provider_name,
            provider=provider,
            api_config=api_config,
            prompt=prompt,
            timeout=timeout,
            verbose=verbose,
        )
        results.append(r)

        if r["success"]:
            content_preview = (r["content"] or "")[:80].replace("\n", "\\n")
            thinking_preview = ""
            if r["thinking"]:
                thinking_preview = f", thinking={len(r['thinking'])} chars"
            print(f"           {ok(f'content=\"{content_preview}...\"{thinking_preview}')}")
            print(f"           {dim(f'latency: {r['latency_ms']}ms')}")
        else:
            error_msg = r["error"] or "Empty response"
            print(f"           {fail(error_msg)}")

        print()

    return results


def discover_config_for_provider(provider_name: str, config_dir: str) -> Optional[str]:
    """根据 provider 名称在配置目录中查找对应的 config 文件。

    匹配规则（按优先级）：
    1. config_{provider_name}.json
    2. config_{provider_name}.active.json
    """
    config_dir = Path(config_dir)

    # 尝试匹配
    candidates = [
        config_dir / f"config_{provider_name}.json",
        config_dir / f"config_{provider_name}.active.json",
    ]

    for path in candidates:
        if path.exists():
            return str(path)

    return None


# ============================================================
# 主函数
# ============================================================

async def main_async(args):
    config_dir = args.config_dir
    all_providers = ProviderRegistry.list_providers()

    # 确定要测试的 provider 列表
    if args.provider:
        target_providers = args.provider
    else:
        target_providers = all_providers

    print()
    print(bold("=" * 70))
    print(bold("  Provider End-to-End Test"))
    print(bold("=" * 70))
    print()
    print(f"  Registered providers: {', '.join(all_providers)}")
    print(f"  Testing:              {', '.join(target_providers)}")
    print(f"  Config directory:     {config_dir}")
    print(f"  Prompt:               \"{args.prompt[:60]}{'...' if len(args.prompt) > 60 else ''}\"")
    print(f"  Timeout:              {args.timeout}s")
    print()

    all_results = {}
    tested = 0
    passed = 0
    failed = 0
    skipped = 0

    for provider_name in target_providers:
        print(bold(f"{'─' * 70}"))
        print(bold(f"  Provider: {provider_name}"))
        print(bold(f"{'─' * 70}"))
        print()

        # 检查 provider 是否已注册
        if provider_name not in all_providers:
            print(f"  {fail(f'Provider \"{provider_name}\" is not registered')}")
            print(f"  {info(f'Available: {', '.join(all_providers)}')}")
            print()
            failed += 1
            continue

        # 查找配置文件
        if args.config:
            config_path = args.config
        else:
            config_path = discover_config_for_provider(provider_name, config_dir)

        if not config_path:
            print(f"  {warn(f'No config found: configs/config_{provider_name}.json')}")
            print(f"  {dim('Skipping (use --config to specify manually)')}")
            print()
            skipped += 1
            continue

        # 运行测试
        results = await test_provider(
            provider_name=provider_name,
            config_path=config_path,
            prompt=args.prompt,
            timeout=args.timeout,
            verbose=args.verbose,
            max_endpoints=args.max_endpoints,
        )

        all_results[provider_name] = results
        for r in results:
            tested += 1
            if r["success"]:
                passed += 1
            else:
                failed += 1

    # ============================================================
    # 汇总报告
    # ============================================================

    print(bold("=" * 70))
    print(bold("  Summary"))
    print(bold("=" * 70))
    print()

    for provider_name, results in all_results.items():
        ep_pass = sum(1 for r in results if r["success"])
        ep_fail = sum(1 for r in results if not r["success"])
        avg_latency = 0
        if ep_pass > 0:
            avg_latency = sum(r["latency_ms"] for r in results if r["success"]) / ep_pass

        status = ok(f"{ep_pass}/{len(results)} endpoints") if ep_fail == 0 else fail(f"{ep_pass}/{len(results)} endpoints")
        latency_str = f"avg {avg_latency:.0f}ms" if avg_latency > 0 else ""
        print(f"  {provider_name:12s} {status}  {dim(latency_str)}")

        # 显示失败详情
        for r in results:
            if not r["success"]:
                print(f"  {'':12s}   {fail(r['base_url'])}")
                print(f"  {'':12s}   {dim(r.get('error', 'Unknown error'))}")

    if skipped > 0:
        print(f"\n  {warn(f'{skipped} provider(s) skipped (no config file found)')}")

    print()
    print(bold(f"  Total: {tested} endpoints tested, {passed} passed, {failed} failed, {skipped} skipped"))
    print(bold("=" * 70))
    print()

    return failed == 0


def main():
    parser = argparse.ArgumentParser(
        description="测试已注册 Provider 的端到端配置是否正确",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 测试所有 provider
  python -m distill_pipeline.providers.test_providers

  # 只测试 kimi 和 minimax
  python -m distill_pipeline.providers.test_providers --provider kimi minimax

  # 指定配置文件
  python -m distill_pipeline.providers.test_providers --provider kimi --config /path/to/config.json

  # 详细输出
  python -m distill_pipeline.providers.test_providers --verbose

  # 每个 provider 只测试第一个端点
  python -m distill_pipeline.providers.test_providers --max-endpoints 1
        """,
    )
    parser.add_argument(
        "--provider", "-p",
        nargs="+",
        default=None,
        help="要测试的 provider 名称（默认：测试所有已注册的 provider）",
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="指定配置文件路径（覆盖自动发现）",
    )
    parser.add_argument(
        "--config-dir",
        default=str(Path(__file__).resolve().parent.parent.parent / "configs"),
        help="配置文件目录（默认：项目根目录下的 configs/）",
    )
    parser.add_argument(
        "--prompt",
        default="你好，请用一句话介绍你自己。",
        help="测试用的 prompt（默认：你好，请用一句话介绍你自己。）",
    )
    parser.add_argument(
        "--timeout", "-t",
        type=int,
        default=60,
        help="单次请求超时秒数（默认：60）",
    )
    parser.add_argument(
        "--max-endpoints",
        type=int,
        default=0,
        help="每个 provider 最多测试几个端点（默认：0 = 不限）",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细的请求参数和完整响应",
    )

    args = parser.parse_args()
    success = asyncio.run(main_async(args))
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
