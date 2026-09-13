"""Parsing the per-stage block a replay summary carries.

The block exists in two forms: the constructed summary ``handleSummary`` prints
(``stages``/``ramp`` keys) and the raw end-of-test data object k6's
``--summary-export`` writes (stage Trends under ``metrics``). Both must read
back the same numbers, and a summary without stages must say so as None, not
as an error.
"""

from __future__ import annotations

from analysis.k6_stages import parse_stage_block, ramp_stage_indices, ramp_window_sec


def _raw_data() -> dict:
    return {
        "state": {"testRunDurationMs": 1200000},
        "metrics": {
            "stage_00_latency_ms": {"values": {"med": 10.0, "p(95)": 20.0, "p(99)": 30.0}},
            "stage_00_requests": {"values": {"count": 5}},
            "stage_01_latency_ms": {"values": {"med": 11.0, "p(95)": 21.0, "p(99)": 31.0}},
            "stage_01_requests": {"values": {"count": 6}},
            "ramp_latency_ms": {"values": {"med": 10.5, "p(95)": 20.5, "p(99)": 30.5}},
            "ramp_requests": {"values": {"count": 11}},
            "http_req_duration": {"values": {"med": 10.2, "p(99)": 30.2}},
        },
    }


class TestParseStageBlock:
    def test_raw_data_object_yields_stage_percentiles_and_counts(self):
        block = parse_stage_block(_raw_data())

        assert block is not None
        assert block["stages"]["stage_00"] == {
            "count": 5,
            "p50_ms": 10.0,
            "p95_ms": 20.0,
            "p99_ms": 30.0,
        }
        assert block["stages"]["stage_01"]["p99_ms"] == 31.0
        assert block["ramp"]["p99_ms"] == 30.5
        assert block["ramp"]["count"] == 11

    def test_constructed_summary_passes_through(self):
        constructed = {
            "stages": {"stage_00": {"count": 1, "p50_ms": 2.0, "p95_ms": 3.0, "p99_ms": 4.0}},
            "ramp": {"stages": ["stage_00"], "window_sec": [0.0, 30.0], "p99_ms": 4.0},
        }

        assert parse_stage_block(constructed) == constructed

    def test_a_summary_without_stages_is_none_not_an_error(self):
        assert parse_stage_block({"metrics": {"http_req_duration": {"values": {}}}}) is None
        assert parse_stage_block({}) is None
        assert parse_stage_block(None) is None


class TestRampRule:
    CLARKNET_TARGETS = [
        44,
        58,
        29,
        22,
        60,
        37,
        60,
        62,
        77,
        101,
        131,
        77,
        70,
        48,
        139,
        86,
        73,
        142,
        164,
        116,
        121,
        119,
        79,
        67,
        92,
        47,
        46,
        40,
        73,
        69,
        73,
        113,
        78,
        44,
        43,
        59,
        37,
        40,
        43,
        54,
    ]

    def test_canonical_trace_ramp_is_stages_5_through_18(self):
        assert ramp_stage_indices(self.CLARKNET_TARGETS) == (5, 18)

    def test_window_covers_150_to_570_seconds_of_30s_buckets(self):
        stages = [{"duration": "30s", "target": t} for t in self.CLARKNET_TARGETS]

        assert ramp_window_sec(stages) == (150.0, 570.0)

    def test_a_flat_trace_has_no_ramp(self):
        assert ramp_stage_indices([50, 50, 50]) is None
        assert ramp_window_sec([{"duration": "30s", "target": 50}] * 3) is None
