"""The machine half of a command's output: one line of JSON, and truncation that names itself."""

from __future__ import annotations

import json
from pathlib import Path

from shared.output import json_line, print_next, truncate


class TestJsonLine:
    def test_parses_back_to_the_payload_on_one_line(self):
        payload = {"scenario": "s3-hybrid-reactive", "runs": [{"run": 1, "p99_ms": 215.0}]}

        line = json_line(payload)

        assert "\n" not in line
        assert json.loads(line) == payload

    def test_is_smaller_than_the_indented_form(self):
        """This is the whole reason the module exists: indentation costs real tokens."""
        payload = [{"scenario": "s3-hybrid-reactive", "run_id": i, "p99_ms": 100.0 + i} for i in range(50)]

        assert len(json_line(payload)) < len(json.dumps(payload, indent=2))

    def test_a_value_json_cannot_encode_is_written_not_raised(self):
        """Paths appear in payloads (`bundle`, `summary_path`); they must not crash a CLI."""
        assert "/tmp/example" in json_line({"path": Path("/tmp/example")})


class TestTruncate:
    def test_a_short_value_is_untouched(self):
        assert truncate("short") == "short"

    def test_a_long_value_names_its_length_and_the_way_out(self):
        text = "x" * 500

        cut = truncate(text, limit=100)

        assert cut.startswith("x" * 100)
        assert "500 chars" in cut
        assert "--full" in cut
        assert len(cut) < len(text)

    def test_full_returns_the_whole_value(self):
        text = "y" * 500

        assert truncate(text, limit=100, full=True) == text


class TestPrintNext:
    def test_each_step_prints_on_its_own_line(self, capsys):
        print_next(["thesis analysis mechanism results/experiments/phase-b/bundle"])

        out = capsys.readouterr().out
        assert out.strip() == "next: thesis analysis mechanism results/experiments/phase-b/bundle"

    def test_several_steps_stay_a_command_list(self, capsys):
        print_next(["thesis analysis variance b", "thesis experiment analyze b"])

        assert capsys.readouterr().out.splitlines() == [
            "next: thesis analysis variance b",
            "next: thesis experiment analyze b",
        ]
