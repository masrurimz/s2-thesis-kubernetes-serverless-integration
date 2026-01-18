#!/usr/bin/env python3
"""
Validate HAProxy TCP socket connectivity and weight adjustment.

Run this script to verify the socket fix is working:
    uv run python scripts/validate_haproxy_socket.py
"""

import socket
import sys
import time

from config import settings

def test_tcp_connection(host: str = settings.HAPROXY_HOST, port: int = settings.HAPROXY_SOCKET_PORT) -> bool:
    """Test TCP socket connection to HAProxy."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        
        # Send show info command
        sock.send(b"show info\n")
        response = sock.recv(4096).decode()
        sock.close()
        
        if "HAProxy" in response or "Version" in response:
            print(f"✓ TCP socket connection successful on {host}:{port}")
            print(f"  Response snippet: {response[:100]}...")
            return True
        else:
            print(f"✗ Unexpected response: {response[:200]}")
            return False
            
    except ConnectionRefusedError:
        print(f"✗ Connection refused on {host}:{port}")
        print("  → Is HAProxy running? Try: docker-compose up -d")
        return False
    except socket.timeout:
        print(f"✗ Connection timeout on {host}:{port}")
        return False
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_weight_adjustment(host: str = settings.HAPROXY_HOST, port: int = settings.HAPROXY_SOCKET_PORT) -> bool:
    """Test weight adjustment via TCP socket."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        
        # Get current weights first
        sock.send(b"show stat\n")
        stats = sock.recv(8192).decode()
        sock.close()
        
        print("Current backend stats:")
        for line in stats.split('\n'):
            if 'servers,' in line and 'BACKEND' not in line:
                parts = line.split(',')
                if len(parts) > 18:
                    print(f"  {parts[1]}: weight={parts[18]}")
        
        # Try setting weight
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        sock.connect((host, port))
        
        cmd = "set server servers/k3s-cluster weight 70\n"
        sock.send(cmd.encode())
        response = sock.recv(1024).decode()
        sock.close()
        
        if response.strip() == "" or "weight" in response.lower():
            print("✓ Weight adjustment command accepted")
            
            # Verify change
            time.sleep(0.5)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((host, port))
            sock.send(b"show stat\n")
            new_stats = sock.recv(8192).decode()
            sock.close()
            
            for line in new_stats.split('\n'):
                if 'k3s-cluster' in line:
                    parts = line.split(',')
                    if len(parts) > 18:
                        new_weight = parts[18]
                        if new_weight == "70":
                            print(f"✓ Weight verified: k3s-cluster weight is now {new_weight}")
                            
                            # Restore original weight
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.connect((host, port))
                            sock.send(b"set server servers/k3s-cluster weight 80\n")
                            sock.close()
                            print("✓ Restored original weight (80)")
                            return True
            
            print("✗ Weight change not verified in stats")
            return False
        else:
            print(f"✗ Weight command failed: {response}")
            return False
            
    except Exception as e:
        print(f"✗ Weight adjustment test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("HAProxy TCP Socket Validation")
    print("=" * 60)
    print()
    
    # Test basic connection
    print("[1/2] Testing TCP socket connection...")
    conn_ok = test_tcp_connection()
    print()
    
    if not conn_ok:
        print("Cannot proceed without connection. Ensure HAProxy is running:")
        print("  cd infrastructure/haproxy && docker-compose up -d")
        sys.exit(1)
    
    # Test weight adjustment
    print("[2/2] Testing weight adjustment...")
    weight_ok = test_weight_adjustment()
    print()
    
    # Summary
    print("=" * 60)
    if conn_ok and weight_ok:
        print("✓ All validations passed!")
        print("  The HAProxy TCP socket fix is working correctly.")
        sys.exit(0)
    else:
        print("✗ Some validations failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
