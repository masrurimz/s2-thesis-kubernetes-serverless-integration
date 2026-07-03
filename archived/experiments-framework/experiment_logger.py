#!/usr/bin/env python3
"""
Experiment tracking and logging for thesis evaluation.
Tracks runs, metrics, and generates reproducible results.
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List
import structlog

logger = structlog.get_logger(__name__)


class ExperimentLogger:
    """Tracks experiment runs and metrics in SQLite database."""

    def __init__(self, db_path: str = "experiments/experiments.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario TEXT NOT NULL,
                workload TEXT NOT NULL,
                dataset TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                status TEXT DEFAULT 'running',
                config TEXT,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                checkpoint_name TEXT NOT NULL,
                data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES runs(id)
            )
        """)

        conn.commit()
        conn.close()

    def start_run(
        self,
        scenario: str,
        workload: str,
        dataset: str = None,
        config: dict = None,
    ) -> int:
        """Start a new experiment run, return run_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runs (scenario, workload, dataset, config)
            VALUES (?, ?, ?, ?)
        """,
            (scenario, workload, dataset, json.dumps(config) if config else None),
        )
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info("Experiment run started", run_id=run_id, scenario=scenario)
        return run_id

    def log_metric(self, run_id: int, metric_name: str, metric_value: float):
        """Log a metric for a run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO metrics (run_id, metric_name, metric_value)
            VALUES (?, ?, ?)
        """,
            (run_id, metric_name, metric_value),
        )
        conn.commit()
        conn.close()

    def log_metrics(self, run_id: int, metrics: Dict[str, float]):
        """Log multiple metrics at once."""
        for name, value in metrics.items():
            self.log_metric(run_id, name, value)

    def save_checkpoint(self, run_id: int, checkpoint_name: str, data: dict):
        """Save checkpoint data for a run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO checkpoints (run_id, checkpoint_name, data)
            VALUES (?, ?, ?)
        """,
            (run_id, checkpoint_name, json.dumps(data)),
        )
        conn.commit()
        conn.close()
        logger.info(
            "Checkpoint saved", run_id=run_id, checkpoint_name=checkpoint_name
        )

    def end_run(self, run_id: int, status: str = "completed", notes: str = None):
        """End an experiment run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE runs SET ended_at = CURRENT_TIMESTAMP, status = ?, notes = ?
            WHERE id = ?
        """,
            (status, notes, run_id),
        )
        conn.commit()
        conn.close()
        logger.info("Experiment run ended", run_id=run_id, status=status)

    def get_run(self, run_id: int) -> Optional[Dict]:
        """Get run details by ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, scenario, workload, dataset, started_at, ended_at, status, config, notes
            FROM runs WHERE id = ?
        """,
            (run_id,),
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "id": result[0],
                "scenario": result[1],
                "workload": result[2],
                "dataset": result[3],
                "started_at": result[4],
                "ended_at": result[5],
                "status": result[6],
                "config": json.loads(result[7]) if result[7] else None,
                "notes": result[8],
            }
        return None

    def get_run_metrics(self, run_id: int) -> List[Dict]:
        """Get all metrics for a run."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT metric_name, metric_value, timestamp FROM metrics
            WHERE run_id = ? ORDER BY timestamp
        """,
            (run_id,),
        )
        results = cursor.fetchall()
        conn.close()
        return [{"name": r[0], "value": r[1], "timestamp": r[2]} for r in results]

    def get_scenario_summary(self, scenario: str) -> Dict:
        """Get summary statistics for a scenario across all runs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.metric_name, AVG(m.metric_value), MIN(m.metric_value), MAX(m.metric_value), COUNT(*)
            FROM metrics m
            JOIN runs r ON m.run_id = r.id
            WHERE r.scenario = ? AND r.status = 'completed'
            GROUP BY m.metric_name
        """,
            (scenario,),
        )
        results = cursor.fetchall()
        conn.close()
        return {
            r[0]: {"avg": r[1], "min": r[2], "max": r[3], "count": r[4]}
            for r in results
        }

    def list_runs(
        self,
        scenario: str = None,
        workload: str = None,
        status: str = None,
        limit: int = 100,
    ) -> List[Dict]:
        """List runs with optional filters."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT id, scenario, workload, dataset, started_at, ended_at, status FROM runs WHERE 1=1"
        params = []

        if scenario:
            query += " AND scenario = ?"
            params.append(scenario)
        if workload:
            query += " AND workload = ?"
            params.append(workload)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "scenario": r[1],
                "workload": r[2],
                "dataset": r[3],
                "started_at": r[4],
                "ended_at": r[5],
                "status": r[6],
            }
            for r in results
        ]

    def export_run_to_json(self, run_id: int, output_path: str = None) -> str:
        """Export run with all metrics to JSON file."""
        run = self.get_run(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")

        run["metrics"] = self.get_run_metrics(run_id)

        if output_path is None:
            output_path = f"results/raw/run_{run_id}.json"

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(run, f, indent=2, default=str)

        logger.info("Run exported", run_id=run_id, path=output_path)
        return output_path
