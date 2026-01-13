#!/usr/bin/env python3
"""
Sprint 2: Fallback Handler for Intelligent Routing

Provides safe fallback strategies when predictions fail or confidence is low.
"""

import time
from typing import Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


class FallbackHandler:
    """Handles fallback routing strategies when intelligent routing fails."""
    
    def __init__(self,
                 safe_k3s_weight: int = 80,
                 safe_knative_weight: int = 20,
                 emergency_k3s_weight: int = 95,
                 emergency_knative_weight: int = 5):
        """
        Initialize fallback handler.
        
        Args:
            safe_k3s_weight: Safe default K3s weight
            safe_knative_weight: Safe default Knative weight  
            emergency_k3s_weight: Emergency K3s weight (minimal serverless)
            emergency_knative_weight: Emergency Knative weight
        """
        self.safe_k3s_weight = safe_k3s_weight
        self.safe_knative_weight = safe_knative_weight
        self.emergency_k3s_weight = emergency_k3s_weight
        self.emergency_knative_weight = emergency_knative_weight
        
        # Fallback state tracking
        self.fallback_mode = False
        self.emergency_mode = False
        self.last_fallback_time = None
        self.fallback_reason = None
        
        logger.info("FallbackHandler initialized",
                   safe_weights={'k3s': safe_k3s_weight, 'knative': safe_knative_weight})
        
    def get_fallback_weights(self, current_stats: Dict) -> Dict[str, int]:
        """
        Get fallback weights based on current system state.
        
        Args:
            current_stats: Current system statistics
            
        Returns:
            Dictionary with fallback weights
        """
        try:
            # Check for emergency conditions
            if self._is_emergency_condition(current_stats):
                return self._get_emergency_weights(current_stats)
            
            # Check for high load conditions
            if self._is_high_load_condition(current_stats):
                return self._get_high_load_weights(current_stats)
                
            # Check for low load conditions
            if self._is_low_load_condition(current_stats):
                return self._get_low_load_weights(current_stats)
                
            # Default safe weights
            self.fallback_reason = "default_safe"
            return {
                'k3s': self.safe_k3s_weight,
                'knative': self.safe_knative_weight
            }
            
        except Exception as e:
            logger.error("Fallback weight calculation failed", error=str(e))
            # Ultra-safe emergency weights
            return {
                'k3s': self.emergency_k3s_weight,
                'knative': self.emergency_knative_weight
            }
            
    def _is_emergency_condition(self, stats: Dict) -> bool:
        """Check if system is in emergency condition."""
        try:
            error_rate = stats.get('error_rate', 0.0)
            response_time = stats.get('avg_response_time', 0.0)
            
            # Emergency if high error rate or extremely high response time
            if error_rate > 0.05:  # 5% error rate
                self.fallback_reason = "high_error_rate"
                return True
                
            if response_time > 1000:  # 1 second response time
                self.fallback_reason = "high_response_time"
                return True
                
            return False
            
        except Exception:
            return True  # Assume emergency if we can't evaluate
            
    def _is_high_load_condition(self, stats: Dict) -> bool:
        """Check if system is under high load."""
        try:
            total_requests = stats.get('total_requests', 0)
            response_time = stats.get('avg_response_time', 0.0)
            
            # High load if many requests or elevated response time
            if total_requests > 2000:  # High request volume
                self.fallback_reason = "high_request_volume"
                return True
                
            if response_time > 200:  # Elevated response time
                self.fallback_reason = "elevated_response_time"
                return True
                
            return False
            
        except Exception:
            return False
            
    def _is_low_load_condition(self, stats: Dict) -> bool:
        """Check if system is under low load."""
        try:
            total_requests = stats.get('total_requests', 0)
            
            # Low load if very few requests
            if total_requests < 100:
                self.fallback_reason = "low_request_volume"
                return True
                
            return False
            
        except Exception:
            return False
            
    def _get_emergency_weights(self, stats: Dict) -> Dict[str, int]:
        """Get weights for emergency conditions."""
        self.emergency_mode = True
        self.last_fallback_time = int(time.time())
        
        logger.warning("Emergency fallback activated", 
                      reason=self.fallback_reason,
                      stats=stats)
        
        # Route most traffic to stable K3s
        return {
            'k3s': self.emergency_k3s_weight,
            'knative': self.emergency_knative_weight
        }
        
    def _get_high_load_weights(self, stats: Dict) -> Dict[str, int]:
        """Get weights for high load conditions."""
        self.fallback_mode = True
        self.last_fallback_time = int(time.time())
        
        logger.info("High load fallback activated",
                   reason=self.fallback_reason,
                   total_requests=stats.get('total_requests'))
        
        # Increase serverless for better scaling under high load
        return {
            'k3s': 60,  # Reduce K3s
            'knative': 40  # Increase serverless for scaling
        }
        
    def _get_low_load_weights(self, stats: Dict) -> Dict[str, int]:
        """Get weights for low load conditions."""
        self.fallback_mode = True
        self.last_fallback_time = int(time.time())
        
        logger.debug("Low load fallback activated",
                    reason=self.fallback_reason,
                    total_requests=stats.get('total_requests'))
        
        # Maximize K3s for cost efficiency during low load
        return {
            'k3s': 90,  # Maximize cost-efficient K3s
            'knative': 10  # Minimal serverless
        }
        
    def should_enable_intelligent_routing(self) -> bool:
        """
        Check if intelligent routing should be re-enabled.
        
        Returns:
            True if safe to re-enable intelligent routing
        """
        try:
            # Don't re-enable if in emergency mode
            if self.emergency_mode:
                return False
                
            # Don't re-enable if recent fallback
            if self.last_fallback_time:
                time_since_fallback = int(time.time()) - self.last_fallback_time
                if time_since_fallback < 300:  # 5 minutes
                    return False
                    
            # Safe to re-enable
            return True
            
        except Exception:
            return False
            
    def reset_fallback_state(self) -> None:
        """Reset fallback state after successful recovery."""
        self.fallback_mode = False
        self.emergency_mode = False
        self.fallback_reason = None
        
        logger.info("Fallback state reset - intelligent routing restored")
        
    def get_status(self) -> Dict:
        """Get current fallback handler status."""
        return {
            'fallback_mode': self.fallback_mode,
            'emergency_mode': self.emergency_mode,
            'last_fallback_time': self.last_fallback_time,
            'fallback_reason': self.fallback_reason,
            'safe_weights': {
                'k3s': self.safe_k3s_weight,
                'knative': self.safe_knative_weight
            },
            'emergency_weights': {
                'k3s': self.emergency_k3s_weight,
                'knative': self.emergency_knative_weight
            }
        }
        
    def get_recovery_weights(self, target_weights: Dict[str, int]) -> Dict[str, int]:
        """
        Get gradual recovery weights to transition back to intelligent routing.
        
        Args:
            target_weights: Target intelligent weights
            
        Returns:
            Gradual transition weights
        """
        try:
            if not self.fallback_mode and not self.emergency_mode:
                return target_weights
                
            # Get current safe weights
            current_weights = {
                'k3s': self.safe_k3s_weight,
                'knative': self.safe_knative_weight
            }
            
            # Calculate gradual transition (25% step toward target)
            transition_factor = 0.25
            
            k3s_diff = target_weights['k3s'] - current_weights['k3s']
            knative_diff = target_weights['knative'] - current_weights['knative']
            
            recovery_weights = {
                'k3s': int(current_weights['k3s'] + k3s_diff * transition_factor),
                'knative': int(current_weights['knative'] + knative_diff * transition_factor)
            }
            
            # Ensure weights sum to 100
            total = recovery_weights['k3s'] + recovery_weights['knative']
            if total != 100:
                recovery_weights['k3s'] = 100 - recovery_weights['knative']
                
            logger.debug("Recovery weights calculated",
                        current=current_weights,
                        target=target_weights,
                        recovery=recovery_weights)
            
            return recovery_weights
            
        except Exception as e:
            logger.error("Recovery weight calculation failed", error=str(e))
            return {
                'k3s': self.safe_k3s_weight,
                'knative': self.safe_knative_weight
            }


def main():
    """Test the fallback handler."""
    handler = FallbackHandler()
    
    # Test normal conditions
    normal_stats = {
        'total_requests': 1000,
        'avg_response_time': 25.0,
        'error_rate': 0.0
    }
    weights = handler.get_fallback_weights(normal_stats)
    print(f"Normal conditions: {weights}")
    
    # Test high load conditions
    high_load_stats = {
        'total_requests': 3000,
        'avg_response_time': 250.0,
        'error_rate': 0.0
    }
    weights = handler.get_fallback_weights(high_load_stats)
    print(f"High load conditions: {weights}")
    
    # Test emergency conditions
    emergency_stats = {
        'total_requests': 1000,
        'avg_response_time': 1500.0,
        'error_rate': 0.1
    }
    weights = handler.get_fallback_weights(emergency_stats)
    print(f"Emergency conditions: {weights}")
    
    # Test status
    status = handler.get_status()
    print(f"Handler status: {status}")


if __name__ == "__main__":
    main()