#!/usr/bin/env python3
"""
Sprint 2: HAProxy Weight Adjuster

This module handles real-time traffic weight adjustment through HAProxy's
admin socket interface for intelligent routing decisions.
"""

import socket
import time
from typing import Dict, Optional, Tuple

import structlog

logger = structlog.get_logger(__name__)


class HAProxyWeightAdjuster:
    """Manages HAProxy backend server weight adjustments via admin socket."""
    
    def __init__(self, 
                 socket_path: str = "/tmp/haproxy-admin.sock",
                 backend_name: str = "hybrid-backend",
                 k3s_server: str = "k3s-backend",
                 knative_server: str = "knative-backend"):
        """
        Initialize HAProxy weight adjuster.
        
        Args:
            socket_path: Path to HAProxy admin socket
            backend_name: HAProxy backend name
            k3s_server: K3s server name in HAProxy config
            knative_server: Knative server name in HAProxy config
        """
        self.socket_path = socket_path
        self.backend_name = backend_name
        self.k3s_server = k3s_server
        self.knative_server = knative_server
        
        # Connection settings
        self.socket_timeout = 5.0
        self.retry_attempts = 3
        self.retry_delay = 1.0
        
        logger.info("HAProxyWeightAdjuster initialized",
                   socket_path=socket_path,
                   backend=backend_name)
        
    def _send_command(self, command: str) -> Optional[str]:
        """
        Send command to HAProxy admin socket.
        
        Args:
            command: HAProxy admin command
            
        Returns:
            Command response or None if failed
        """
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(self.socket_timeout)
            
            # Connect and send command
            sock.connect(self.socket_path)
            sock.send((command + '\n').encode())
            
            # Receive response
            response = sock.recv(4096).decode().strip()
            sock.close()
            
            logger.debug("HAProxy command sent",
                        command=command,
                        response_length=len(response))
            
            return response
            
        except FileNotFoundError:
            logger.error("HAProxy admin socket not found", path=self.socket_path)
            return None
        except socket.timeout:
            logger.error("HAProxy socket timeout", command=command)
            return None
        except Exception as e:
            logger.error("HAProxy command failed", command=command, error=str(e))
            return None
            
    def test_connection(self) -> bool:
        """
        Test HAProxy admin socket connection.
        
        Returns:
            True if connection working, False otherwise
        """
        try:
            response = self._send_command("show info")
            if response and "HAProxy" in response:
                logger.info("HAProxy admin socket connection successful")
                return True
            else:
                logger.warning("HAProxy admin socket test failed")
                return False
                
        except Exception as e:
            logger.error("HAProxy connection test failed", error=str(e))
            return False
            
    def get_current_weights(self) -> Optional[Dict[str, int]]:
        """
        Get current backend server weights from HAProxy.
        
        Returns:
            Dictionary with current weights or None if failed
        """
        try:
            response = self._send_command("show stat")
            if not response:
                return None
                
            # Parse HAProxy stats CSV
            lines = response.strip().split('\n')
            
            weights = {}
            for line in lines:
                if not line or line.startswith('#'):
                    continue
                    
                fields = line.split(',')
                if len(fields) < 19:  # Ensure we have enough fields
                    continue
                    
                pxname = fields[0]  # Proxy name
                svname = fields[1]  # Server name
                weight = fields[18] # Weight field
                
                if pxname == self.backend_name:
                    if svname == self.k3s_server:
                        weights['k3s'] = int(weight) if weight.isdigit() else 0
                    elif svname == self.knative_server:
                        weights['knative'] = int(weight) if weight.isdigit() else 0
                        
            if 'k3s' in weights and 'knative' in weights:
                logger.debug("Current weights retrieved", weights=weights)
                return weights
            else:
                logger.warning("Could not parse current weights from HAProxy stats")
                return None
                
        except Exception as e:
            logger.error("Failed to get current weights", error=str(e))
            return None
            
    def set_weights(self, k3s_weight: int, knative_weight: int) -> bool:
        """
        Set backend server weights in HAProxy.
        
        Args:
            k3s_weight: Weight for K3s backend (0-100)
            knative_weight: Weight for Knative backend (0-100)
            
        Returns:
            True if weights set successfully, False otherwise
        """
        try:
            # Validate weights
            if not (0 <= k3s_weight <= 100 and 0 <= knative_weight <= 100):
                logger.error("Invalid weights", k3s=k3s_weight, knative=knative_weight)
                return False
                
            if k3s_weight + knative_weight == 0:
                logger.error("Total weight cannot be zero")
                return False
                
            # Get current weights for comparison
            current_weights = self.get_current_weights()
            if current_weights:
                if (current_weights['k3s'] == k3s_weight and 
                    current_weights['knative'] == knative_weight):
                    logger.debug("Weights already set correctly", 
                                k3s=k3s_weight, knative=knative_weight)
                    return True
                    
            # Set K3s backend weight
            k3s_command = f"set weight {self.backend_name}/{self.k3s_server} {k3s_weight}"
            k3s_response = self._send_command(k3s_command)
            
            if not k3s_response:
                logger.error("Failed to set K3s weight", weight=k3s_weight)
                return False
                
            # Set Knative backend weight
            knative_command = f"set weight {self.backend_name}/{self.knative_server} {knative_weight}"
            knative_response = self._send_command(knative_command)
            
            if not knative_response:
                logger.error("Failed to set Knative weight", weight=knative_weight)
                # Try to rollback K3s weight if possible
                if current_weights:
                    self._send_command(f"set weight {self.backend_name}/{self.k3s_server} {current_weights['k3s']}")
                return False
                
            # Verify weights were set correctly
            time.sleep(0.5)  # Brief delay for HAProxy to update
            new_weights = self.get_current_weights()
            
            if (new_weights and 
                new_weights['k3s'] == k3s_weight and 
                new_weights['knative'] == knative_weight):
                
                logger.info("Weights updated successfully",
                           previous=current_weights,
                           new=new_weights)
                return True
            else:
                logger.error("Weight verification failed",
                           expected={'k3s': k3s_weight, 'knative': knative_weight},
                           actual=new_weights)
                return False
                
        except Exception as e:
            logger.error("Weight adjustment failed", error=str(e))
            return False
            
    def set_weights_with_retry(self, k3s_weight: int, knative_weight: int) -> bool:
        """
        Set weights with retry logic for improved reliability.
        
        Args:
            k3s_weight: Weight for K3s backend
            knative_weight: Weight for Knative backend
            
        Returns:
            True if successful, False after all retries failed
        """
        for attempt in range(self.retry_attempts):
            try:
                if self.set_weights(k3s_weight, knative_weight):
                    return True
                    
                if attempt < self.retry_attempts - 1:
                    logger.warning("Weight adjustment attempt failed, retrying",
                                 attempt=attempt + 1,
                                 total_attempts=self.retry_attempts)
                    time.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error("Weight adjustment attempt failed", 
                           attempt=attempt + 1, error=str(e))
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay)
                    
        logger.error("All weight adjustment attempts failed")
        return False
        
    def disable_server(self, server: str) -> bool:
        """
        Disable a backend server (emergency use).
        
        Args:
            server: Server name ('k3s' or 'knative')
            
        Returns:
            True if server disabled successfully
        """
        try:
            server_name = self.k3s_server if server == 'k3s' else self.knative_server
            command = f"disable server {self.backend_name}/{server_name}"
            
            response = self._send_command(command)
            if response:
                logger.warning("Server disabled", server=server, response=response)
                return True
            else:
                logger.error("Failed to disable server", server=server)
                return False
                
        except Exception as e:
            logger.error("Server disable failed", server=server, error=str(e))
            return False
            
    def enable_server(self, server: str) -> bool:
        """
        Enable a backend server.
        
        Args:
            server: Server name ('k3s' or 'knative')
            
        Returns:
            True if server enabled successfully
        """
        try:
            server_name = self.k3s_server if server == 'k3s' else self.knative_server
            command = f"enable server {self.backend_name}/{server_name}"
            
            response = self._send_command(command)
            if response:
                logger.info("Server enabled", server=server, response=response)
                return True
            else:
                logger.error("Failed to enable server", server=server)
                return False
                
        except Exception as e:
            logger.error("Server enable failed", server=server, error=str(e))
            return False
            
    def get_server_status(self) -> Dict[str, str]:
        """
        Get status of backend servers.
        
        Returns:
            Dictionary with server statuses
        """
        try:
            response = self._send_command("show stat")
            if not response:
                return {}
                
            status = {}
            lines = response.strip().split('\n')
            
            for line in lines:
                if not line or line.startswith('#'):
                    continue
                    
                fields = line.split(',')
                if len(fields) < 17:
                    continue
                    
                pxname = fields[0]  # Proxy name
                svname = fields[1]  # Server name
                status_field = fields[17]  # Status field
                
                if pxname == self.backend_name:
                    if svname == self.k3s_server:
                        status['k3s'] = status_field
                    elif svname == self.knative_server:
                        status['knative'] = status_field
                        
            logger.debug("Server status retrieved", status=status)
            return status
            
        except Exception as e:
            logger.error("Failed to get server status", error=str(e))
            return {}


def main():
    """Test the HAProxy weight adjuster."""
    adjuster = HAProxyWeightAdjuster()
    
    # Test connection
    if not adjuster.test_connection():
        print("HAProxy admin socket not available")
        return
        
    # Get current weights
    current = adjuster.get_current_weights()
    print(f"Current weights: {current}")
    
    # Test weight adjustment
    if current:
        # Swap weights for testing
        new_k3s = current['knative']
        new_knative = current['k3s']
        
        print(f"Setting new weights: k3s={new_k3s}, knative={new_knative}")
        success = adjuster.set_weights(new_k3s, new_knative)
        print(f"Weight adjustment {'successful' if success else 'failed'}")
        
        # Verify
        updated = adjuster.get_current_weights()
        print(f"Updated weights: {updated}")


if __name__ == "__main__":
    main()