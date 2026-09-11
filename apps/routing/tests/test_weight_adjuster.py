"""Tests for HAProxy weight adjuster."""

import pytest
from unittest.mock import Mock, patch

from routing.algorithm.weight_adjuster import HAProxyWeightAdjuster


class TestHAProxyWeightAdjuster:
    """Tests for HAProxyWeightAdjuster class."""

    @pytest.fixture
    def adjuster(self):
        """Create adjuster with mocked connectivity."""
        with patch.object(HAProxyWeightAdjuster, "_test_connection", return_value=False):
            return HAProxyWeightAdjuster()

    def test_init(self, adjuster):
        """Test adjuster initialization."""
        assert adjuster.tcp_socket_host == "localhost"
        assert adjuster.tcp_socket_port == 9999
        assert adjuster.stats_url == "http://localhost:18404/stats;csv"
        assert adjuster.backend_name == "servers"
        assert adjuster.socket_available is False

    def test_validate_weights_valid(self, adjuster):
        """Test weight validation with valid values."""
        result = adjuster.set_weights(80, 20)
        assert result is False

    def test_validate_weights_out_of_range_high(self, adjuster):
        """Test weight validation with out of range values (too high)."""
        result = adjuster.set_weights(150, 20)
        assert result is False

    def test_validate_weights_out_of_range_negative(self, adjuster):
        """Test weight validation with negative values."""
        result = adjuster.set_weights(-10, 20)
        assert result is False

    def test_validate_weights_zero_total(self, adjuster):
        """Test weight validation with zero total."""
        result = adjuster.set_weights(0, 0)
        assert result is False

    @patch("requests.get")
    def test_get_current_weights_http_fallback(self, mock_get, adjuster):
        """Test getting weights via HTTP stats."""
        stats_csv = "\n".join(
            [
                "# pxname,svname,qcur,qmax,scur,smax,slim,stot,bin,bout,dreq,dresp,ereq,econ,eresp,wretr,wredis,status,weight,act,bck",
                "servers,k3s,0,0,0,1,100,1000,50000,100000,0,0,0,0,0,0,0,UP,80,1,0",
                "servers,knative,0,0,0,1,100,250,12500,25000,0,0,0,0,0,0,0,UP,20,1,0",
            ]
        )
        mock_response = Mock()
        mock_response.text = stats_csv
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        weights = adjuster.get_current_weights()

        assert weights == {"k3s": 80, "knative": 20}

    @patch("requests.get")
    def test_get_current_weights_http_failure(self, mock_get, adjuster):
        """Test handling HTTP failure."""
        mock_get.side_effect = Exception("Connection failed")

        weights = adjuster.get_current_weights()
        assert weights == {}

    @patch("requests.get")
    def test_get_current_weights_timeout(self, mock_get, adjuster):
        """Test handling HTTP timeout."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        weights = adjuster.get_current_weights()
        assert weights == {}


class TestTCPSocketConnection:
    """Tests for TCP socket functionality."""

    def test_send_command_connection_refused(self):
        """Test TCP command when connection refused."""
        adjuster = HAProxyWeightAdjuster(tcp_socket_port=65432)
        adjuster.socket_available = False

        result = adjuster._send_command("show info")
        assert result is None

    def test_test_connection_failure(self):
        """Test connectivity check when port not available."""
        adjuster = HAProxyWeightAdjuster(tcp_socket_port=65000)
        adjuster.socket_available = False

        assert adjuster._test_connection() is False


class TestWeightAdjusterRetry:
    """Tests for retry logic in weight adjuster."""

    @pytest.fixture
    def adjuster(self):
        """Create adjuster with mocked connectivity."""
        with patch.object(HAProxyWeightAdjuster, "_test_connection", return_value=False):
            adj = HAProxyWeightAdjuster()
            return adj

    @patch.object(HAProxyWeightAdjuster, "set_weights")
    def test_set_weights_with_retry_success(self, mock_set, adjuster):
        """Test retry logic succeeds on first try."""
        mock_set.return_value = True

        result = adjuster.set_weights_with_retry(80, 20)

        assert result is True
        assert mock_set.call_count == 1

    @patch.object(HAProxyWeightAdjuster, "set_weights")
    def test_set_weights_with_retry_eventual_success(self, mock_set, adjuster):
        """Test retry logic succeeds on second try."""
        mock_set.side_effect = [False, True]

        result = adjuster.set_weights_with_retry(80, 20)

        assert result is True
        assert mock_set.call_count == 2

    @patch.object(HAProxyWeightAdjuster, "set_weights")
    def test_set_weights_with_retry_all_failures(self, mock_set, adjuster):
        """Test retry logic after all attempts fail."""
        mock_set.return_value = False

        result = adjuster.set_weights_with_retry(80, 20)

        assert result is False
        assert mock_set.call_count == 3
