"""The series rules: parse a stage, retry a failure, stop the chain when it repeats.

The chain used to be a shell script, so its rules — retry once, stop rather than run
later stages against a broken stack, keep the indexer out of the measurement window —
were untested and lived in one operator's head. They are tested here with a fake
runner, which is also why the runner is a parameter.
"""

from pathlib import Path

import pytest
from experiment.series import StageSpec, parse_stage, run_series, summarise


class FakeRunner:
    """Records the commands it was asked to run and answers with a scripted result."""

    def __init__(self, results: dict[str, list[int]] | None = None):
        self.calls: list[list[str]] = []
        self.results = results or {}

    def __call__(self, command, log_path: Path) -> int:
        self.calls.append(list(command))
        profile = command[command.index("--profile") + 1]
        scripted = self.results.get(profile, [0])
        same_profile = [c for c in self.calls if c[c.index("--profile") + 1] == profile]
        return scripted[min(len(same_profile) - 1, len(scripted) - 1)]


class FakeIndexer:
    def __init__(self):
        self.actions: list[str] = []

    def __call__(self, action: str) -> bool:
        self.actions.append(action)
        return True


class TestParsing:
    def test_a_bare_profile(self):
        spec = parse_stage("h2-pair")

        assert spec == StageSpec(profile="h2-pair", overrides={})
        assert spec.command() == ["uv", "run", "thesis", "experiment", "reproduce", "--profile", "h2-pair"]

    def test_overrides_become_flags(self):
        spec = parse_stage("baselines:runs=5,output=results/x")

        assert spec.overrides == {"runs": "5", "output": "results/x"}
        assert spec.command()[-4:] == ["--runs", "5", "--output", "results/x"]

    @pytest.mark.parametrize("spec", ["", ":pairs=1", "h2-pair:pairs", "h2-pair:pairs=", "h2-pair:nope=1"])
    def test_a_bad_stage_is_rejected(self, spec):
        with pytest.raises(ValueError):
            parse_stage(spec)

    def test_the_description_carries_the_overrides(self):
        assert parse_stage("h2-pair:pairs=1").describe() == "h2-pair (pairs=1)"


class TestRunSeries:
    def test_stages_run_in_order(self, tmp_path):
        runner = FakeRunner()
        indexer = FakeIndexer()

        outcomes = run_series(
            [parse_stage("a"), parse_stage("b")],
            log_path=tmp_path / "s.log",
            runner=runner,
            indexer=indexer,
            sleep=lambda _: None,
        )

        profiles = [call[call.index("--profile") + 1] for call in runner.calls]
        assert profiles == ["a", "b"]
        assert all(outcome.ok for outcome in outcomes)

    def test_a_failure_is_retried_once(self, tmp_path):
        runner = FakeRunner({"a": [1, 0]})

        outcomes = run_series(
            [parse_stage("a")], log_path=tmp_path / "s.log", runner=runner, indexer=FakeIndexer(), sleep=lambda _: None
        )

        assert len(runner.calls) == 2
        assert outcomes[0].ok is True
        assert outcomes[0].attempts == 2

    def test_a_repeated_failure_stops_the_chain(self, tmp_path):
        runner = FakeRunner({"a": [1, 1], "b": [0]})

        outcomes = run_series(
            [parse_stage("a"), parse_stage("b")],
            log_path=tmp_path / "s.log",
            runner=runner,
            indexer=FakeIndexer(),
            sleep=lambda _: None,
        )

        assert [outcome.stage for outcome in outcomes] == ["a"]
        assert outcomes[0].ok is False
        assert "b" not in " ".join(" ".join(call) for call in runner.calls)

    def test_the_indexer_is_paused_for_the_window_and_restored(self, tmp_path):
        indexer = FakeIndexer()

        run_series(
            [parse_stage("a")], log_path=tmp_path / "s.log", runner=FakeRunner(), indexer=indexer, sleep=lambda _: None
        )

        assert indexer.actions == ["stop", "start"]

    def test_the_indexer_is_restored_even_when_a_stage_fails(self, tmp_path):
        indexer = FakeIndexer()

        run_series(
            [parse_stage("a")],
            log_path=tmp_path / "s.log",
            runner=FakeRunner({"a": [1, 1]}),
            indexer=indexer,
            sleep=lambda _: None,
        )

        assert indexer.actions == ["stop", "start"]

    def test_the_log_records_each_stage_and_its_outcome(self, tmp_path):
        log_path = tmp_path / "s.log"

        run_series(
            [parse_stage("a")], log_path=log_path, runner=FakeRunner(), indexer=FakeIndexer(), sleep=lambda _: None
        )

        text = log_path.read_text()
        assert "series start" in text
        assert "stage a: attempt 1" in text
        assert "stage a: ok" in text
        assert "indexer restored" in text

    def test_summary_is_readable_and_payload_is_json(self, tmp_path):
        outcomes = run_series(
            [parse_stage("a")],
            log_path=tmp_path / "s.log",
            runner=FakeRunner(),
            indexer=FakeIndexer(),
            sleep=lambda _: None,
        )

        assert "stage" in summarise(outcomes)
        assert outcomes[0].as_dict()["stage"] == "a"
