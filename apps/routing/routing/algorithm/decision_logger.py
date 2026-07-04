#!/usr/bin/env python3
"""
Sprint 2: Decision Logger for Intelligent Routing

Logs routing decisions with SQLite audit trail for analysis and debugging.
"""

import json
import sqlite3
import time
from pathlib import Path
from typing import Dict, List

import structlog

logger = structlog.get_logger(__name__)


class DecisionLogger:
    """Logs intelligent routing decisions for audit and analysis."""

    def __init__(self, db_path: str = "data/routing-decisions.db"):
        """
        Initialize decision logger.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info("DecisionLogger initialized", db_path=str(self.db_path))

    def _init_database(self) -> None:
        """Initialize SQLite database with routing decisions table."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routing_decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    scenario TEXT NOT NULL,
                    action TEXT NOT NULL,
                    k3s_weight INTEGER NOT NULL,
                    knative_weight INTEGER NOT NULL,
                    reason TEXT,
                    p99_latency_ms REAL,
                    violation_duration_sec INTEGER,
                    predicted_requests INTEGER,
                    confidence REAL,
                    metadata TEXT
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON routing_decisions(timestamp)
            """)

            conn.commit()
            conn.close()
            logger.debug("Database initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise

    def log_decision(self, decision: Dict) -> bool:
        """
        Log a routing decision.

        Args:
            decision: Decision dictionary with routing details

        Returns:
            True if logged successfully
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO routing_decisions
                (timestamp, scenario, action, k3s_weight, knative_weight,
                 reason, p99_latency_ms, violation_duration_sec,
                 predicted_requests, confidence, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.get("timestamp", time.time()),
                    decision.get("scenario", "unknown"),
                    decision.get("action", "UNKNOWN"),
                    decision.get("k3s_weight", 0),
                    decision.get("knative_weight", 0),
                    decision.get("reason", ""),
                    decision.get("p99_latency_ms"),
                    decision.get("violation_duration_sec"),
                    decision.get("predicted_requests"),
                    decision.get("confidence"),
                    json.dumps(decision.get("metadata", {})),
                ),
            )

            conn.commit()
            conn.close()
            logger.debug("Decision logged", action=decision.get("action"))
            return True
        except Exception as e:
            logger.error("Failed to log decision", error=str(e))
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
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cutoff_time = time.time() - (hours * 3600)
            cursor.execute(
                """
                SELECT * FROM routing_decisions
                WHERE timestamp > ?
                ORDER BY timestamp DESC
                """,
                (cutoff_time,),
            )

            rows = cursor.fetchall()
            conn.close()

            decisions = []
            for row in rows:
                decision = dict(row)
                if decision.get("metadata"):
                    try:
                        decision["metadata"] = json.loads(decision["metadata"])
                    except json.JSONDecodeError:
                        decision["metadata"] = {}
                decisions.append(decision)

            logger.debug("Retrieved recent decisions", count=len(decisions), hours=hours)
            return decisions
        except Exception as e:
            logger.error("Failed to get recent decisions", error=str(e))
            return []

    def get_decision_stats(self, hours: int = 24) -> Dict:
        """
        Get statistics about routing decisions.

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with decision statistics
        """
        try:
            decisions = self.get_recent_decisions(hours)

            if not decisions:
                return {
                    "total_decisions": 0,
                    "action_counts": {},
                    "avg_p99_latency": 0,
                    "avg_confidence": 0,
                }

            action_counts = {}
            p99_latencies = []
            confidences = []

            for d in decisions:
                action = d.get("action", "UNKNOWN")
                action_counts[action] = action_counts.get(action, 0) + 1

                if d.get("p99_latency_ms") is not None:
                    p99_latencies.append(d["p99_latency_ms"])
                if d.get("confidence") is not None:
                    confidences.append(d["confidence"])

            stats = {
                "total_decisions": len(decisions),
                "action_counts": action_counts,
                "avg_p99_latency": sum(p99_latencies) / len(p99_latencies) if p99_latencies else 0,
                "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
                "time_range_hours": hours,
            }

            logger.debug("Computed decision stats", stats=stats)
            return stats
        except Exception as e:
            logger.error("Failed to compute decision stats", error=str(e))
            return {}

    def export_decisions(self, hours: int = 24, output_path: str = "data/decisions-export.json") -> bool:
        """
        Export decisions to JSON file.

        Args:
            hours: Number of hours to export
            output_path: Output file path

        Returns:
            True if exported successfully
        """
        try:
            decisions = self.get_recent_decisions(hours)

            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)

            with open(output, "w") as f:
                json.dump(
                    {
                        "export_time": time.time(),
                        "hours": hours,
                        "total_decisions": len(decisions),
                        "decisions": decisions,
                    },
                    f,
                    indent=2,
                )

            logger.info("Decisions exported", path=output_path, count=len(decisions))
            return True
        except Exception as e:
            logger.error("Failed to export decisions", error=str(e))
            return False

    def cleanup_old_decisions(self, keep_days: int = 7) -> int:
        """
        Remove decisions older than keep_days.

        Args:
            keep_days: Number of days to keep

        Returns:
            Number of deleted rows
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cutoff_time = time.time() - (keep_days * 24 * 3600)
            cursor.execute(
                "DELETE FROM routing_decisions WHERE timestamp < ?",
                (cutoff_time,),
            )

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info("Cleaned up old decisions", deleted=deleted, keep_days=keep_days)
            return deleted
        except Exception as e:
            logger.error("Failed to cleanup old decisions", error=str(e))
            return 0


def main():
    """Test the decision logger."""
    logger = DecisionLogger(db_path="data/test-decisions.db")

    # Log a test decision
    decision = {
        "timestamp": time.time(),
        "scenario": "s3-hybrid-reactive",
        "action": "SCALE_OUT",
        "k3s_weight": 70,
        "knative_weight": 30,
        "reason": "SLO violation detected",
        "p99_latency_ms": 250,
        "violation_duration_sec": 45,
    }

    success = logger.log_decision(decision)
    print(f"Logged: {success}")

    # Get stats
    stats = logger.get_decision_stats(hours=1)
    print(f"Decision stats: {stats}")


if __name__ == "__main__":
    main()
