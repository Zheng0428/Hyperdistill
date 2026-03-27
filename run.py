#!/usr/bin/env python3
"""
HyperDistill - Unified CLI Entry Point

Usage:
  # API backend (default)
  python run.py --task query_response --provider minimax --config config.json -i input.jsonl -o output.jsonl

  # CLI agent backend
  python run.py --task stackoverflow --backend cli --cli-model sonnet --agent-instructions agent.md -i input.jsonl -o out.jsonl

  # Health check / filter / list
  python run.py --health-check --config config.json
  python run.py --filter keyword -i output.jsonl
  python run.py --list
"""

import argparse
import asyncio
import sys
import os

# Add project root to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="HyperDistill - LLM Data Distillation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # API backend (default)
  python run.py --task query_response --provider minimax \\
    --config configs/config.json -i input.jsonl -o output.jsonl

  # CLI agent backend
  python run.py --task stackoverflow --backend cli --cli-model sonnet \\
    --agent-name stackoverflow-enhancer \\
    --skills code-analyzer,data-validator \\
    -i input.jsonl -o output.jsonl -w 4

  # CLI agent with custom API endpoint
  ANTHROPIC_BASE_URL=https://... ANTHROPIC_API_KEY=sk-xxx \\
  python run.py --task stackoverflow --backend cli \\
    --agent-name stackoverflow-enhancer \\
    --cli-model MiniMax-M2.5 -i input.jsonl -o output.jsonl

  # Health check
  python run.py --health-check --config configs/config.json

  # Filter output
  python run.py --filter keyword -i output.jsonl
        """,
    )

    # Mode selection
    mode_group = parser.add_argument_group("Mode")
    mode_group.add_argument(
        "--health-check", action="store_true",
        help="Run API health check only",
    )
    mode_group.add_argument(
        "--filter", type=str, default=None, metavar="NAME",
        help="Run post-processing filter (keyword, empty_response)",
    )
    mode_group.add_argument(
        "--list", action="store_true",
        help="List available tasks, providers, and filters",
    )

    # Task configuration
    task_group = parser.add_argument_group("Task")
    task_group.add_argument(
        "--task", type=str, default=None,
        help="Task name (query_response, code_to_question, text_to_response, stackoverflow)",
    )

    # Backend selection
    backend_group = parser.add_argument_group("Backend")
    backend_group.add_argument(
        "--backend", type=str, default="api", choices=["api", "cli"],
        help="Execution backend: 'api' (OpenAI-compatible API) or 'cli' (subprocess agent). Default: api",
    )

    # API backend options
    api_group = parser.add_argument_group("API Backend Options (--backend api)")
    api_group.add_argument(
        "--provider", type=str, default="default",
        help="API provider (kimi, dpsk, glm, minimax, default). Default: default",
    )
    api_group.add_argument("--config", help="API config file path (JSON)")
    api_group.add_argument("--api-key", help="API key (single or comma-separated)")
    api_group.add_argument("--api-keys", help="Multiple API keys (comma-separated)")
    api_group.add_argument("--base-url", help="API base URL")
    api_group.add_argument("--base-urls", help="Multiple base URLs (comma-separated)")
    api_group.add_argument("--model", help="Model name")
    api_group.add_argument("--models", help="Multiple model names (comma-separated)")
    api_group.add_argument("--api-concurrencies", help="Per-API concurrency limits (comma-separated)")

    # CLI backend options
    cli_group = parser.add_argument_group("CLI Backend Options (--backend cli)")
    cli_group.add_argument(
        "--cli-cmd", type=str, default="claude",
        help="CLI executable name or path (default: claude)",
    )
    cli_group.add_argument(
        "--cli-model", type=str, default="sonnet",
        help="Model name for CLI --model flag (default: sonnet)",
    )
    cli_group.add_argument(
        "--agent-instructions", type=str, default=None,
        help="Path to agent instructions .md file (content prepended to every prompt)",
    )
    cli_group.add_argument(
        "--agent-name", type=str, default=None,
        help="Name of agent to load from .claude/agents (falls back to ./agents, overrides --agent-instructions)",
    )
    cli_group.add_argument(
        "--agents-dir", type=str, default=None,
        help="Directory containing agent .md files (default: ./.claude/agents when --agent-name is used)",
    )
    cli_group.add_argument(
        "--skills", type=str, default=None,
        help="Comma-separated skill names to load from .claude/skills (falls back to ./skills)",
    )
    cli_group.add_argument(
        "--skills-dir", type=str, default=None,
        help="Directory containing Claude-style skills directories (default: ./.claude/skills when --skills is used)",
    )
    cli_group.add_argument(
        "--cli-timeout", type=int, default=600,
        help="CLI subprocess timeout in seconds (default: 600)",
    )
    cli_group.add_argument(
        "--cli-extra-args", type=str, default=None,
        help="Extra CLI arguments (comma-separated, e.g., '--verbose,--no-cache')",
    )

    # IO
    io_group = parser.add_argument_group("Input/Output")
    io_group.add_argument("-i", "--input", help="Input file path")
    io_group.add_argument("-o", "--output", help="Output file path")

    # Generation parameters (API backend)
    gen_group = parser.add_argument_group("Generation Parameters (API backend)")
    gen_group.add_argument(
        "-w", "--workers", type=int, default=None,
        help="Concurrent worker count (default: auto from concurrencies or 4 for CLI)",
    )
    gen_group.add_argument(
        "--temperature", type=float, default=0.7,
        help="Sampling temperature (default: 0.7, API backend only)",
    )
    gen_group.add_argument(
        "--top_p", type=float, default=None,
        help="Top-p nucleus sampling (API backend only)",
    )
    gen_group.add_argument(
        "--timeout", type=int, default=72000,
        help="API request timeout in seconds (default: 72000, API backend only)",
    )
    gen_group.add_argument(
        "--max-retries", type=int, default=3,
        help="Max retries per item (default: 3)",
    )

    # Output control
    out_group = parser.add_argument_group("Output Control")
    out_group.add_argument(
        "--split-max-lines", type=int, default=100000,
        help="Max lines per output part file (default: 100000)",
    )
    out_group.add_argument(
        "--progress-threshold", type=int, default=100,
        help="Stop at this %% completion (default: 100)",
    )

    # Data loading
    data_group = parser.add_argument_group("Data Loading")
    data_group.add_argument(
        "--max-text-length", type=int, default=None,
        help="Skip items with text longer than this",
    )
    data_group.add_argument(
        "--batch-size", type=int, default=5000,
        help="Streaming batch size (default: 5000)",
    )

    # Health check options
    hc_group = parser.add_argument_group("Health Check Options")
    hc_group.add_argument("--health-check-output", default=None)
    hc_group.add_argument("--verbose", action="store_true")

    # Filter options
    flt_group = parser.add_argument_group("Filter Options")
    flt_group.add_argument("--filter-output", default=None)

    return parser


def cmd_list():
    """List all available components."""
    from hyperdistill.tasks import TaskRegistry
    from hyperdistill.providers import ProviderRegistry
    from hyperdistill.filters import FILTER_REGISTRY

    print("=" * 55)
    print("Available Tasks:")
    for name in TaskRegistry.list_tasks():
        print(f"  - {name}")
    print()
    print("Available Providers (API backend):")
    for name in ProviderRegistry.list_providers():
        print(f"  - {name}")
    print()
    print("Available Backends:")
    print(f"  - api  (OpenAI-compatible API via AsyncOpenAI)")
    print(f"  - cli  (subprocess agent via claude CLI)")
    print()
    print("Available Filters:")
    for name in sorted(FILTER_REGISTRY.keys()):
        print(f"  - {name}")
    print("=" * 55)


def cmd_health_check(args):
    from hyperdistill.health_check import run_health_check
    if not args.config:
        print("Error: --config is required for health check")
        sys.exit(1)
    run_health_check(
        config_path=args.config,
        output_path=args.health_check_output,
        verbose=args.verbose,
    )


def cmd_filter(args):
    from hyperdistill.filters import get_filter
    if not args.input:
        print("Error: -i/--input is required for filtering")
        sys.exit(1)
    flt = get_filter(args.filter)
    output = flt.filter_file(args.input, args.filter_output)
    print(f"Filtered output: {output}")


def _build_api_backend(args):
    """Build ApiBackend from CLI args."""
    from hyperdistill.config import (
        load_config, build_api_configs_from_args, parse_concurrencies,
    )
    from hyperdistill.providers import get_provider
    from hyperdistill.client_pool import ClientPool
    from hyperdistill.backends import ApiBackend

    # Load API configs
    api_configs = None
    api_concurrencies = None

    if args.config:
        api_configs, api_concurrencies = load_config(args.config)
    elif args.api_keys or (args.api_key and "," in args.api_key):
        keys_str = args.api_keys or args.api_key
        keys = [k.strip() for k in keys_str.split(",")]
        urls_str = args.base_urls or args.base_url
        if not urls_str:
            print("Error: --base-url required with --api-keys")
            sys.exit(1)
        urls = [u.strip() for u in urls_str.split(",")]
        models_str = args.models or args.model
        if not models_str:
            print("Error: --model required with --api-keys")
            sys.exit(1)
        models = [m.strip() for m in models_str.split(",")]
        api_configs = build_api_configs_from_args(keys, urls, models)
    elif args.api_key and args.base_url and args.model:
        api_configs = [{
            "api_key": args.api_key,
            "base_url": args.base_url,
            "model": args.model,
        }]
    else:
        print("Error: --config or (--api-key, --base-url, --model) required for API backend")
        sys.exit(1)

    if api_concurrencies is None and args.api_concurrencies:
        api_concurrencies = parse_concurrencies(
            args.api_concurrencies, len(api_configs)
        )

    # Auto workers
    if args.workers is None:
        if api_concurrencies:
            args.workers = sum(api_concurrencies)
        else:
            args.workers = 10

    provider = get_provider(args.provider)
    client_pool = ClientPool(
        api_configs=api_configs,
        api_concurrencies=api_concurrencies,
        config_path=args.config,
    )

    return ApiBackend(
        client_pool=client_pool,
        provider=provider,
        temperature=args.temperature,
        top_p=args.top_p,
        timeout=args.timeout,
    )


def _build_cli_backend(args):
    """Build CliBackend from CLI args."""
    from hyperdistill.backends import CliBackend

    # Auto workers for CLI (lower default — each subprocess is heavier)
    if args.workers is None:
        args.workers = 4

    extra_args = []
    if args.cli_extra_args:
        extra_args = [a.strip() for a in args.cli_extra_args.split(",") if a.strip()]

    # Parse skills list
    skills = None
    if args.skills:
        skills = [s.strip() for s in args.skills.split(",") if s.strip()]

    agents_dir = args.agents_dir
    if args.agent_name and not agents_dir:
        agents_dir = ".claude/agents"

    skills_dir = args.skills_dir
    if skills and not skills_dir:
        skills_dir = ".claude/skills"

    return CliBackend(
        cli_cmd=args.cli_cmd,
        model=args.cli_model,
        agent_instructions_path=args.agent_instructions,
        agent_name=args.agent_name,
        skills=skills,
        agents_dir=agents_dir,
        skills_dir=skills_dir,
        timeout=args.cli_timeout,
        cli_extra_args=extra_args,
    )


def cmd_distill(args):
    """Run the distillation pipeline."""
    from hyperdistill.tasks import get_task
    from hyperdistill.output_writer import OutputWriter
    from hyperdistill.engine import DistillEngine
    from hyperdistill.utils import log

    # Validate required args
    if not args.task:
        print("Error: --task is required")
        sys.exit(1)
    if not args.input:
        print("Error: -i/--input is required")
        sys.exit(1)
    if not args.output:
        print("Error: -o/--output is required")
        sys.exit(1)

    # Print config
    print("=" * 55)
    print("HyperDistill Configuration")
    print("=" * 55)
    for arg in vars(args):
        val = getattr(args, arg)
        if val is not None and arg not in ("health_check", "filter", "list"):
            print(f"  {arg}: {val}")
    print("=" * 55)
    print()

    # Build backend
    if args.backend == "cli":
        backend = _build_cli_backend(args)
    else:
        backend = _build_api_backend(args)

    # Initialize task
    task = get_task(args.task)

    # OutputWriter will automatically use task.get_id_fields() for ID extraction
    writer = OutputWriter(
        output_file=args.output,
        split_max_lines=args.split_max_lines,
        id_fields=["id", "data_id"],  # Fallback fields when task doesn't provide get_id_fields()
        progress_threshold=args.progress_threshold,
    )

    engine = DistillEngine(
        task=task,
        backend=backend,
        writer=writer,
        input_file=args.input,
        max_workers=args.workers,
        progress_threshold=args.progress_threshold,
        max_retries=args.max_retries,
        max_text_length=args.max_text_length,
        batch_size=args.batch_size,
    )

    log("Starting distillation pipeline")
    asyncio.run(engine.run())
    log("Pipeline completed")


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.health_check:
        cmd_health_check(args)
    elif args.filter:
        cmd_filter(args)
    elif args.task:
        cmd_distill(args)
    else:
        parser.print_help()
        print()
        print("Tip: Use --list to see available tasks, providers, and filters")


if __name__ == "__main__":
    main()
