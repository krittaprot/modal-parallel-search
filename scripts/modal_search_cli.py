#!/usr/bin/env python3
"""Self-contained Modal parallel web-search CLI for coding agents.

Run examples:

  modal run modal_search_cli.py --query "your search"

  modal run modal_search_cli.py --query "q1;;q2;;q3"

  modal run modal_search_cli.py --queries-json '["query one", "query two"]'

  modal run modal_search_cli.py --queries-file queries.txt

  modal run modal_search_cli.py --query "your search" --fetch-pages --output-format markdown
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

# ---------------------------------------------------------------------------
# Custom help — Modal's local_entrypoint click wrapper doesn't expose per-option
# help text, so we intercept --help and print our own usage guide.
# ---------------------------------------------------------------------------

_USAGE = """\
Modal Parallel Search — web search for AI agents, powered by Modal.

If you are new: run this first from the repo/skill folder:

  modal run scripts/modal_search_cli.py --query "Modal Python serverless" --max-results 1

USAGE:
  modal run scripts/modal_search_cli.py [OPTIONS]

QUERY INPUT (pick one or combine):
  --query          One query, or multiple joined by ";;".
                   Example: --query "your query"
                   Example: --query "q1;;q2;;q3"

  --queries-json   JSON array of query strings. Best for agents and 3+ queries.
                   Example: --queries-json '["q1", "q2"]'

  --queries-file   File with one query per line. Blank lines and # comments are OK.

SEARCH OPTIONS:
  --max-results    Results per query.              [default: 5]
  --backend        Search backend.                 [default: auto]
                   Choices: auto, yahoo, brave, duckduckgo
  --region         Search region / locale.         [default: us-en]
  --safesearch     Safe-search level.              [default: moderate]
                   Choices: on, moderate, off
  --timelimit      Time filter.                    [default: none]
                   Choices: d (day), w (week), m (month), y (year)

PAGE FETCH + EXTRACT:
  --fetch-pages    Fetch and extract readable text from top search results.
  --fetch-top-n    Number of top results per query to fetch. [default: 3]
  --fetch-chars    Max extracted chars per page.   [default: 4000]

OUTPUT:
  --output-format  markdown or json.               [default: markdown]
                   Markdown is best for people/LLMs. JSON is best for tools.
                   For clean JSON stdout, use: modal run -q ... --output-format json
  --show-events    Print spawn/status events before the final output.
                   Leave this off when another tool needs clean JSON.

BENCHMARK:
  --benchmark      Compare sequential vs parallel search wall time.

NOTES:
  • Each query spawns a separate Modal container, so many queries run in parallel.
  • Repeated --query flags do NOT accumulate (Modal limitation).
    Use ;;, --queries-json, or --queries-file for multiple queries.
  • If Modal says you are not logged in, run: modal setup

EXAMPLES:
  # Single quick search
  modal run scripts/modal_search_cli.py --query "Modal Python serverless" --max-results 1

  # 5 parallel queries, filtered to last week
  modal run scripts/modal_search_cli.py \\
    --queries-json '["AI chips", "OpenAI news", "AI regulation"]' \\
    --timelimit w --max-results 5

  # Fetch/extract top pages and render Markdown notes
  modal run scripts/modal_search_cli.py \\
    --query "Modal serverless pricing examples" \\
    --max-results 5 --fetch-pages --fetch-top-n 3

  # Benchmark sequential vs parallel wall time
  modal run scripts/modal_search_cli.py \\
    --queries-file examples/benchmark_queries.txt \\
    --max-results 3 --benchmark
"""


def _print_help_and_exit() -> None:
    print(_USAGE)
    sys.exit(0)


def _user_error(message: str) -> None:
    """Print a short, beginner-friendly error and stop without a Python traceback."""
    print(f"Error: {message}", file=sys.stderr)
    print("\nRun this for examples and option help:", file=sys.stderr)
    print("  modal run scripts/modal_search_cli.py --help", file=sys.stderr)
    raise SystemExit(2)


# Modal's click parser grabs --help before main() runs, so we intercept at
# module import time — before the @app.local_entrypoint decorator is invoked.
if "--help" in sys.argv or "-h" in sys.argv:
    _print_help_and_exit()

import modal


app = modal.App(name="modal-parallel-search")

image = modal.Image.debian_slim(python_version="3.12").uv_pip_install("ddgs==9.14.4")


class ReadableHTMLExtractor(HTMLParser):
    """Small stdlib-only HTML-to-text extractor for search result pages."""

    BLOCK_TAGS = {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
    SKIP_TAGS = {"script", "style", "noscript", "svg", "canvas", "iframe"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag == "title":
            self._in_title = True
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self._in_title:
            self.title_parts.append(text)
        else:
            self.parts.append(text)
            self.parts.append(" ")

    def title(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.title_parts)).strip()

    def text(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        return "\n\n".join(lines).strip()


def emit_log(payload: dict[str, Any]) -> None:
    """Emit structured logs that are easy to grep or parse."""
    logging.info(json.dumps(payload, sort_keys=True))


@app.function(
    image=image,
    cpu=0.25,
    memory=256,
    timeout=60,
)
def search_one(spec: dict[str, Any]) -> dict[str, Any]:
    """Run one DDGS text search in one Modal invocation."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("ddgs").setLevel(logging.WARNING)
    logging.getLogger("primp").setLevel(logging.WARNING)

    import contextlib
    import io

    from ddgs import DDGS
    from ddgs.exceptions import DDGSException

    query = spec["query"]
    max_results = spec.get("max_results", 5)
    region = spec.get("region", "us-en")
    safesearch = spec.get("safesearch", "moderate")
    timelimit = spec.get("timelimit") or None
    backend = spec.get("backend", "auto")
    emit_remote_logs = spec.get("emit_remote_logs", True)

    started = time.monotonic()
    if emit_remote_logs:
        emit_log(
            {
                "event": "search_started",
                "query": query,
                "backend": backend,
                "max_results": max_results,
                "region": region,
                "safesearch": safesearch,
                "timelimit": timelimit,
            }
        )

    last_error: str | None = None
    results: list[dict[str, Any]] = []

    for attempt in range(1, 4):
        try:
            if emit_remote_logs:
                emit_log({"event": "search_attempt", "query": query, "attempt": attempt})
            with DDGS(timeout=20) as ddgs:
                sink = io.StringIO()
                with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                    results = list(
                        ddgs.text(
                            query,
                            region=region,
                            safesearch=safesearch,
                            timelimit=timelimit,
                            max_results=max_results,
                            backend=backend,
                        )
                    )
            break
        except DDGSException as exc:
            last_error = str(exc)
            if emit_remote_logs:
                emit_log(
                    {
                        "event": "search_attempt_failed",
                        "query": query,
                        "attempt": attempt,
                        "error": last_error,
                    }
                )
            if attempt < 3:
                time.sleep(0.75 * attempt)
    else:
        payload = {
            "query": query,
            "backend": backend,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "result_count": 0,
            "results": [],
            "error": last_error,
        }
        if emit_remote_logs:
            emit_log({"event": "search_finished", "status": "error", **payload})
        return payload

    payload = {
        "query": query,
        "backend": backend,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "result_count": len(results),
        "results": results,
    }
    if emit_remote_logs:
        emit_log(
            {
                "event": "search_finished",
                "status": "ok",
                "query": query,
                "backend": backend,
                "elapsed_seconds": payload["elapsed_seconds"],
                "result_count": payload["result_count"],
                "top_results": results[:3],
            }
        )
    return payload


@app.function(
    image=image,
    cpu=0.25,
    memory=256,
    timeout=60,
)
def fetch_page(spec: dict[str, Any]) -> dict[str, Any]:
    """Fetch one result URL and extract readable text with stdlib tools."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)

    url = spec["url"]
    max_chars = int(spec.get("max_chars", 4000))
    timeout_seconds = int(spec.get("timeout_seconds", 15))
    started = time.monotonic()

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return {
            "url": url,
            "ok": False,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "error": f"unsupported URL scheme: {parsed.scheme}",
        }

    try:
        req = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; ModalParallelSearch/0.1; "
                    "+https://github.com/krittaprot/modal-parallel-search)"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(req, timeout=timeout_seconds) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read(1_000_000)

        if "html" not in content_type.lower():
            text = raw.decode("utf-8", errors="replace")
            text = re.sub(r"\s+", " ", text).strip()
            title = ""
        else:
            html = raw.decode("utf-8", errors="replace")
            parser = ReadableHTMLExtractor()
            parser.feed(html)
            title = parser.title()
            text = parser.text()

        text = text[:max_chars].strip()
        return {
            "url": url,
            "ok": True,
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "content_type": content_type,
            "title": title,
            "text": text,
            "text_chars": len(text),
            "truncated": len(text) >= max_chars,
        }
    except HTTPError as exc:
        error = f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        error = f"URL error: {exc.reason}"
    except Exception as exc:  # noqa: BLE001 - return agent-readable fetch errors
        error = f"{type(exc).__name__}: {exc}"

    return {
        "url": url,
        "ok": False,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "error": error,
    }


def _clean_queries(raw_queries: list[str]) -> list[str]:
    """Strip empty queries and de-duplicate while preserving order."""
    deduped: list[str] = []
    seen: set[str] = set()

    for query in raw_queries:
        clean = str(query).strip()
        if clean and clean not in seen:
            deduped.append(clean)
            seen.add(clean)

    return deduped


def load_queries(
    *,
    query: str = "",
    queries_json: str = "",
    queries_file: str = "",
) -> list[str]:
    """Load queries from --query, --queries-json, and/or --queries-file.

    Notes:
      - --query accepts a single query or multiple queries joined by ";;":
          modal run modal_search_cli.py --query "your search"
          modal run modal_search_cli.py --query "q1;;q2;;q3"
      - Use --queries-json for many queries at once (recommended for 3+):
          modal run modal_search_cli.py --queries-json '["q1", "q2", "q3"]'
      - Use --queries-file for one query per line.
    """
    queries: list[str] = []

    # --query: split on ;; to support multiple queries in one flag.
    # (Modal's local_entrypoint only supports scalar types, so repeated
    # --query flags don't accumulate — use ;; as an in-band separator.)
    if query:
        parts = [p.strip() for p in query.split(";;")]
        queries.extend([p for p in parts if p])

    if queries_json:
        try:
            loaded = json.loads(queries_json)
        except json.JSONDecodeError as exc:
            raise ValueError(
                '--queries-json must be valid JSON, for example: '
                '\'["first query", "second query"]\''
            ) from exc
        if not isinstance(loaded, list) or not all(isinstance(item, str) for item in loaded):
            raise ValueError("--queries-json must be a JSON array of strings")
        queries.extend(loaded)

    if queries_file:
        path = Path(queries_file).expanduser()
        if not path.exists():
            raise ValueError(f"--queries-file not found: {path}")
        file_queries = [
            line.strip()
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        queries.extend(file_queries)

    deduped = _clean_queries(queries)
    if not deduped:
        raise ValueError(
            'provide at least one query with --query, --queries-json, or --queries-file'
        )

    return deduped


def build_specs(
    queries: list[str],
    max_results: int,
    region: str,
    safesearch: str,
    timelimit: str | None,
    backend: str,
    emit_remote_logs: bool = True,
) -> list[dict[str, Any]]:
    """Build serializable specs for each remote search call."""
    return [
        {
            "query": query,
            "max_results": max_results,
            "region": region,
            "safesearch": safesearch,
            "timelimit": timelimit,
            "backend": backend,
            "emit_remote_logs": emit_remote_logs,
        }
        for query in queries
    ]


def run_parallel_searches(
    queries: list[str],
    max_results: int = 5,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    backend: str = "auto",
    *,
    emit_events: bool = True,
) -> list[dict[str, Any]]:
    """Fan out one Modal FunctionCall per query, then collect in input order."""
    specs = build_specs(
        queries, max_results, region, safesearch, timelimit, backend, emit_events
    )

    calls = []
    for spec in specs:
        call = search_one.spawn(spec)
        calls.append(call)
        if emit_events:
            print(
                json.dumps(
                    {
                        "event": "spawned_search_call",
                        "query": spec["query"],
                        "function_call_id": call.object_id,
                    },
                    sort_keys=True,
                ),
                flush=True,
            )

    return [call.get() for call in calls]


def run_sequential_searches(
    queries: list[str],
    max_results: int = 5,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str | None = None,
    backend: str = "auto",
) -> list[dict[str, Any]]:
    """Run the same searches one after another for benchmark comparisons."""
    specs = build_specs(
        queries, max_results, region, safesearch, timelimit, backend, False
    )
    return [search_one.remote(spec) for spec in specs]


def enrich_with_page_fetches(
    search_results: list[dict[str, Any]],
    *,
    fetch_top_n: int = 3,
    fetch_chars: int = 4000,
    emit_events: bool = True,
) -> list[dict[str, Any]]:
    """Fetch top result pages in parallel and attach extracts under result['page']."""
    calls: list[tuple[int, int, Any]] = []

    for query_idx, query_result in enumerate(search_results):
        for result_idx, result in enumerate(query_result.get("results", [])[:fetch_top_n]):
            url = result.get("href") or result.get("url")
            if not url:
                continue
            call = fetch_page.spawn({"url": url, "max_chars": fetch_chars})
            calls.append((query_idx, result_idx, call))
            if emit_events:
                print(
                    json.dumps(
                        {
                            "event": "spawned_page_fetch_call",
                            "url": url,
                            "function_call_id": call.object_id,
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )

    for query_idx, result_idx, call in calls:
        page = call.get()
        search_results[query_idx]["results"][result_idx]["page"] = page

    return search_results


def run_benchmark(
    queries: list[str],
    max_results: int,
    region: str,
    safesearch: str,
    timelimit: str | None,
    backend: str,
) -> dict[str, Any]:
    """Compare sequential and parallel search wall time for the same query set."""
    sequential_started = time.monotonic()
    sequential_results = run_sequential_searches(
        queries=queries,
        max_results=max_results,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        backend=backend,
    )
    sequential_wall = time.monotonic() - sequential_started

    parallel_started = time.monotonic()
    parallel_results = run_parallel_searches(
        queries=queries,
        max_results=max_results,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit,
        backend=backend,
        emit_events=False,
    )
    parallel_wall = time.monotonic() - parallel_started

    speedup = sequential_wall / parallel_wall if parallel_wall > 0 else None
    return {
        "query_count": len(queries),
        "max_results": max_results,
        "sequential_wall_seconds": round(sequential_wall, 3),
        "parallel_wall_seconds": round(parallel_wall, 3),
        "speedup": round(speedup, 2) if speedup is not None else None,
        "sequential_result_counts": [r.get("result_count", 0) for r in sequential_results],
        "parallel_result_counts": [r.get("result_count", 0) for r in parallel_results],
        "parallel_results": parallel_results,
    }


def _md_escape(text: Any) -> str:
    return str(text or "").replace("\r", "").strip()


def format_markdown(payload: dict[str, Any]) -> str:
    """Render final payload as human-readable research notes."""
    lines: list[str] = []
    lines.append("# Search research notes")
    lines.append("")
    lines.append(
        f"- Queries: {payload.get('query_count', 0)}"
        f"\n- Wall time: {payload.get('wall_seconds', 0)}s"
    )
    if payload.get("benchmark"):
        bench = payload["benchmark"]
        lines.append(
            "- Benchmark: "
            f"sequential {bench.get('sequential_wall_seconds')}s vs "
            f"parallel {bench.get('parallel_wall_seconds')}s "
            f"({bench.get('speedup')}x speedup)"
        )
    lines.append("")

    for query_idx, query_result in enumerate(payload.get("results", []), start=1):
        lines.append(f"## {query_idx}. {_md_escape(query_result.get('query'))}")
        lines.append("")
        if query_result.get("error"):
            lines.append(f"Error: `{_md_escape(query_result['error'])}`")
            lines.append("")
            continue

        lines.append(
            f"Found {query_result.get('result_count', 0)} results "
            f"in {query_result.get('elapsed_seconds', 0)}s."
        )
        lines.append("")

        for result_idx, result in enumerate(query_result.get("results", []), start=1):
            title = _md_escape(result.get("title") or "Untitled")
            href = _md_escape(result.get("href") or result.get("url") or "")
            body = _md_escape(result.get("body") or "")
            lines.append(f"### {query_idx}.{result_idx}. {title}")
            if href:
                lines.append(f"Source: {href}")
            if body:
                lines.append("")
                lines.append(body)

            page = result.get("page")
            if page:
                lines.append("")
                if page.get("ok"):
                    page_title = _md_escape(page.get("title"))
                    if page_title and page_title != title:
                        lines.append(f"Fetched page title: {page_title}")
                        lines.append("")
                    extract = _md_escape(page.get("text"))
                    if extract:
                        lines.append("Extract:")
                        lines.append("")
                        lines.append(extract)
                else:
                    lines.append(f"Fetch failed: `{_md_escape(page.get('error'))}`")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


@app.local_entrypoint()
def main(
    query: str = "",
    queries_json: str = "",
    queries_file: str = "",
    max_results: int = 5,
    region: str = "us-en",
    safesearch: str = "moderate",
    timelimit: str = "",
    backend: str = "auto",
    fetch_pages: bool = False,
    fetch_top_n: int = 3,
    fetch_chars: int = 4000,
    output_format: str = "markdown",
    benchmark: bool = False,
    show_events: bool = False,
) -> None:
    """Modal local entrypoint — use --help for full usage guide."""
    if safesearch not in {"on", "moderate", "off"}:
        _user_error("--safesearch must be one of: on, moderate, off")

    if timelimit and timelimit not in {"d", "w", "m", "y"}:
        _user_error("--timelimit must be one of: d, w, m, y")

    if backend not in {"auto", "yahoo", "brave", "duckduckgo"}:
        _user_error("--backend must be one of: auto, yahoo, brave, duckduckgo")

    if max_results < 1:
        _user_error("--max-results must be at least 1")

    if fetch_top_n < 1:
        _user_error("--fetch-top-n must be at least 1")

    if fetch_chars < 200:
        _user_error("--fetch-chars must be at least 200")

    if output_format not in {"json", "markdown"}:
        _user_error("--output-format must be one of: json, markdown")

    try:
        queries = load_queries(
            query=query,
            queries_json=queries_json,
            queries_file=queries_file,
        )
    except (OSError, ValueError) as exc:
        _user_error(str(exc))

    emit_events = show_events
    started = time.monotonic()
    if emit_events:
        print(
            json.dumps(
                {
                    "event": "modal_search_started",
                    "query_count": len(queries),
                    "max_results": max_results,
                    "backend": backend,
                    "region": region,
                    "safesearch": safesearch,
                    "timelimit": timelimit or None,
                    "fetch_pages": fetch_pages,
                    "fetch_top_n": fetch_top_n if fetch_pages else None,
                    "output_format": output_format,
                    "benchmark": benchmark,
                },
                indent=2,
            ),
            flush=True,
        )

    benchmark_payload: dict[str, Any] | None = None
    if benchmark:
        benchmark_payload = run_benchmark(
            queries=queries,
            max_results=max_results,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit or None,
            backend=backend,
        )
        results = benchmark_payload.pop("parallel_results")
    else:
        results = run_parallel_searches(
            queries=queries,
            max_results=max_results,
            region=region,
            safesearch=safesearch,
            timelimit=timelimit or None,
            backend=backend,
            emit_events=emit_events,
        )

    if fetch_pages:
        results = enrich_with_page_fetches(
            results,
            fetch_top_n=fetch_top_n,
            fetch_chars=fetch_chars,
            emit_events=emit_events,
        )

    payload: dict[str, Any] = {
        "query_count": len(queries),
        "wall_seconds": round(time.monotonic() - started, 3),
        "results": results,
    }

    if benchmark_payload:
        payload["benchmark"] = benchmark_payload

    if output_format == "markdown":
        print(format_markdown(payload))
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
