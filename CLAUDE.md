# Distill Pipeline — Project Context

## Project Location
`/volume/pt-coder/users/tuney/Script/distill_pipeline/`

## What This Is
A modular LLM data distillation framework, refactored from `raw2qa_new/` (7+ duplicated Python scripts). Supports two execution backends: **API** (AsyncOpenAI) and **CLI** (subprocess agent like `claude --bare`).

## Architecture
```
Engine (sliding-window concurrency)
  → Backend.call(item, task)
      ├── ApiBackend  → ClientPool → Provider → /chat/completions
      └── CliBackend  → asyncio.subprocess → claude --bare
  → Task.process_result()
  → OutputWriter.write()
```

## Key Modules
- **backends/**: `BaseBackend` ABC → `ApiBackend`, `CliBackend`
- **dataloader/**: Streaming JSONL/Parquet loaders (never full load), auto-detect by extension
- **providers/**: Kimi, DeepSeek, GLM, MiniMax, Default — each handles `extra_body` + response parsing
- **tasks/**: `query_response`, `code_to_question`, `text_to_response`, `stackoverflow`
- **engine.py**: Sliding-window async concurrency (fixed batch-stall bug at 5k items)
- **output_writer.py**: Partitioned JSONL output, single-pass streaming resume/dedup
- **client_pool.py**: Concurrency expansion, random selection, hot-reload
- **providers/test_providers.py**: End-to-end provider testing against real endpoints

## Important Design Decisions
- Registry pattern for Task/Provider/DataLoader — new ones just register
- MiniMax thinking is in `<think>` tags inside content (not `reasoning_content`)
- Engine uses sliding window (not batch drain) to avoid stalling
- OutputWriter only stores `processed_ids` set, not full data objects
- CliBackend uses `asyncio.create_subprocess_exec` for non-blocking subprocess

## Config Files
- `configs/config_{provider}.json` — API endpoint configs
- Agent instructions loaded from `.md` files, YAML frontmatter auto-stripped

## CLI Entry Point
```bash
# API mode
python run.py --task <name> --backend api --provider <name> --config <json> -i <in> -o <out>
# CLI agent mode
python run.py --task <name> --backend cli --cli-model <model> --agent-instructions <md> -i <in> -o <out>
```

## Related Files
- `DEVELOPMENT.md` — Full development history with 6 phases
- `README.md` — User-facing documentation
- Original project: `/volume/pt-coder/users/tuney/Script/raw2qa_new/`
- StackOverflow data: `/volume/pt-coder/users/tuney/pretrain_data/stackoverflow/`
