---
name: modal-parallel-search
description: Use this skill whenever an AI/coding agent needs current web information, no-key web search, parallel research across several queries, Markdown research notes, optional page fetching/extraction, or a sequential-vs-parallel Modal benchmark. Especially use it when the user is new to agents or terminals and needs gentle setup guidance for Modal, shell commands, or installing an Agent Skill.
license: MIT
---

# Modal Parallel Search

This skill gives an agent a simple terminal command for web research:

```bash
modal run scripts/modal_search_cli.py --query "your search terms"
```

It uses Modal serverless containers to run one or many searches in parallel and returns clean Markdown by default.

## How to help the user

Be friendly and assume the user may be new to terminals.

- Explain each command in one short sentence before asking them to run it.
- Prefer copy/paste-ready commands.
- Start with the smallest smoke test before using multi-query search or page fetching.
- Never print, store, or commit Modal token secrets.
- If something fails, translate the error into the next concrete step instead of dumping jargon.

## First-time setup checklist

From the skill/repo folder, verify these in order:

```bash
modal --version
modal token info
modal run scripts/modal_search_cli.py --query "Modal Python serverless" --max-results 1
```

If `modal` is missing, install it:

```bash
uv tool install modal
```

If the user does not have `uv`, use Python/pip instead:

```bash
python3 -m pip install --user modal
```

If Modal is not authenticated, use the browser setup flow:

```bash
modal setup
modal token info
```

For a headless machine or pre-created token:

```bash
modal token set --token-id "YOUR_TOKEN_ID" --token-secret "YOUR_TOKEN_SECRET"
# or export environment variables for this shell/session:
export MODAL_TOKEN_ID="YOUR_TOKEN_ID"
export MODAL_TOKEN_SECRET="YOUR_TOKEN_SECRET"
```

Remind the user: do not paste real token values into chat unless they intentionally trust the environment, and never commit them.

## Common commands

Single search:

```bash
modal run scripts/modal_search_cli.py \
  --query "Modal Python serverless coding agents" \
  --max-results 3
```

Several searches in parallel with JSON input (best for agents):

```bash
modal run scripts/modal_search_cli.py \
  --queries-json '["Modal serverless Python", "coding agents web search CLI", "Agent Skills examples"]' \
  --max-results 5
```

Several searches with the quick `;;` separator:

```bash
modal run scripts/modal_search_cli.py \
  --query "Modal pricing;;Modal web endpoints Python;;Modal volumes examples"
```

Many searches from a file:

```bash
modal run scripts/modal_search_cli.py \
  --queries-file examples/queries.txt
```

Fetch and extract top pages when snippets are not enough:

```bash
modal run scripts/modal_search_cli.py \
  --query "Modal web endpoints examples" \
  --max-results 5 \
  --fetch-pages \
  --fetch-top-n 3
```

Return structured JSON for another tool. Use Modal's `-q` flag so progress messages do not mix with JSON:

```bash
modal run -q scripts/modal_search_cli.py \
  --queries-json '["Modal Python", "Modal pricing"]' \
  --output-format json
```

Benchmark sequential vs parallel fan-out:

```bash
modal run scripts/modal_search_cli.py \
  --queries-file examples/benchmark_queries.txt \
  --max-results 3 \
  --benchmark
```

## Options to remember

- `--query`: one query. Use `;;` inside it for quick multi-query input.
- `--queries-json`: JSON array of query strings; safest for agents and complex query text.
- `--queries-file`: one query per line; blank lines and `#` comments are ignored.
- `--max-results N`: results per query.
- `--backend auto`: default. Other values: `yahoo`, `brave`, `duckduckgo`.
- `--timelimit d|w|m|y`: filter to day/week/month/year when supported.
- `--fetch-pages`: fetch top result URLs and attach readable extracts.
- `--output-format markdown|json`: Markdown for humans/LLMs, JSON for tools.
- `--show-events`: print spawn/status events; leave off when another tool needs clean JSON.
- `--benchmark`: compare sequential vs parallel wall time for the same query set.

Modal local entrypoints treat `--query` as a single scalar. Repeating `--query` flags will not accumulate. Use `;;`, `--queries-json`, or `--queries-file` instead.

## Troubleshooting cues

- `modal: command not found`: install Modal with `uv tool install modal` or `python3 -m pip install --user modal`.
- Authentication/token error: run `modal setup`, then `modal token info`.
- No results or backend error: retry once, then try `--backend duckduckgo` or fewer queries/results.
- JSON parsing failed: use valid JSON, e.g. `'["first query", "second query"]'`; on Windows PowerShell, escaping may differ.
- Page fetch failed: search still worked; some sites block automated fetches. Use the source URL/snippet or try another result.

## Validation

Use the built-in help when uncertain:

```bash
modal run scripts/modal_search_cli.py --help
```

Cheap smoke test:

```bash
modal run scripts/modal_search_cli.py --query "Modal Python serverless" --max-results 1
```
