"""
Structured observability for RAG requests.

Every ask/index operation produces a JSON trace log with:
  - trace_id (for correlating logs)
  - latency breakdown (retrieval vs generation)
  - retrieved chunks and sources
  - model provider info
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
TRACE_FILE = LOG_DIR / "traces.jsonl"

logger = logging.getLogger("eka.tracer")


@dataclass
class ChunkTrace:
    source: str
    score: float | None
    excerpt: str


@dataclass
class RequestTrace:
    trace_id: str
    operation: str  # "ask" | "index"
    question: str | None = None
    answer_preview: str | None = None
    retrieval_ms: float | None = None
    generation_ms: float | None = None
    total_ms: float | None = None
    chunks_retrieved: int = 0
    chunks: list[ChunkTrace] = field(default_factory=list)
    cited_sources: list[str] = field(default_factory=list)
    provider_info: dict[str, str] = field(default_factory=dict)
    status: str = "ok"
    error: str | None = None
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Timer:
    """Simple context manager for millisecond timing."""

    def __init__(self):
        self.start = time.perf_counter()
        self.elapsed_ms: float = 0.0

    def stop(self) -> float:
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000
        return self.elapsed_ms


def new_trace_id() -> str:
    return str(uuid.uuid4())[:8]


def setup_logging(log_level: str = "INFO") -> None:
    """Configure console + file logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_DIR / "app.log")
    file_handler.setFormatter(formatter)

    root = logging.getLogger("eka")
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(console)
        root.addHandler(file_handler)


def log_trace(trace: RequestTrace) -> None:
    """Write a structured JSON trace to traces.jsonl and log a summary."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    with TRACE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(trace.to_dict(), default=str) + "\n")

    if trace.operation == "ask":
        logger.info(
            "trace=%s op=ask retrieval=%.0fms generation=%.0fms total=%.0fms "
            "chunks=%d sources=%s",
            trace.trace_id,
            trace.retrieval_ms or 0,
            trace.generation_ms or 0,
            trace.total_ms or 0,
            trace.chunks_retrieved,
            trace.cited_sources,
        )
    else:
        logger.info(
            "trace=%s op=%s status=%s total=%.0fms",
            trace.trace_id,
            trace.operation,
            trace.status,
            trace.total_ms or 0,
        )
