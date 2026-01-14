"""Tests for CLF parser."""
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "data" / "scripts"))

from clf_parser import parse_clf_line, parse_clf_file, clf_to_rps, create_train_val_test_split


class TestCLFParser:
    """Tests for CLF parsing functions."""

    def test_parse_valid_clf_line(self):
        """Test parsing a valid CLF line."""
        line = '192.168.1.1 - - [14/Jan/2026:10:30:00 +0000] "GET /index.html HTTP/1.1" 200 1234'
        result = parse_clf_line(line)

        assert result is not None
        timestamp, request, status, bytes_sent = result
        assert request == "GET /index.html HTTP/1.1"
        assert status == 200
        assert bytes_sent == 1234

    def test_parse_invalid_clf_line(self):
        """Test parsing invalid line returns None."""
        line = "this is not a valid clf line"
        result = parse_clf_line(line)
        assert result is None

    def test_parse_clf_line_with_dash_bytes(self):
        """Test parsing line with dash for bytes."""
        line = '192.168.1.1 - - [14/Jan/2026:10:30:00 +0000] "GET / HTTP/1.1" 304 -'
        result = parse_clf_line(line)

        assert result is not None
        _, _, status, bytes_sent = result
        assert status == 304
        assert bytes_sent == 0


class TestCLFToRPS:
    """Tests for CLF to RPS conversion."""

    @pytest.fixture
    def sample_clf_file(self, tmp_path):
        """Create sample CLF file."""
        content = '''192.168.1.1 - - [14/Jan/2026:10:30:00 +0000] "GET /a HTTP/1.1" 200 100
192.168.1.2 - - [14/Jan/2026:10:30:00 +0000] "GET /b HTTP/1.1" 200 200
192.168.1.3 - - [14/Jan/2026:10:30:01 +0000] "GET /c HTTP/1.1" 200 300
192.168.1.4 - - [14/Jan/2026:10:30:01 +0000] "GET /d HTTP/1.1" 404 0
192.168.1.5 - - [14/Jan/2026:10:30:02 +0000] "GET /e HTTP/1.1" 200 500
'''
        clf_path = tmp_path / "test.log"
        clf_path.write_text(content)
        return clf_path

    def test_clf_to_rps(self, sample_clf_file):
        """Test converting CLF to RPS."""
        df = clf_to_rps(sample_clf_file, resolution_seconds=1)

        assert len(df) == 3  # 3 unique seconds
        assert "rps" in df.columns
        assert "timestamp" in df.columns

        # First second has 2 requests
        assert df.iloc[0]["rps"] == 2

    def test_clf_to_rps_with_output(self, sample_clf_file, tmp_path):
        """Test saving RPS to CSV."""
        output_path = tmp_path / "output.csv"
        df = clf_to_rps(sample_clf_file, output_path=output_path)

        assert output_path.exists()
        assert len(df) > 0


class TestTrainValTestSplit:
    """Tests for data splitting."""

    def test_split_ratios(self):
        """Test split maintains correct ratios."""
        import pandas as pd
        from datetime import datetime, timedelta

        data = []
        base = datetime.now()
        for i in range(100):
            data.append({"timestamp": base + timedelta(seconds=i), "rps": 100 + i})
        df = pd.DataFrame(data)

        train, val, test = create_train_val_test_split(
            df, train_ratio=0.7, val_ratio=0.15
        )

        assert len(train) == 70
        assert len(val) == 15
        assert len(test) == 15

    def test_split_is_temporal(self):
        """Test split maintains temporal order."""
        import pandas as pd
        from datetime import datetime, timedelta

        data = []
        base = datetime.now()
        for i in range(100):
            data.append(
                {
                    "timestamp": base + timedelta(seconds=i),
                    "rps": i,  # Use index as value to verify order
                }
            )
        df = pd.DataFrame(data)

        train, val, test = create_train_val_test_split(df)

        # Train should have earliest data
        assert train["rps"].max() < val["rps"].min()
        # Val should be before test
        assert val["rps"].max() < test["rps"].min()
