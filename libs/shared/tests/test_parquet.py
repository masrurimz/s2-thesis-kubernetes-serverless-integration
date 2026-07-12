"""Tests for atomic Parquet write/read with provenance metadata."""

import pyarrow as pa
import pytest

from shared.storage.parquet import REQUIRED_METADATA_KEYS, read_table_parquet, write_table_parquet


@pytest.fixture()
def sample_table():
    return pa.table(
        {
            "timestamp": pa.array([1.0, 2.0, 3.0], type=pa.float64()),
            "latency_ms": pa.array([10.5, 20.0, 30.5], type=pa.float64()),
            "scenario": pa.array(["s3", "s3", "s4"], type=pa.string()),
        }
    )


class TestWriteTableParquet:
    """Atomic write with provenance metadata."""

    def test_write_creates_file(self, sample_table, tmp_path):
        path = tmp_path / "metrics.parquet"
        write_table_parquet(
            sample_table,
            path,
            schema_version=2,
            metadata={
                "experiment_id": "phase-b/2026-07-12_h2",
                "scenario": "s4",
                "run_id": "1",
                "producer_git_commit": "abc1234",
                "generated_at": "2026-07-12T10:00:00+00:00",
            },
        )
        assert path.exists()
        assert path.stat().st_size > 0

    def test_no_temp_file_left_behind(self, sample_table, tmp_path):
        path = tmp_path / "metrics.parquet"
        write_table_parquet(
            sample_table,
            path,
            schema_version=2,
            metadata={
                "experiment_id": "exp1",
                "scenario": "s4",
                "run_id": "1",
                "producer_git_commit": "abc1234",
                "generated_at": "2026-07-12T10:00:00+00:00",
            },
        )
        # Only the destination file should exist, no .tmp leftovers
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].name == "metrics.parquet"

    def test_metadata_includes_required_keys(self, sample_table, tmp_path):
        path = tmp_path / "metrics.parquet"
        write_table_parquet(
            sample_table,
            path,
            schema_version=2,
            metadata={
                "experiment_id": "phase-b/2026-07-12_h2",
                "scenario": "s4",
                "run_id": "1",
                "producer_git_commit": "abc1234",
                "generated_at": "2026-07-12T10:00:00+00:00",
            },
        )
        table = read_table_parquet(path)
        meta = table.schema.metadata
        assert meta is not None
        for key in REQUIRED_METADATA_KEYS:
            assert key.encode() in meta, f"Missing metadata key: {key}"
        assert meta[b"evidence_schema_version"] == b"2"
        assert meta[b"experiment_id"] == b"phase-b/2026-07-12_h2"
        assert meta[b"scenario"] == b"s4"

    def test_overwrite_replaces_atomically(self, sample_table, tmp_path):
        path = tmp_path / "metrics.parquet"
        metadata = {
            "experiment_id": "exp1",
            "scenario": "s4",
            "run_id": "1",
            "producer_git_commit": "abc1234",
            "generated_at": "2026-07-12T10:00:00+00:00",
        }
        write_table_parquet(sample_table, path, schema_version=2, metadata=metadata)

        # Overwrite with a different table
        bigger_table = pa.table(
            {
                "timestamp": pa.array([1.0, 2.0, 3.0, 4.0], type=pa.float64()),
                "latency_ms": pa.array([10.5, 20.0, 30.5, 40.0], type=pa.float64()),
                "scenario": pa.array(["s3", "s3", "s4", "s4"], type=pa.string()),
            }
        )
        write_table_parquet(bigger_table, path, schema_version=2, metadata=metadata)

        result = read_table_parquet(path)
        assert result.num_rows == 4


class TestReadTableParquet:
    """Round-trip preserves data."""

    def test_round_trip_preserves_data(self, sample_table, tmp_path):
        path = tmp_path / "metrics.parquet"
        write_table_parquet(
            sample_table,
            path,
            schema_version=2,
            metadata={
                "experiment_id": "exp1",
                "scenario": "s4",
                "run_id": "1",
                "producer_git_commit": "abc1234",
                "generated_at": "2026-07-12T10:00:00+00:00",
            },
        )
        result = read_table_parquet(path)
        assert result.num_rows == 3
        assert result.column_names == sample_table.column_names
        assert result["scenario"].to_pylist() == ["s3", "s3", "s4"]
        assert result["latency_ms"].to_pylist() == [10.5, 20.0, 30.5]
