# Modal Parallel Search

<img width="1280" height="900" alt="modal-parallel-search-global-news" src="https://github.com/user-attachments/assets/eae93c64-ebda-4900-8faa-16a0d679574d" />

> Give your coding agent a tiny web-search superpower: one CLI command fans many searches out across Modal serverless containers and returns clean Markdown notes by default, or JSON when requested.

`modal-parallel-search` is a Pi skill + Modal app for agentic web search. It is intentionally small: no browser, no API keys for search, no hosted service to maintain. Your agent shells out to `modal run`, Modal spins up lightweight Python containers, each query runs independently, and the results come back as human-readable Markdown notes by default, or as JSON with `--output-format json`.

Although this repo ships as a Pi package, the core idea is **not Pi-specific**. We built this skill for any AI coding agent with terminal access: OpenClaw, Hermes, Codex, Claude Code, Pi, and so on. If the agent can run a shell command, it can use this Modal-powered CLI.

This is the pattern: **coding agents are great at using CLIs; Modal is great at bursting compute on demand.** Put them together and suddenly an agent can do parallel research without you building infrastructure.

## Why Modal instead of local fan-out?

When an agent gets ambitious, "just run a few searches" can turn into multiple Python processes, dependency installs, browser-ish HTTP clients, or even Docker containers. On a small machine like a MacBook Air M1, that kind of local fan-out can make the laptop hot, drain battery, and steal resources from the editor you are actually trying to use.

Modal moves that bursty work off your laptop. Your Mac stays a thin control plane: Pi calls a CLI, the CLI asks Modal for serverless containers, and the real work runs in the cloud. This is especially nice for coding-agent workflows because you get parallelism without turning your development machine into the cluster.

It also makes the workflow portable. Once Modal auth is set up, the same command works from a MacBook Air, a Mac mini, or any other machine with the repo and the Modal CLI installed. Clone the repo, authenticate Modal, run the CLI — the compute environment is defined in code by the Modal image, not by whatever happens to be installed on that specific Mac.

## Why this is fun

- **Parallel by default** — send 1 query or 20 angles; each query gets its own Modal function call.
- **More breadth, faster** — parallel searches let agents explore multiple phrasings, sources, and angles at once, which speeds up wide web research and increases the breadth of information gathered.
- **Agent-friendly output** — Markdown notes by default for humans and LLMs; structured JSON is available with `--output-format json`.
- **No search API key required** — powered by [`ddgs`](https://pypi.org/project/ddgs/) backends.
- **Tiny surface area** — one Python file and one skill file.
- **Tiny serverless footprint** — `ddgs` is lightweight, and each Modal search container only needs a small CPU/memory slice for a short burst, so typical runs cost extremely close to zero.
- **Modal free-credit friendly** — As of May 23, 2026, Modal accounts receive **$30/month in free credits after adding a credit card**, and this parallel web search workload typically consumes very near to **$0 USD**.
- **Agent Skills ready** — place the skill folder at `~/.agents/skills/modal-parallel-search` and any compatible agent can find it.

> Note: you still need a Modal account/CLI. Modal usage may be billed depending on your account, free credits, and current Modal pricing. As of May 23, 2026, Modal gives accounts $30/month in free credits when a credit card is added, and this tool's workload is intentionally tiny, but always check your own usage. Please respect search provider terms and rate limits.

## Quick start

Install the skill into the shared Agent Skills folder, install Modal, then run a smoke test:

```bash
curl -fsSL https://raw.githubusercontent.com/krittaprot/modal-parallel-search/main/scripts/install-skill.sh | bash
uv tool install modal
modal setup
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "Modal Python serverless" \
  --max-results 1
```

The important path is:

```text
~/.agents/skills/modal-parallel-search/
├── SKILL.md
└── scripts/
    └── modal_search_cli.py
```

Any AI agent with terminal access can use that folder. Agent Skills-aware tools can load `SKILL.md`; simpler terminal agents can directly run the Python CLI.

## First-time Modal setup

You need the Modal CLI installed and authenticated once on your local machine.

### 1. Install the Modal Python package / CLI

Recommended with [`uv`](https://docs.astral.sh/uv/):

```bash
uv tool install modal
```

If you already installed Modal with `uv`, upgrade it with:

```bash
uv tool upgrade modal
```

If you do not use `uv`, regular `pip` still works:

```bash
python3 -m pip install modal
```

Verify the CLI is available:

```bash
modal --version
```

### 2. Create or connect your Modal account

As of May 23, 2026, Modal gives accounts **$30/month in free credits after adding a credit card**. This parallel web search tool uses short-lived, lightweight CPU containers, so normal searches should consume very near to **$0 USD** against that credit.

For an interactive local machine, run:

```bash
modal setup
```

This opens a browser flow to create/sign in to your Modal account and stores local credentials, typically in `~/.modal.toml`.

### 3. If you already have a token

If you created a token in the Modal dashboard or need to configure a non-browser environment, set it directly:

```bash
modal token set --token-id "YOUR_TOKEN_ID" --token-secret "YOUR_TOKEN_SECRET"
```

For CI or other automated environments, Modal also supports environment variables:

```bash
export MODAL_TOKEN_ID="YOUR_TOKEN_ID"
export MODAL_TOKEN_SECRET="YOUR_TOKEN_SECRET"
```

Never commit token values to this repo.

### 4. Verify auth with this repo

```bash
modal token info
modal run scripts/modal_search_cli.py \
  --query "Modal Python serverless" \
  --max-results 1
```

Run a single search:

```bash
modal run scripts/modal_search_cli.py \
  --query "Modal Python serverless coding agents" \
  --max-results 3
```

Run several searches in parallel:

```bash
modal run scripts/modal_search_cli.py \
  --queries-json '["pi coding agent", "Modal serverless Python", "coding agents CLI tools"]' \
  --max-results 5 \
  --timelimit w
```

Or with a file:

```bash
modal run scripts/modal_search_cli.py \
  --queries-file examples/queries.txt
```

## Install as an agent skill

### Recommended: one-command install

```bash
curl -fsSL https://raw.githubusercontent.com/krittaprot/modal-parallel-search/main/scripts/install-skill.sh | bash
```

This keeps the full repo checkout here:

```text
~/.agents/skills/.repos/modal-parallel-search
```

And symlinks the actual skill folder here:

```text
~/.agents/skills/modal-parallel-search
```

The skill folder is the part agents need. `SKILL.md` should be directly inside it:

```text
~/.agents/skills/modal-parallel-search/
├── SKILL.md
└── scripts/
    └── modal_search_cli.py
```

### Manual install

If you do not want to pipe a script into `bash`, run the same steps manually:

```bash
mkdir -p ~/.agents/skills/.repos
git clone https://github.com/krittaprot/modal-parallel-search.git \
  ~/.agents/skills/.repos/modal-parallel-search
rm -rf ~/.agents/skills/modal-parallel-search
ln -s ~/.agents/skills/.repos/modal-parallel-search/skills/modal-parallel-search \
  ~/.agents/skills/modal-parallel-search
```

### Use from any terminal-capable agent

Any AI agent that can run shell commands can call the CLI directly:

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "recent Modal serverless agent examples"
```

Agent Skills-compatible tools can additionally read:

```text
~/.agents/skills/modal-parallel-search/SKILL.md
```

### Update later

```bash
git -C ~/.agents/skills/.repos/modal-parallel-search pull
```

The symlink at `~/.agents/skills/modal-parallel-search` keeps pointing at the updated skill folder.

### Pi package alternative

If you prefer Pi's package manager instead, this also works:

```bash
pi install git:github.com/krittaprot/modal-parallel-search
```

Then ask Pi to use the skill, or invoke it explicitly:

```text
/skill:modal-parallel-search search recent Modal serverless agent examples
```

## CLI options

```text
--query          One query, or multiple joined by ";;"
--queries-json   JSON array of query strings
--queries-file   File with one query per line
--max-results    Results per query [default: 5]
--backend        auto, yahoo, brave, duckduckgo [default: auto]
--region         Search region [default: us-en]
--safesearch     on, moderate, off [default: moderate]
--timelimit      d, w, m, y
--fetch-pages    Fetch and extract top result pages [default: false]
--fetch-top-n    Top results per query to fetch [default: 3]
--fetch-chars    Max extracted characters per page [default: 4000]
--output-format  markdown or json [default: markdown]
--benchmark      Compare sequential vs parallel wall time [default: false]
```

Show help:

```bash
modal run scripts/modal_search_cli.py --help
```

## Page fetch + extract mode

Search results usually include title, URL, and snippet. When you want deeper context, add `--fetch-pages` to fetch the top results for each query in parallel and attach extracted readable text.

```bash
modal run scripts/modal_search_cli.py \
  --query "Modal serverless pricing examples" \
  --max-results 5 \
  --fetch-pages \
  --fetch-top-n 3
```

Markdown output is the default because it is easy for humans and LLMs to continue working with. Use JSON if another tool needs a structured payload:

```bash
modal run scripts/modal_search_cli.py \
  --query "Modal serverless pricing examples" \
  --fetch-pages \
  --output-format json
```

## Markdown research notes

By default, the CLI prints Markdown notes grouped by query, with source URLs, snippets, and optional fetched page extracts. This makes the output directly useful as a research scratchpad for coding agents.

```bash
modal run scripts/modal_search_cli.py \
  --queries-json '["Modal Python serverless", "Modal web endpoints"]' \
  --max-results 3
```

## Benchmark examples

Use `--benchmark` to compare sequential query execution against the default parallel fan-out. The benchmark runs the same query set sequentially and in parallel, then reports wall-clock timings and speedup.

```bash
modal run scripts/modal_search_cli.py \
  --queries-file examples/benchmark_queries.txt \
  --max-results 3 \
  --benchmark
```

## How it works

1. The local entrypoint parses one or many queries.
2. Each query becomes a serializable search spec.
3. The CLI calls `search_one.spawn(...)` for every query.
4. Modal runs each search in a separate lightweight container.
5. Optional page fetch mode calls `fetch_page.spawn(...)` for top result URLs and extracts readable text.
6. Results are collected in input order and printed as Markdown by default, or JSON with `--output-format json`.

The remote image is deliberately minimal:

```python
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("ddgs==9.14.4")
)
```

## Example output shape

Default Markdown output:

```md
# Search research notes

- Queries: 1
- Wall time: 2.481s

## 1. Modal Python serverless

Found 3 results in 1.882s.

### 1.1. Modal: High-performance AI infrastructure
Source: https://modal.com/...

Snippet text...
```

JSON output with `--output-format json`:

```json
{
  "query_count": 2,
  "wall_seconds": 3.214,
  "results": [
    {
      "query": "Modal Python serverless",
      "backend": "auto",
      "elapsed_seconds": 1.882,
      "result_count": 3,
      "results": [
        {"title": "...", "href": "https://...", "body": "..."}
      ]
    }
  ]
}
```

## Repository layout

```text
.
├── SKILL.md
├── package.json
├── scripts/
│   ├── install-skill.sh
│   └── modal_search_cli.py
└── examples/
    ├── benchmark_queries.txt
    └── queries.txt
```

## Roadmap ideas

- Result caching in a Modal Volume.

## License

MIT
