#!/usr/bin/env python3
"""Self-contained Modal parallel web-search CLI for coding agents.

Run examples:

  modal run modal_search_cli.py --query "your search"

  modal run modal_search_cli.py --query "q1;;q2;;q3"

  modal run modal_search_cli.py --queries-json '["query one", "query two"]'

  modal run modal_search_cli.py --queries-file queries.txt
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import modal

# ---------------------------------------------------------------------------
# Custom help — Modal's local_entrypoint click wrapper doesn't expose per-option
# help text, so we intercept --help and print our own usage guide.
# ---------------------------------------------------------------------------

_USAGE = """\
Modal Parallel Search — lightweight web search fanned out across Modal.

USAGE:
  modal run scripts/modal_search_cli.py [OPTIONS]

QUERY INPUT (pick one or combine):
  --query          One query, or multiple joined by ";;".
                   modal run modal_search_cli.py --query "your query"
                   modal run modal_search_cli.py --query "q1;;q2;;q3"

  --queries-json   JSON array of query strings (recommended for 3+ queries).
                   modal run modal_search_cli.py --queries-json '["q1","q2"]'

  --queries-file   File with one query per line (# comments and blanks OK).

SEARCH OPTIONS:
  --max-results    Results per query.           [default: 5]
  --backend        Search engine backend.       [default: auto]
                   Choices: auto, yahoo, brave, duckduckgo
  --region         Search region (DDGS locale). [default: us-en]
  --safesearch     Safe-search level.           [default: moderate]
                   Choices: on, moderate, off
  --timelimit      Time filter.                 [default: none]
                   Choices: d (day), w (week), m (month), y (year)

NOTES:
  • Each query spawns a separate Modal container — all run in parallel.
  • "auto" backend tries multiple engines; retries up to 3x on failure.
  • Repeated --query flags do NOT accumulate (Modal limitation).
    Use ;; separator or --queries-json for multi-query.

EXAMPLES:
  # Single quick search
  modal run scripts/modal_search_cli.py --query "Modal Python serverless"

  # 5 parallel queries, last-week results
  modal run scripts/modal_search_cli.py \\
    --queries-json '["AI chips","OpenAI news","AI regulation"]' \\
    --timelimit w --max-results 5

  # Same with ;; separator
  modal run scripts/modal_search_cli.py \\
    --query "AI chips;;OpenAI news;;AI regulation" \\
    --timelimit w
"""


def _print_help_and_exit() -> None:
    print(_USAGE)
    sys.exit(0)


# Modal's click parser grabs --help before main() runs, so we intercept at
# module import time — before the @app.local_entrypoint decorator is invoked.
if "--help" in sys.argv or "-h" in sys.argv:
    _print_help_and_exit()


app = modal.App(name="modal-parallel-search")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .uv_pip_install("ddgs==9.14.4")
)


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

    started = time.monotonic()
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
            emit_log(
                {
                    "event": "search_attempt",
                    "query": query,
                    "attempt": attempt,
                }
            )
            with DDGS(timeout=20) as ddgs:
                with contextlib.redirect_stdout(io.StringIO()):
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
        emit_log({"event": "search_finished", "status": "error", **payload})
        return payload

    payload = {
        "query": query,
        "backend": backend,
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "result_count": len(results),
        "results": results,
    }
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
        loaded = json.loads(queries_json)
        if not isinstance(loaded, list) or not all(isinstance(item, str) for item in loaded):
            raise ValueError("--queries-json must be a JSON array of strings")
        queries.extend(loaded)

    if queries_file:
        path = Path(queries_file).expanduser()
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
) -> list[dict[str, Any]]:
    """Fan out one Modal FunctionCall per query, then collect in input order."""
    specs = build_specs(queries, max_results, region, safesearch, timelimit, backend)

    calls = []
    for spec in specs:
        call = search_one.spawn(spec)
        calls.append(call)
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
) -> None:
    """Modal local entrypoint — use --help for full usage guide."""
    if safesearch not in {"on", "moderate", "off"}:
        raise ValueError("--safesearch must be one of: on, moderate, off")

    if timelimit and timelimit not in {"d", "w", "m", "y"}:
        raise ValueError("--timelimit must be one of: d, w, m, y")

    if max_results < 1:
        raise ValueError("--max-results must be at least 1")

    queries = load_queries(
        query=query,
        queries_json=queries_json,
        queries_file=queries_file,
    )

    started = time.monotonic()
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
            },
            indent=2,
        ),
        flush=True,
    )

    results = run_parallel_searches(
        queries=queries,
        max_results=max_results,
        region=region,
        safesearch=safesearch,
        timelimit=timelimit or None,
        backend=backend,
    )

    print(
        json.dumps(
            {
                "query_count": len(queries),
                "wall_seconds": round(time.monotonic() - started, 3),
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
