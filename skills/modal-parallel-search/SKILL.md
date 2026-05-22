---
name: modal-parallel-search
description: Use this skill when an agent needs free/no-key web search through a Modal-powered parallel search CLI, including one query with many results or multiple queries fanned out across serverless containers.
license: MIT
---

# Modal Parallel Search

Use the repo CLI when you need lightweight no-key web search from an agent.

## First-time setup

If Modal is not installed or authenticated locally:

```bash
python3 -m pip install modal
modal setup
modal token info
```

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

## Recommended Defaults

Keep `--backend auto` unless the user asks to benchmark or isolate engines.

Use `--max-results` when the agent needs broader coverage for a single query. Use `--query "q1;;q2;;q3"`, `--queries-json`, or `--queries-file` when the agent needs multiple angles searched in parallel.

## Validation

Use Modal's generated help when uncertain:

```bash
modal run scripts/modal_search_cli.py --help
```

For a cheap smoke test:

```bash
modal run scripts/modal_search_cli.py --query "Modal Python serverless" --max-results 1
```
