# Modal Parallel Search

> Give your coding agent a tiny web-search superpower: one CLI command fans many searches out across Modal serverless containers and returns clean JSON.

`modal-parallel-search` is a Pi skill + Modal app for agentic web search. It is intentionally small: no browser, no API keys for search, no hosted service to maintain. Your agent shells out to `modal run`, Modal spins up lightweight Python containers, each query runs independently, and the results come back in one JSON payload.

Although this repo ships as a Pi package, the core idea is **not Pi-specific**. We built this skill for any AI coding agent with terminal access: OpenClaw, Hermes, Codex, Claude Code, Pi, and so on. If the agent can run a shell command, it can use this Modal-powered CLI.

This is the pattern: **coding agents are great at using CLIs; Modal is great at bursting compute on demand.** Put them together and suddenly an agent can do parallel research without you building infrastructure.

## Why Modal instead of local fan-out?

When an agent gets ambitious, "just run a few searches" can turn into multiple Python processes, dependency installs, browser-ish HTTP clients, or even Docker containers. On a small machine like a MacBook Air M1, that kind of local fan-out can make the laptop hot, drain battery, and steal resources from the editor you are actually trying to use.

Modal moves that bursty work off your laptop. Your Mac stays a thin control plane: Pi calls a CLI, the CLI asks Modal for serverless containers, and the real work runs in the cloud. This is especially nice for coding-agent workflows because you get parallelism without turning your development machine into the cluster.

It also makes the workflow portable. Once Modal auth is set up, the same command works from a MacBook Air, a Mac mini, or any other machine with the repo and the Modal CLI installed. Clone the repo, authenticate Modal, run the CLI — the compute environment is defined in code by the Modal image, not by whatever happens to be installed on that specific Mac.

## Why this is fun

- **Parallel by default** — send 1 query or 20 angles; each query gets its own Modal function call.
- **More breadth, faster** — parallel searches let agents explore multiple phrasings, sources, and angles at once, which speeds up wide web research and increases the breadth of information gathered.
- **Agent-friendly output** — structured JSON, easy to grep, parse, summarize, or cite.
- **No search API key required** — powered by [`ddgs`](https://pypi.org/project/ddgs/) backends.
- **Tiny surface area** — one Python file and one skill file.
- **Tiny serverless footprint** — `ddgs` is lightweight, and each Modal search container only needs a small CPU/memory slice for a short burst, so typical runs cost extremely close to zero.
- **Pi package ready** — install from GitHub and expose it as `/skill:modal-parallel-search`.

> Note: you still need a Modal account/CLI. Modal usage may be billed depending on your account, free credits, and current Modal pricing. The workload is intentionally tiny, but always check your own usage. Please respect search provider terms and rate limits.

## Quick start

```bash
git clone https://github.com/krittaprot/modal-parallel-search.git
cd modal-parallel-search
uv tool install modal
modal setup
```

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
modal run skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "Modal Python serverless" \
  --max-results 1
```

Run a single search:

```bash
modal run skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "Modal Python serverless coding agents" \
  --max-results 3
```

Run several searches in parallel:

```bash
modal run skills/modal-parallel-search/scripts/modal_search_cli.py \
  --queries-json '["pi coding agent", "Modal serverless Python", "coding agents CLI tools"]' \
  --max-results 5 \
  --timelimit w
```

Or with a file:

```bash
modal run skills/modal-parallel-search/scripts/modal_search_cli.py \
  --queries-file examples/queries.txt
```

## Install as a Pi package

Pi can install packages directly from git:

```bash
pi install git:github.com/krittaprot/modal-parallel-search
```

Then ask Pi to use the skill, or invoke it explicitly:

```text
/skill:modal-parallel-search search recent Modal serverless agent examples
```

Pi discovers the skill from `skills/modal-parallel-search/SKILL.md` via the `package.json` manifest.

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
```

Show help:

```bash
modal run skills/modal-parallel-search/scripts/modal_search_cli.py --help
```

## How it works

1. The local entrypoint parses one or many queries.
2. Each query becomes a serializable search spec.
3. The CLI calls `search_one.spawn(...)` for every query.
4. Modal runs each search in a separate lightweight container.
5. Results are collected in input order and printed as JSON.

The remote image is deliberately minimal:

```python
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("ddgs==9.14.4")
)
```

## Example output shape

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
├── package.json
├── skills/
│   └── modal-parallel-search/
│       ├── SKILL.md
│       └── scripts/
│           └── modal_search_cli.py
└── examples/
    └── queries.txt
```

## Roadmap ideas

- Optional page fetch + extract mode for top results.
- Result caching in a Modal Volume.
- Markdown output mode for human-readable research notes.
- Agent benchmark examples: single query vs parallel query wall time.

## License

MIT
