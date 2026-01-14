"""Tests for PrometheusClient with mocked responses."""

from unittest.mock import Mock, patch
import pytest
from metrics.prometheus_client import PrometheusClient


@pytest.fixture
def client():
    return PrometheusClient("http://localhost:9090")


@pytest.fixture
def mock_response():
    def _make_response(data, status_code=200):
        mock = Mock()
        mock.status_code = status_code
        mock.json.return_value = data
        mock.raise_for_status = Mock()
        if status_code >= 400:
            mock.raise_for_status.side_effect = Exception("HTTP Error")
        return mock
    return _make_response


class TestQueryInstant:
    def test_returns_value_on_success(self, client, mock_response):
        response_data = {
            "status": "success",
            "data": {
                "resultType": "vector",
                "result": [{"metric": {}, "value": [1609459200, "42.5"]}],
            },
        }

        with patch.object(client._session, "get", return_value=mock_response(response_data)):
            result = client.query_instant("up")
            assert result == 42.5

    def test_returns_none_on_empty_result(self, client, mock_response):
        response_data = {
            "status": "success",
            "data": {"resultType": "vector", "result": []},
        }

        with patch.object(client._session, "get", return_value=mock_response(response_data)):
            result = client.query_instant("nonexistent_metric")
            assert result is None

    def test_returns_none_on_connection_error(self, client):
        import requests
        with patch.object(client._session, "get", side_effect=requests.ConnectionError("Connection refused")):
            result = client.query_instant("up")
            assert result is None

    def test_passes_timestamp_parameter(self, client, mock_response):
        response_data = {
            "status": "success",
            "data": {"result": [{"value": [1609459200, "1.0"]}]},
        }

        with patch.object(client._session, "get", return_value=mock_response(response_data)) as mock_get:
            client.query_instant("up", timestamp=1609459200)
            call_params = mock_get.call_args[1]["params"]
            assert call_params["time"] == 1609459200


class TestQueryRange:
    def test_returns_values_on_success(self, client, mock_response):
        response_data = {
            "status": "success",
            "data": {
                "resultType": "matrix",
                "result": [
                    {
                        "metric": {},
                        "values": [
                            [1609459200, "1.0"],
                            [1609459215, "2.0"],
                            [1609459230, "3.0"],
                        ],
                    }
                ],
            },
        }

        with patch.object(client._session, "get", return_value=mock_response(response_data)):
            result = client.query_range("up", 1609459200, 1609459230, step=15)
            assert result == [(1609459200, 1.0), (1609459215, 2.0), (1609459230, 3.0)]

    def test_returns_empty_list_on_no_data(self, client, mock_response):
        response_data = {
            "status": "success",
            "data": {"resultType": "matrix", "result": []},
        }

        with patch.object(client._session, "get", return_value=mock_response(response_data)):
            result = client.query_range("nonexistent", 1609459200, 1609459230)
            assert result == []

    def test_returns_empty_list_on_error(self, client):
        import requests
        with patch.object(client._session, "get", side_effect=requests.Timeout("timeout")):
            result = client.query_range("up", 1609459200, 1609459230)
            assert result == []


class TestGetLatencyPercentiles:
    def test_returns_all_percentiles(self, client):
        def mock_query_instant(expr: str, timestamp=None):
            if "0.5" in expr:
                return 45.0
            elif "0.95" in expr:
                return 85.0
            elif "0.99" in expr:
                return 150.0
            return None

        with patch.object(client, "query_instant", side_effect=mock_query_instant):
            result = client.get_latency_percentiles("30s")
            assert result == {"p50": 45.0, "p95": 85.0, "p99": 150.0}

    def test_returns_zero_for_missing_percentiles(self, client):
        with patch.object(client, "query_instant", return_value=None):
            result = client.get_latency_percentiles()
            assert result == {"p50": 0.0, "p95": 0.0, "p99": 0.0}


class TestGetErrorRate:
    def test_returns_error_rate(self, client):
        with patch.object(client, "query_instant", return_value=0.05):
            result = client.get_error_rate("1m")
            assert result == 0.05

    def test_returns_zero_on_none(self, client):
        with patch.object(client, "query_instant", return_value=None):
            result = client.get_error_rate()
            assert result == 0.0

    def test_clamps_to_valid_range(self, client):
        with patch.object(client, "query_instant", return_value=1.5):
            result = client.get_error_rate()
            assert result == 1.0

        with patch.object(client, "query_instant", return_value=-0.1):
            result = client.get_error_rate()
            assert result == 0.0

    def test_handles_nan(self, client):
        with patch.object(client, "query_instant", return_value=float("nan")):
            result = client.get_error_rate()
            assert result == 0.0


class TestGetThroughput:
    def test_returns_throughput(self, client):
        with patch.object(client, "query_instant", return_value=125.5):
            result = client.get_throughput("1m")
            assert result == 125.5

    def test_returns_zero_on_none(self, client):
        with patch.object(client, "query_instant", return_value=None):
            result = client.get_throughput()
            assert result == 0.0


class TestGetSloViolations:
    def test_returns_violation_count_from_metric(self, client):
        with patch.object(client, "query_instant", return_value=5.0):
            result = client.get_slo_violations(threshold_ms=200)
            assert result == 5

    def test_fallback_to_percentile_check(self, client):
        def mock_query(expr: str, timestamp=None):
            if "slo_violation_total" in expr:
                return None
            return None

        with patch.object(client, "query_instant", side_effect=mock_query):
            with patch.object(
                client, "get_latency_percentiles", return_value={"p50": 50, "p95": 100, "p99": 250}
            ):
                result = client.get_slo_violations(threshold_ms=200)
                assert result == 1

    def test_no_violation_when_under_threshold(self, client):
        with patch.object(client, "query_instant", return_value=None):
            with patch.object(
                client, "get_latency_percentiles", return_value={"p50": 30, "p95": 80, "p99": 150}
            ):
                result = client.get_slo_violations(threshold_ms=200)
                assert result == 0
