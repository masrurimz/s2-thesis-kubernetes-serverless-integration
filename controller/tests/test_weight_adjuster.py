"""Tests for HAProxy weight adjuster."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import socket

from intelligent_router.weight_adjuster import HAProxyWeightAdjuster


class TestHAProxyWeightAdjuster:
    """Tests for HAProxyWeightAdjuster class."""
    
    @pytest.fixture
    def adjuster(self):
        """Create adjuster with mocked connectivity."""
        with patch.object(HAProxyWeightAdjuster, '_test_socket_connectivity', return_value=False):
            with patch.object(HAProxyWeightAdjuster, '_test_tcp_socket_connectivity', return_value=False):
                return HAProxyWeightAdjuster()
    
    def test_init(self, adjuster):
        """Test adjuster initialization."""
        assert adjuster.backend_name == "servers"
        assert adjuster.k3s_server == "k3s-cluster"
        assert adjuster.knative_server == "knative"
    
    def test_parse_stats_response(self, adjuster, mock_haproxy_stats):
        """Test parsing HAProxy stats CSV."""
        weights = adjuster._parse_stats_response(mock_haproxy_stats)
        
        assert weights is not None
        assert weights['k3s'] == 80
        assert weights['knative'] == 20
    
    def test_parse_stats_invalid_response(self, adjuster):
        """Test parsing invalid stats response."""
        weights = adjuster._parse_stats_response("invalid data")
        assert weights is None
    
    def test_parse_stats_empty_response(self, adjuster):
        """Test parsing empty stats response."""
        weights = adjuster._parse_stats_response("")
        assert weights is None
    
    def test_parse_stats_missing_servers(self, adjuster):
        """Test parsing stats with missing servers."""
        partial_stats = """# pxname,svname,weight
servers,other-server,0,0,0,1,100,1000,50000,100000,0,0,0,0,0,0,0,UP,50,1
"""
        weights = adjuster._parse_stats_response(partial_stats)
        assert weights is None
    
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
    
    @patch('requests.get')
    def test_get_current_weights_http_fallback(self, mock_get, adjuster, mock_haproxy_stats):
        """Test getting weights via HTTP fallback."""
        mock_response = Mock()
        mock_response.text = mock_haproxy_stats
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        weights = adjuster.get_current_weights()
        
        assert weights is not None
        assert weights['k3s'] == 80
        assert weights['knative'] == 20
    
    @patch('requests.get')
    def test_get_current_weights_http_failure(self, mock_get, adjuster):
        """Test handling HTTP failure."""
        mock_get.side_effect = Exception("Connection failed")
        
        weights = adjuster.get_current_weights()
        assert weights is None
    
    @patch('requests.get')
    def test_get_current_weights_timeout(self, mock_get, adjuster):
        """Test handling HTTP timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        weights = adjuster.get_current_weights()
        assert weights is None


class TestTCPSocketConnection:
    """Tests for TCP socket functionality."""
    
    def test_send_command_tcp_connection_refused(self):
        """Test TCP command when connection refused."""
        with patch.object(HAProxyWeightAdjuster, '_test_socket_connectivity', return_value=False):
            with patch.object(HAProxyWeightAdjuster, '_test_tcp_socket_connectivity', return_value=False):
                adjuster = HAProxyWeightAdjuster(tcp_socket_port=65432)
        
        result = adjuster._send_command_tcp("show info")
        assert result is None
    
    def test_test_socket_connectivity_failure(self):
        """Test Unix socket connectivity check when socket doesn't exist."""
        with patch.object(HAProxyWeightAdjuster, '_test_tcp_socket_connectivity', return_value=False):
            adjuster = HAProxyWeightAdjuster(socket_path="/nonexistent/socket.sock")
        
        assert adjuster._test_socket_connectivity() is False
    
    def test_test_tcp_socket_connectivity_failure(self):
        """Test TCP socket connectivity check when port not available."""
        with patch.object(HAProxyWeightAdjuster, '_test_socket_connectivity', return_value=False):
            adjuster = HAProxyWeightAdjuster(tcp_socket_port=65000)
        
        assert adjuster._test_tcp_socket_connectivity() is False


class TestWeightAdjusterRetry:
    """Tests for retry logic in weight adjuster."""
    
    @pytest.fixture
    def adjuster(self):
        """Create adjuster with mocked connectivity."""
        with patch.object(HAProxyWeightAdjuster, '_test_socket_connectivity', return_value=False):
            with patch.object(HAProxyWeightAdjuster, '_test_tcp_socket_connectivity', return_value=False):
                adj = HAProxyWeightAdjuster()
                adj.retry_delay = 0.01
                return adj
    
    @patch.object(HAProxyWeightAdjuster, 'set_weights')
    def test_set_weights_with_retry_success(self, mock_set, adjuster):
        """Test retry logic succeeds on first try."""
        mock_set.return_value = True
        
        result = adjuster.set_weights_with_retry(80, 20)
        
        assert result is True
        assert mock_set.call_count == 1
    
    @patch.object(HAProxyWeightAdjuster, 'set_weights')
    def test_set_weights_with_retry_eventual_success(self, mock_set, adjuster):
        """Test retry logic succeeds on second try."""
        mock_set.side_effect = [False, True]
        
        result = adjuster.set_weights_with_retry(80, 20)
        
        assert result is True
        assert mock_set.call_count == 2
    
    @patch.object(HAProxyWeightAdjuster, 'set_weights')
    def test_set_weights_with_retry_all_failures(self, mock_set, adjuster):
        """Test retry logic after all attempts fail."""
        mock_set.return_value = False
        
        result = adjuster.set_weights_with_retry(80, 20)
        
        assert result is False
        assert mock_set.call_count == adjuster.retry_attempts


class TestServerManagement:
    """Tests for server enable/disable functionality."""
    
    @pytest.fixture
    def adjuster(self):
        """Create adjuster with mocked connectivity."""
        with patch.object(HAProxyWeightAdjuster, '_test_socket_connectivity', return_value=False):
            with patch.object(HAProxyWeightAdjuster, '_test_tcp_socket_connectivity', return_value=False):
                return HAProxyWeightAdjuster()
    
    @patch.object(HAProxyWeightAdjuster, '_send_command')
    def test_disable_server_success(self, mock_send, adjuster):
        """Test disabling a server."""
        mock_send.return_value = "OK"
        
        result = adjuster.disable_server('k3s')
        
        assert result is True
        mock_send.assert_called_once()
    
    @patch.object(HAProxyWeightAdjuster, '_send_command')
    def test_disable_server_failure(self, mock_send, adjuster):
        """Test disabling server failure."""
        mock_send.return_value = None
        
        result = adjuster.disable_server('knative')
        
        assert result is False
    
    @patch.object(HAProxyWeightAdjuster, '_send_command')
    def test_enable_server_success(self, mock_send, adjuster):
        """Test enabling a server."""
        mock_send.return_value = "OK"
        
        result = adjuster.enable_server('k3s')
        
        assert result is True
    
    @patch.object(HAProxyWeightAdjuster, '_send_command')
    def test_get_server_status(self, mock_send, adjuster, mock_haproxy_stats):
        """Test getting server status."""
        mock_send.return_value = mock_haproxy_stats
        
        status = adjuster.get_server_status()
        
        assert 'k3s' in status
        assert 'knative' in status
