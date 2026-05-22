# Modal Parallel Search

<img width="1280" height="900" alt="modal-parallel-search-global-news" src="https://github.com/user-attachments/assets/eae93c64-ebda-4900-8faa-16a0d679574d" />

> A tiny web-search superpower for AI coding agents: run one command, fan out several searches across Modal serverless containers, and get clean Markdown notes back.

`modal-parallel-search` is an Agent Skill plus a Modal-powered CLI. It is useful when an AI agent needs current web information but you do not want to set up a search API key, browser automation, a hosted service, or local fan-out scripts.

It works with any terminal-capable coding agent: Pi, Claude Code, Codex-style agents, OpenClaw, Hermes, or your own agent loop. If the agent can run `modal run ...`, it can use this tool.

## In plain English

- **What it does:** searches the web and returns research notes.
- **Why Modal:** the bursty work runs in short-lived cloud containers instead of on your laptop.
- **What you need:** a terminal, Python/uv or pip, and a Modal account/token.
- **Search API keys:** none required for search. The CLI uses [`ddgs`](https://pypi.org/project/ddgs/) backends.
- **Typical output:** Markdown, because it is easy for people and AI agents to read.
- **Cost note:** this workload is intentionally tiny, but Modal usage depends on your account and current Modal pricing. Check your Modal dashboard and pricing page if cost matters.

## Fastest quick start

Copy/paste these commands into your terminal:

```bash
curl -fsSL https://raw.githubusercontent.com/krittaprot/modal-parallel-search/main/scripts/install-skill.sh | bash
uv tool install modal
modal setup
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "Modal Python serverless" \
  --max-results 1
```

What those commands do:

1. Install this skill into `~/.agents/skills/modal-parallel-search`.
2. Install the Modal CLI.
3. Sign in to Modal in your browser.
4. Run a tiny smoke-test search.

If you do not have `uv`, install Modal with pip instead:

```bash
python3 -m pip install --user modal
```

## What gets installed

The installer keeps the repo here:

```text
~/.agents/skills/.repos/modal-parallel-search
```

And creates this agent-friendly path:

```text
~/.agents/skills/modal-parallel-search
```

The important files are:

```text
~/.agents/skills/modal-parallel-search/
├── SKILL.md
├── scripts/
│   ├── install-skill.sh
│   └── modal_search_cli.py
└── examples/
    ├── benchmark_queries.txt
    └── queries.txt
```

Agent Skills-aware tools read `SKILL.md`. Simpler terminal agents can directly call `scripts/modal_search_cli.py`.

## First-time setup, slowly

### 1. Make sure Modal is installed

```bash
modal --version
```

If that says `command not found`, install Modal:

```bash
uv tool install modal
```

Or with pip:

```bash
python3 -m pip install --user modal
```

### 2. Sign in to Modal

For a normal laptop/desktop:

```bash
modal setup
```

This opens a browser login flow and stores credentials locally, usually in `~/.modal.toml`.

Then verify:

```bash
modal token info
```

### 3. Headless server or existing token

If you cannot use a browser, create a token in Modal and set it directly:

```bash
modal token set --token-id "YOUR_TOKEN_ID" --token-secret "YOUR_TOKEN_SECRET"
```

For CI or temporary shells:

```bash
export MODAL_TOKEN_ID="YOUR_TOKEN_ID"
export MODAL_TOKEN_SECRET="YOUR_TOKEN_SECRET"
```

Never commit token values to git.

### 4. Run the smoke test

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "Modal Python serverless" \
  --max-results 1
```

If you see `# Search research notes`, it worked.

## Install as an Agent Skill

### Recommended installer

```bash
curl -fsSL https://raw.githubusercontent.com/krittaprot/modal-parallel-search/main/scripts/install-skill.sh | bash
```

You can customize the install location:

```bash
AGENTS_SKILLS_DIR="$HOME/.agents/skills" bash scripts/install-skill.sh
```

You can point the installer at a fork:

```bash
MODAL_PARALLEL_SEARCH_REPO_URL="https://github.com/YOU/modal-parallel-search.git" \
  bash scripts/install-skill.sh
```

### Manual install

If you prefer not to pipe a script into `bash`:

```bash
mkdir -p ~/.agents/skills/.repos
git clone https://github.com/krittaprot/modal-parallel-search.git \
  ~/.agents/skills/.repos/modal-parallel-search
rm -rf ~/.agents/skills/modal-parallel-search
ln -s ~/.agents/skills/.repos/modal-parallel-search \
  ~/.agents/skills/modal-parallel-search
```

Check it:

```bash
ls ~/.agents/skills/modal-parallel-search/SKILL.md
```

### Update later

```bash
git -C ~/.agents/skills/.repos/modal-parallel-search pull --ff-only
```

The symlink at `~/.agents/skills/modal-parallel-search` keeps pointing at the updated repo.

### Pi package alternative

If you use Pi's package manager:

```bash
pi install git:github.com/krittaprot/modal-parallel-search
```

Then ask Pi to use the skill, or invoke it explicitly:

```text
/skill:modal-parallel-search search recent Modal serverless agent examples
```

## Everyday usage

Run a single search:

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "recent Modal serverless agent examples" \
  --max-results 3
```

Run several searches in parallel:

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --queries-json '["pi coding agent", "Modal serverless Python", "coding agents CLI tools"]' \
  --max-results 5 \
  --timelimit w
```

Use a plain text file with one query per line:

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --queries-file ~/.agents/skills/modal-parallel-search/examples/queries.txt
```

Quick multi-query shortcut:

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "Modal pricing;;Modal web endpoints Python;;Modal volumes examples"
```

> Modal local entrypoints accept `--query` as one scalar value. Repeating `--query` flags does not build a list. Use `;;`, `--queries-json`, or `--queries-file` for multiple queries.

## CLI options

```text
--query          One query, or multiple joined by ";;"
--queries-json   JSON array of query strings
--queries-file   File with one query per line; # comments and blanks are ignored
--max-results    Results per query [default: 5]
--backend        auto, yahoo, brave, duckduckgo [default: auto]
--region         Search region [default: us-en]
--safesearch     on, moderate, off [default: moderate]
--timelimit      d, w, m, y
--fetch-pages    Fetch and extract top result pages [default: false]
--fetch-top-n    Top results per query to fetch [default: 3]
--fetch-chars    Max extracted characters per page [default: 4000]
--output-format  markdown or json [default: markdown]
--show-events    Print spawn/status events before final output [default: false]
--benchmark      Compare sequential vs parallel wall time [default: false]
```

Show help:

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py --help
```

## Page fetch + extract mode

Search results include title, URL, and snippet. Add `--fetch-pages` when snippets are not enough and you want readable text from the top result pages.

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "Modal serverless pricing examples" \
  --max-results 5 \
  --fetch-pages \
  --fetch-top-n 3
```

Some sites block automated fetching. That is normal. The search result URL and snippet still remain in the notes.

## Markdown and JSON output

Markdown is the default:

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --queries-json '["Modal Python serverless", "Modal web endpoints"]' \
  --max-results 3
```

Use JSON when another tool needs to parse the result. Add Modal's `-q` flag so Modal progress messages do not mix with the JSON:

```bash
modal run -q ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --query "Modal serverless pricing examples" \
  --output-format json
```

## Benchmark parallel fan-out

Use `--benchmark` to compare sequential query execution against parallel fan-out. This runs the same query set two ways and reports wall-clock timings.

```bash
modal run ~/.agents/skills/modal-parallel-search/scripts/modal_search_cli.py \
  --queries-file ~/.agents/skills/modal-parallel-search/examples/benchmark_queries.txt \
  --max-results 3 \
  --benchmark
```

## Troubleshooting

### `modal: command not found`

Install Modal:

```bash
uv tool install modal
# or
python3 -m pip install --user modal
```

If pip installed it but your shell still cannot find it, restart the terminal or add your Python user scripts directory to `PATH`.

### Modal says you are not authenticated

Run:

```bash
modal setup
modal token info
```

### `git: command not found`

Install Git first. On macOS, running `git --version` usually prompts Apple developer tools installation. On Ubuntu/Debian:

```bash
sudo apt-get update && sudo apt-get install -y git
```

### JSON input errors

Use valid JSON with double quotes:

```bash
--queries-json '["first query", "second query"]'
```

PowerShell quoting can be different; using `--queries-file` is often easier on Windows.

### No results or backend errors

Search backends can temporarily fail or rate-limit. Try:

```bash
--backend duckduckgo
```

Or reduce `--max-results` / query count and retry.

## How it works

1. The local Modal entrypoint parses one or many queries.
2. Each query becomes a serializable search spec.
3. The CLI calls `search_one.spawn(...)` for every query.
4. Modal runs searches in separate lightweight containers.
5. Optional page-fetch mode calls `fetch_page.spawn(...)` for top result URLs.
6. Results are collected in input order and printed as Markdown or JSON.

The Modal image is intentionally small:

```python
image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("ddgs==9.14.4")
)
```

## Example output shape

Markdown output:

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

JSON output:

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
├── README.md
├── package.json
├── scripts/
│   ├── install-skill.sh
│   └── modal_search_cli.py
└── examples/
    ├── benchmark_queries.txt
    └── queries.txt
```

## Roadmap ideas

- Optional result caching in a Modal Volume.
- More beginner-friendly wrappers for common agent workflows.
- Additional output templates for citations and comparison tables.

## License

MIT
