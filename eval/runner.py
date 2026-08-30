"""
RAG evaluation runner.

Runs a set of test questions against the assistant and scores:
  - Keyword coverage in the generated answer
  - Whether the expected source document was cited
  - Whether refusal-style questions are handled safely
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from assistant.agent import EnterpriseKnowledgeAssistant

DEFAULT_TEST_FILE = Path(__file__).resolve().parent / "test_cases.json"
DEFAULT_RESULTS_DIR = Path(__file__).resolve().parent / "results"
KEYWORD_PASS_THRESHOLD = 0.6


@dataclass
class TestCase:
    id: str
    question: str
    expected_keywords: list[str] = field(default_factory=list)
    expected_source_contains: str | None = None
    must_refuse: bool = False
    refusal_phrases: list[str] = field(default_factory=list)


@dataclass
class TestResult:
    id: str
    question: str
    passed: bool
    keyword_score: float
    source_hit: bool
    refused_correctly: bool | None
    answer_preview: str
    cited_sources: list[str]
    latency_seconds: float
    failure_reason: str | None = None


@dataclass
class EvaluationReport:
    total: int
    passed: int
    failed: int
    pass_rate: float
    avg_keyword_score: float
    avg_latency_seconds: float
    provider_info: dict[str, str]
    results: list[TestResult]

    def format_summary(self) -> str:
        lines = [
            "",
            "=== Evaluation Report ===",
            f"  Passed:          {self.passed}/{self.total} ({self.pass_rate:.0%})",
            f"  Avg keyword hit: {self.avg_keyword_score:.0%}",
            f"  Avg latency:     {self.avg_latency_seconds:.1f}s",
            f"  LLM:             {self.provider_info.get('llm_provider')} / {self.provider_info.get('llm_model')}",
            f"  Embeddings:      {self.provider_info.get('embedding_provider')} / {self.provider_info.get('embedding_model')}",
            "",
            "Results:",
        ]
        for result in self.results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"  [{status}] {result.id}")
            if not result.passed and result.failure_reason:
                lines.append(f"         {result.failure_reason}")
        return "\n".join(lines)


def load_test_cases(path: Path | None = None) -> list[TestCase]:
    test_file = path or DEFAULT_TEST_FILE
    raw = json.loads(test_file.read_text(encoding="utf-8"))
    return [TestCase(**item) for item in raw]


def _keyword_score(answer: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(1 for keyword in keywords if keyword.lower() in answer_lower)
    return hits / len(keywords)


def _source_hit(citations: list, expected_source: str | None) -> bool:
    if not expected_source:
        return True
    return any(expected_source in cite.source for cite in citations)


def _refused_correctly(answer: str, refusal_phrases: list[str]) -> bool:
    answer_lower = answer.lower()
    phrases = refusal_phrases or [
        "don't have",
        "do not have",
        "not contain",
        "not in",
        "no information",
        "insufficient",
        "cannot find",
        "can't find",
        "unable to find",
    ]
    return any(phrase in answer_lower for phrase in phrases)


def _evaluate_case(
    assistant: EnterpriseKnowledgeAssistant, case: TestCase
) -> TestResult:
    start = time.perf_counter()
    response = assistant.ask(case.question)
    latency = time.perf_counter() - start

    keyword_score = _keyword_score(response.answer, case.expected_keywords)
    source_hit = _source_hit(response.citations, case.expected_source_contains)
    cited_sources = [cite.source for cite in response.citations]

    if case.must_refuse:
        refused = _refused_correctly(response.answer, case.refusal_phrases)
        passed = refused
        failure_reason = None if passed else "Expected a refusal, but answer looked confident"
        return TestResult(
            id=case.id,
            question=case.question,
            passed=passed,
            keyword_score=keyword_score,
            source_hit=source_hit,
            refused_correctly=refused,
            answer_preview=response.answer[:160].replace("\n", " "),
            cited_sources=cited_sources,
            latency_seconds=round(latency, 2),
            failure_reason=failure_reason,
        )

    keyword_ok = keyword_score >= KEYWORD_PASS_THRESHOLD
    passed = keyword_ok and source_hit
    failure_reason = None
    if not keyword_ok:
        failure_reason = (
            f"Keyword score {keyword_score:.0%} below {KEYWORD_PASS_THRESHOLD:.0%}"
        )
    elif not source_hit:
        failure_reason = f"Expected source containing '{case.expected_source_contains}'"

    return TestResult(
        id=case.id,
        question=case.question,
        passed=passed,
        keyword_score=round(keyword_score, 2),
        source_hit=source_hit,
        refused_correctly=None,
        answer_preview=response.answer[:160].replace("\n", " "),
        cited_sources=cited_sources,
        latency_seconds=round(latency, 2),
        failure_reason=failure_reason,
    )


def run_evaluation(
    test_file: Path | None = None,
    verbose: bool = False,
    save_report: bool = True,
) -> EvaluationReport:
    """Run all test cases and return an evaluation report."""
    cases = load_test_cases(test_file)
    assistant = EnterpriseKnowledgeAssistant()

    index_result = assistant.index()
    if index_result.get("status") == "empty":
        raise RuntimeError(str(index_result.get("message")))

    results: list[TestResult] = []
    for case in cases:
        result = _evaluate_case(assistant, case)
        results.append(result)
        if verbose:
            status = "PASS" if result.passed else "FAIL"
            print(f"\n[{status}] {case.id}")
            print(f"  Q: {case.question}")
            print(f"  A: {result.answer_preview}")
            print(f"  Keyword score: {result.keyword_score:.0%}")
            print(f"  Source hit:    {result.source_hit}")
            if result.failure_reason:
                print(f"  Reason:        {result.failure_reason}")

    passed = sum(1 for result in results if result.passed)
    total = len(results)
    report = EvaluationReport(
        total=total,
        passed=passed,
        failed=total - passed,
        pass_rate=passed / total if total else 0.0,
        avg_keyword_score=sum(r.keyword_score for r in results) / total if total else 0.0,
        avg_latency_seconds=sum(r.latency_seconds for r in results) / total if total else 0.0,
        provider_info=assistant.provider_info,
        results=results,
    )

    if save_report:
        _save_report(report)

    return report


def _save_report(report: EvaluationReport) -> Path:
    DEFAULT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = DEFAULT_RESULTS_DIR / f"eval_{timestamp}.json"

    payload = {
        "summary": {
            "total": report.total,
            "passed": report.passed,
            "failed": report.failed,
            "pass_rate": report.pass_rate,
            "avg_keyword_score": report.avg_keyword_score,
            "avg_latency_seconds": report.avg_latency_seconds,
            "provider_info": report.provider_info,
        },
        "results": [asdict(result) for result in report.results],
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    latest_path = DEFAULT_RESULTS_DIR / "latest.json"
    latest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path
