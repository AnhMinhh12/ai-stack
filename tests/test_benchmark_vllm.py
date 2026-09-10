import importlib.util
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "benchmark_vllm.py"
spec = importlib.util.spec_from_file_location("benchmark_vllm", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def base_result():
    return {
        "completed": 99, "failed": 1,
        "request_throughput": 4.0, "output_throughput": 100.0,
        "total_token_throughput": 500.0,
        "median_ttft_ms": 100.0, "p95_ttft_ms": 1200.0, "p99_ttft_ms": 1400.0,
        "median_itl_ms": 10.0, "p95_itl_ms": 40.0, "p99_itl_ms": 45.0,
        "median_e2el_ms": 300.0, "p95_e2el_ms": 800.0, "p99_e2el_ms": 900.0,
    }


class BenchmarkParserTests(unittest.TestCase):
    def test_summary_percentiles_and_slo(self):
        parsed = module.parse_result(base_result(), {"input_len": 4096, "concurrency": 8, "rate": 1})
        self.assertEqual(parsed["ttft_ms"]["p95"], 1200.0)
        self.assertEqual(parsed["itl_ms"]["p95"], 40.0)
        self.assertEqual(parsed["success_rate_pct"], 99.0)
        self.assertTrue(parsed["slo_pass"])

    def test_request_level_nearest_rank_percentiles(self):
        result = base_result()
        result["request_level_metrics"] = [
            {"ttft": 1.0, "itl": 10.0, "e2el": 100.0},
            {"ttft": 2.0, "itl": 20.0, "e2el": 200.0},
            {"ttft": 3.0, "itl": 30.0, "e2el": 300.0},
            {"ttft": 4.0, "itl": 40.0, "e2el": 400.0},
        ]
        parsed = module.parse_result(result, {"input_len": 4096, "concurrency": 8, "rate": 1})
        self.assertEqual(parsed["ttft_ms"], {"p50": 2.0, "p95": 4.0, "p99": 4.0})

    def test_missing_percentile_fails_closed(self):
        result = base_result()
        del result["p95_ttft_ms"]
        with self.assertRaisesRegex(ValueError, "p95"):
            module.parse_result(result, {"input_len": 4096, "concurrency": 8, "rate": 1})


if __name__ == "__main__":
    unittest.main()
