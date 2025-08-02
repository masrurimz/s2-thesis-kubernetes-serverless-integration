#!/usr/bin/env python3
"""
Sprint 2: Decision Logger for Intelligent Routing

Logs routing decisions with SQLite audit trail for analysis and debugging.
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class DecisionLogger:
    """Logs intelligent routing decisions for audit and analysis."""
    
    def __init__(self, db_path: str = "data/routing-decisions.db"):
        """
        Initialize decision logger.
        
        Args:
            db_path: SQLite database path
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        logger.info("DecisionLogger initialized", db_path=str(self.db_path))
        
    def _init_database(self) -> None:
        """Initialize SQLite database with routing decisions table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create routing decisions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS routing_decisions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp INTEGER NOT NULL,
                        decision_type TEXT NOT NULL,
                        current_stats TEXT,
                        prediction_data TEXT,
                        previous_weights TEXT,
                        target_weights TEXT,
                        weights_changed BOOLEAN,
                        decision_latency REAL,
                        confidence REAL,
                        load_change REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for efficient queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON routing_decisions(timestamp)
                """)
                
                conn.commit()
                logger.debug("Database initialized successfully")
                
        except Exception as e:
            logger.error("Database initialization failed", error=str(e))
            raise
            
    def log_decision(self, decision: Dict) -> bool:
        """
        Log a routing decision to the database.
        
        Args:
            decision: Decision data dictionary
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Extract data with safe defaults
                timestamp = decision.get('timestamp', int(time.time()))
                decision_type = decision.get('decision_type', 'unknown')
                current_stats = json.dumps(decision.get('current_stats', {}))
                prediction_data = json.dumps(decision.get('prediction', {}))
                previous_weights = json.dumps(decision.get('previous_weights', {}))
                target_weights = json.dumps(decision.get('target_weights', {}))
                weights_changed = decision.get('weights_changed', False)
                decision_latency = decision.get('decision_latency', 0.0)
                
                # Calculate additional metrics
                confidence = 0.0
                load_change = 0.0
                
                if 'prediction' in decision and decision['prediction']:
                    confidence = decision['prediction'].get('confidence', 0.0)
                    
                if 'current_stats' in decision and 'prediction' in decision:
                    current_req = decision['current_stats'].get('total_requests', 0)
                    predicted_req = decision['prediction'].get('predicted_requests', 0)
                    if current_req > 0:
                        load_change = (predicted_req - current_req) / current_req
                
                # Insert decision record
                cursor.execute("""
                    INSERT INTO routing_decisions 
                    (timestamp, decision_type, current_stats, prediction_data,
                     previous_weights, target_weights, weights_changed, 
                     decision_latency, confidence, load_change)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, decision_type, current_stats, prediction_data,
                    previous_weights, target_weights, weights_changed,
                    decision_latency, confidence, load_change
                ))
                
                conn.commit()
                
                logger.debug("Decision logged",
                           type=decision_type,
                           timestamp=timestamp,
                           weights_changed=weights_changed)
                return True
                
        except Exception as e:
            logger.error("Decision logging failed", error=str(e))
            return False
            
    def get_recent_decisions(self, hours: int = 24) -> List[Dict]:
        """
        Get recent routing decisions.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of decision dictionaries
        """
        try:
            cutoff_time = int(time.time()) - (hours * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM routing_decisions 
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
                
                columns = [desc[0] for desc in cursor.description]
                decisions = []
                
                for row in cursor.fetchall():
                    decision = dict(zip(columns, row))
                    
                    # Parse JSON fields
                    for field in ['current_stats', 'prediction_data', 
                                'previous_weights', 'target_weights']:
                        if decision[field]:
                            try:
                                decision[field] = json.loads(decision[field])
                            except json.JSONDecodeError:
                                decision[field] = {}
                                
                    decisions.append(decision)
                    
                logger.debug("Retrieved recent decisions", count=len(decisions))
                return decisions
                
        except Exception as e:
            logger.error("Failed to get recent decisions", error=str(e))
            return []
            
    def get_decision_stats(self, hours: int = 24) -> Dict:
        """
        Get decision statistics for analysis.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with decision statistics
        """
        try:
            cutoff_time = int(time.time()) - (hours * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get basic counts
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_decisions,
                        SUM(CASE WHEN weights_changed = 1 THEN 1 ELSE 0 END) as weight_changes,
                        SUM(CASE WHEN decision_type = 'intelligent' THEN 1 ELSE 0 END) as intelligent_decisions,
                        SUM(CASE WHEN decision_type = 'fallback' THEN 1 ELSE 0 END) as fallback_decisions,
                        AVG(decision_latency) as avg_latency,
                        AVG(confidence) as avg_confidence,
                        AVG(load_change) as avg_load_change
                    FROM routing_decisions 
                    WHERE timestamp >= ?
                """, (cutoff_time,))
                
                row = cursor.fetchone()
                
                stats = {
                    'total_decisions': row[0] or 0,
                    'weight_changes': row[1] or 0,
                    'intelligent_decisions': row[2] or 0,
                    'fallback_decisions': row[3] or 0,
                    'avg_latency': round(row[4] or 0, 3),
                    'avg_confidence': round(row[5] or 0, 3),
                    'avg_load_change': round(row[6] or 0, 3),
                    'analysis_period_hours': hours
                }
                
                # Calculate percentages
                if stats['total_decisions'] > 0:
                    stats['weight_change_rate'] = round(
                        (stats['weight_changes'] / stats['total_decisions']) * 100, 1
                    )
                    stats['intelligent_rate'] = round(
                        (stats['intelligent_decisions'] / stats['total_decisions']) * 100, 1
                    )
                else:
                    stats['weight_change_rate'] = 0.0
                    stats['intelligent_rate'] = 0.0
                    
                logger.debug("Decision stats calculated", **stats)
                return stats
                
        except Exception as e:
            logger.error("Failed to get decision stats", error=str(e))
            return {}
            
    def export_decisions(self, 
                        hours: int = 24, 
                        output_path: str = "data/decisions-export.json") -> bool:
        """
        Export decisions to JSON file for analysis.
        
        Args:
            hours: Number of hours to export
            output_path: Output file path
            
        Returns:
            True if exported successfully
        """
        try:
            decisions = self.get_recent_decisions(hours)
            stats = self.get_decision_stats(hours)
            
            export_data = {
                'export_timestamp': int(time.time()),
                'export_period_hours': hours,
                'statistics': stats,
                'decisions': decisions
            }
            
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            logger.info("Decisions exported", 
                       path=output_path,
                       count=len(decisions))
            return True
            
        except Exception as e:
            logger.error("Decision export failed", error=str(e))
            return False
            
    def cleanup_old_decisions(self, keep_days: int = 7) -> int:
        """
        Clean up old decision records.
        
        Args:
            keep_days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_time = int(time.time()) - (keep_days * 24 * 3600)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    DELETE FROM routing_decisions 
                    WHERE timestamp < ?
                """, (cutoff_time,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info("Old decisions cleaned up", 
                           deleted=deleted_count,
                           kept_days=keep_days)
                return deleted_count
                
        except Exception as e:
            logger.error("Decision cleanup failed", error=str(e))
            return 0


def main():
    """Test the decision logger."""
    logger_instance = DecisionLogger()
    
    # Test decision logging
    test_decision = {
        'timestamp': int(time.time()),
        'decision_type': 'intelligent',
        'current_stats': {'total_requests': 1000},
        'prediction': {'predicted_requests': 1200, 'confidence': 0.85},
        'previous_weights': {'k3s': 80, 'knative': 20},
        'target_weights': {'k3s': 70, 'knative': 30},
        'weights_changed': True,
        'decision_latency': 0.045
    }
    
    success = logger_instance.log_decision(test_decision)
    print(f"Decision logging: {'success' if success else 'failed'}")
    
    # Get stats
    stats = logger_instance.get_decision_stats(1)
    print(f"Decision stats: {stats}")


if __name__ == "__main__":
    main()