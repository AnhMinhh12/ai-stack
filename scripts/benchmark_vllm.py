#!/usr/bin/env python3
"""Fail-closed vLLM capacity harness.

The harness is intentionally dry-run by default. A real GPU load test requires
BENCHMARK_APPROVED=YES and --execute because it can affect latency, memory and
service availability.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MODEL_PATH = "Qwen/Qwen2.5-14B-Instruct"
SERVED_MODEL_NAME = "qwen2.5-14b"
DEFAULT_INPUT_LENS = (4096, 8192, 16384)
DEFAULT_CONCURRENCIES = (8, 16, 32, 64)
DEFAULT_RATES = (1, 4, 8, 16)
PERCENTILES = (50, 95, 99)


def percentile(values: list[float], p: int) -> float:
    """Nearest-rank percentile, deterministic and fail-closed for empty input."""
    if not values:
        raise ValueError(f"cannot calculate p{p} from an empty sample")
    ordered = sorted(values)
    rank = max(1, math.ceil((p / 100) * len(ordered)))
    return ordered[rank - 1]


def _first_number(data: dict[str, Any], names: tuple[str, ...]) -> float | None:
    for name in names:
        value = data.get(name)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _series(result: dict[str, Any], metric: str) -> list[float]:
    candidates = (
        result.get("request_level_metrics"),
        result.get("per_request_metrics"),
        result.get("requests"),
    )
    values: list[float] = []
    for candidate in candidates:
        if not isinstance(candidate, list):
            continue
        for row in candidate:
            if isinstance(row, dict):
                value = row.get(metric)
                if isinstance(value, (int, float)):
                    values.append(float(value))
    return values


def metric_percentiles(result: dict[str, Any], metric: str) -> dict[str, float]:
    values = _series(result, metric)
    if values:
        return {f"p{p}": percentile(values, p) for p in PERCENTILES}

    # vLLM result JSON exposes summary percentile fields when detailed samples
    # are not retained. Missing p50/p95/p99 is an error, never a zero/default.
    aliases = {
        50: (f"median_{metric}_ms", f"p50_{metric}_ms", f"p50_{metric}"),
        95: (f"p95_{metric}_ms", f"p95_{metric}"),
        99: (f"p99_{metric}_ms", f"p99_{metric}"),
    }
    parsed: dict[str, float] = {}
    for p, names in aliases.items():
        value = _first_number(result, names)
        if value is None:
            raise ValueError(f"missing p{p} metric for {metric}")
        parsed[f"p{p}"] = value
    return parsed


def parse_result(result: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    completed = _first_number(result, ("completed", "successful_requests", "num_completed"))
    failed = _first_number(result, ("failed", "failed_requests", "num_failures"))
    if completed is None or failed is None:
        raise ValueError("missing completed/failed request counts")
    total = completed + failed
    if total <= 0:
        raise ValueError("benchmark produced zero requests")

    request_throughput = _first_number(result, ("request_throughput", "request_throughput_req_per_s"))
    output_throughput = _first_number(result, ("output_throughput", "output_token_throughput"))
    total_throughput = _first_number(result, ("total_token_throughput", "total_throughput"))
    if any(value is None for value in (request_throughput, output_throughput, total_throughput)):
        raise ValueError("missing throughput metric")

    metrics = {
        **context,
        "completed": int(completed),
        "failed": int(failed),
        "success_rate_pct": completed / total * 100.0,
        "error_rate_pct": failed / total * 100.0,
        "request_throughput": request_throughput,
        "output_token_throughput": output_throughput,
        "total_token_throughput": total_throughput,
        "ttft_ms": metric_percentiles(result, "ttft"),
        "itl_ms": metric_percentiles(result, "itl"),
        "e2el_ms": metric_percentiles(result, "e2el"),
    }
    metrics["slo"] = {
        "ttft_p95_lt_1500ms": metrics["ttft_ms"]["p95"] < 1500.0,
        "itl_p95_lt_50ms": metrics["itl_ms"]["p95"] < 50.0,
        "success_gte_99pct": metrics["success_rate_pct"] >= 99.0,
    }
    metrics["slo_pass"] = all(metrics["slo"].values())
    return metrics


def build_command(input_len: int, concurrency: int, rate: int, result_name: str) -> list[str]:
    args = [
        "--backend", "openai-chat",
        "--model", MODEL_PATH,
        "--served-model-name", SERVED_MODEL_NAME,
        "--endpoint", "/v1/chat/completions",
        "--dataset-name", "random",
        "--random-input-len", str(input_len),
        "--random-output-len", "256",
        "--num-prompts", "64",
        "--request-rate", str(rate),
        "--max-concurrency", str(concurrency),
        "--percentile-metrics", "ttft,itl,e2el",
        "--metric-percentiles", "50,95,99",
        "--save-result", "--save-detailed",
        "--result-dir", "/tmp/vllm-bench",
        "--result-filename", result_name,
        "--metadata", f"input_len={input_len}", f"concurrency={concurrency}", f"rate={rate}",
        "--ready-check-timeout-sec", "30",
        "--seed", "20260909",
    ]
    # Keep the secret out of argv and logs: vllm container already has VLLM_API_KEY.
    shell = 'export OPENAI_API_KEY="$VLLM_API_KEY"; exec vllm bench serve "$@"'
    return ["docker", "exec", "vllm-engine", "sh", "-lc", shell, "--", *args]


def run_case(case: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    result_name = f"case_i{case['input_len']}_c{case['concurrency']}_r{case['rate']}.json"
    cmd = build_command(case["input_len"], case["concurrency"], case["rate"], result_name)
    subprocess.run(["docker", "exec", "vllm-engine", "mkdir", "-p", "/tmp/vllm-bench"], check=True)
    subprocess.run(cmd, check=True)
    destination = output_dir / result_name
    subprocess.run(["docker", "cp", f"vllm-engine:/tmp/vllm-bench/{result_name}", str(destination)], check=True)
    result = json.loads(destination.read_text())
    return parse_result(result, case)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="run GPU load; requires BENCHMARK_APPROVED=YES")
    parser.add_argument("--output-dir", type=Path, default=Path("docs/evidence/CAP-20260909"))
    parser.add_argument("--input-lens", default=','.join(map(str, DEFAULT_INPUT_LENS)))
    parser.add_argument("--concurrencies", default=','.join(map(str, DEFAULT_CONCURRENCIES)))
    parser.add_argument("--rates", default=','.join(map(str, DEFAULT_RATES)))
    args = parser.parse_args()

    input_lens = [int(x) for x in args.input_lens.split(',') if x]
    concurrencies = [int(x) for x in args.concurrencies.split(',') if x]
    rates = [int(x) for x in args.rates.split(',') if x]
    if not input_lens or not concurrencies or not rates:
        raise SystemExit("input-lens, concurrencies and rates must be non-empty")

    cases = [
        {"input_len": i, "concurrency": c, "rate": r}
        for i in input_lens for c in concurrencies for r in rates
    ]
    if not args.execute:
        print("DRY RUN: no GPU load was generated")
        print(f"cases={len(cases)} input_lens={input_lens} concurrencies={concurrencies} rates={rates}")
        print("Set BENCHMARK_APPROVED=YES and pass --execute only in an approved window.")
        return 0
    if os.environ.get("BENCHMARK_APPROVED") != "YES":
        raise SystemExit("refusing GPU load: BENCHMARK_APPROVED=YES is required")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    for case in cases:
        results.append(run_case(case, args.output_dir))

    report = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_PATH,
        "served_model": SERVED_MODEL_NAME,
        "workload": {"input_lens": input_lens, "output_len": 256, "concurrencies": concurrencies, "rates": rates, "num_prompts": 64, "seed": 20260909},
        "percentiles": list(PERCENTILES),
        "results": results,
        "capacity_gate_pass": bool(results) and all(row["slo_pass"] for row in results),
    }
    report_path = args.output_dir / "capacity-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"report={report_path}")
    print(f"capacity_gate_pass={report['capacity_gate_pass']}")
    if not report["capacity_gate_pass"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
