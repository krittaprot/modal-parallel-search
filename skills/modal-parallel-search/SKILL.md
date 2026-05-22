---
name: modal-parallel-search
description: Use this skill when an agent needs free/no-key web search through a Modal-powered parallel search CLI, including one query with many results, multiple queries fanned out across serverless containers, Markdown research notes, optional page fetch/extract, or sequential-vs-parallel benchmarks.
license: MIT
---

# Modal Parallel Search

Use the repo CLI when you need lightweight no-key web search from an agent.

## First-time setup

If Modal is not installed or authenticated locally:

```bash
uv tool install modal
modal setup
modal token info
```

If `uv` is not available, use `python3 -m pip install modal` instead.

For headless environments or pre-created tokens:

```bash
modal token set --token-id "YOUR_TOKEN_ID" --token-secret "YOUR_TOKEN_SECRET"
# or
export MODAL_TOKEN_ID="YOUR_TOKEN_ID"
export MODAL_TOKEN_SECRET="YOUR_TOKEN_SECRET"
```

Never commit token values.

From this skill folder root, run:

```bash
modal run scripts/modal_search_cli.py --query "search query"
```

From the repository root, run:

```bash
modal run skills/modal-parallel-search/scripts/modal_search_cli.py --query "search query"
```

**Multi-query via `;;` separator** (quick and shell-friendly):

```bash
modal run scripts/modal_search_cli.py \
  --query "stock market dip today;;why is the stock market down;;bond yields stock market dip"
```

**Multi-query via JSON** (recommended for 3+ queries or complex query strings containing `;;`):

```bash
modal run scripts/modal_search_cli.py \
  --queries-json '["stock market dip today", "why is the stock market down", "bond yields stock market dip"]'
```

> **Modal limitation:** `--query` is a single scalar parameter because Modal local entrypoints accept scalar CLI parameters. Repeated `--query` flags overwrite each other. Use `;;`, `--queries-json`, or `--queries-file` for multi-query.

## Common Options

- `--query`: query string. Use `;;` to pass multiple queries in one flag.
- `--max-results N`: result count per query. Use this for one query with many results.
- `--backend auto`: default and recommended. Other useful values: `yahoo`, `brave`, `duckduckgo`.
- `--queries-file path.txt`: one query per line; blank lines and `#` comments are ignored.
- `--queries-json '["q1", "q2"]'`: machine-friendly query input.
- `--region us-en`: search region passed to DDGS.
- `--safesearch moderate`: safe search setting. Valid values: `on`, `moderate`, `off`.
- `--timelimit d|w|m|y`: optional time filter for day, week, month, or year.
- `--fetch-pages`: fetch top result pages and extract readable text.
- `--fetch-top-n N`: number of top results per query to fetch. Default: `3`.
- `--fetch-chars N`: max extracted characters per fetched page. Default: `4000`.
- `--output-format markdown|json`: Markdown is the default for human-readable, LLM-friendly notes; JSON is available for tool parsing.
- `--benchmark`: run a sequential-vs-parallel wall-time comparison for the same query set.

## Recommended Defaults

Keep `--backend auto` unless the user asks to benchmark or isolate engines.

Use `--max-results` when the agent needs broader coverage for a single query. Use `--query "q1;;q2;;q3"`, `--queries-json`, or `--queries-file` when the agent needs multiple angles searched in parallel.

Default output is Markdown because it is readable and easy for LLMs to continue working with. Add `--output-format json` only when another tool needs structured JSON.

Use page fetch/extract when snippets are not enough:

```bash
modal run scripts/modal_search_cli.py \
  --query "Modal web endpoints examples" \
  --max-results 5 \
  --fetch-pages \
  --fetch-top-n 3
```

Use benchmarking when you need to show the wall-time benefit of parallel fan-out:

```bash
modal run scripts/modal_search_cli.py \
  --queries-json '["Modal serverless Python pricing", "Modal web endpoints Python", "Modal volumes cache examples"]' \
  --max-results 3 \
  --benchmark
```

## Validation

Use Modal's generated help when uncertain:

```bash
modal run scripts/modal_search_cli.py --help
```

For a cheap smoke test:

```bash
modal run scripts/modal_search_cli.py --query "Modal Python serverless" --max-results 1
```
