"""Tests for experiment logger."""
import pytest
from pathlib import Path
import tempfile
import sys

experiments_path = Path(__file__).parent.parent.parent / "experiments"
sys.path.insert(0, str(experiments_path))

from experiment_logger import ExperimentLogger


class TestExperimentLogger:
    """Tests for experiment tracking."""
    
    @pytest.fixture
    def logger(self, temp_db):
        """Create logger with temp database."""
        return ExperimentLogger(db_path=str(temp_db))
    
    def test_init_creates_database(self, temp_db):
        """Test logger creates database on init."""
        logger = ExperimentLogger(db_path=str(temp_db))
        assert temp_db.exists()
    
    def test_start_run(self, logger):
        """Test starting experiment run."""
        run_id = logger.start_run(
            scenario="s4-hybrid-predictive",
            workload="steady",
            dataset="clarknet"
        )
        
        assert isinstance(run_id, int)
        assert run_id > 0
    
    def test_start_run_with_config(self, logger):
        """Test starting run with config."""
        run_id = logger.start_run(
            scenario="s1-k8s-only",
            workload="spike",
            config={'duration': 300, 'rps': 1000}
        )
        
        run = logger.get_run(run_id)
        assert run['config'] == {'duration': 300, 'rps': 1000}
    
    def test_log_metric(self, logger):
        """Test logging a single metric."""
        run_id = logger.start_run("test-scenario", "test-workload")
        
        logger.log_metric(run_id, "p50_latency", 25.5)
        
        metrics = logger.get_run_metrics(run_id)
        assert len(metrics) == 1
        assert metrics[0]['name'] == 'p50_latency'
        assert metrics[0]['value'] == 25.5
    
    def test_log_metrics(self, logger):
        """Test logging multiple metrics."""
        run_id = logger.start_run("s1-k8s-only", "spike")
        
        logger.log_metrics(run_id, {
            'p50_latency': 25.5,
            'p99_latency': 150.0,
            'error_rate': 0.01
        })
        
        metrics = logger.get_run_metrics(run_id)
        assert len(metrics) == 3
    
    def test_end_run(self, logger):
        """Test ending run."""
        run_id = logger.start_run("s2-serverless-only", "endurance")
        logger.end_run(run_id, status="completed", notes="Test run")
        
        run = logger.get_run(run_id)
        assert run['status'] == 'completed'
        assert run['notes'] == 'Test run'
        assert run['ended_at'] is not None
    
    def test_end_run_failed(self, logger):
        """Test ending run with failed status."""
        run_id = logger.start_run("test", "test")
        logger.end_run(run_id, status="failed", notes="Connection error")
        
        run = logger.get_run(run_id)
        assert run['status'] == 'failed'
    
    def test_get_run(self, logger):
        """Test getting run details."""
        run_id = logger.start_run(
            scenario="s3-hybrid-reactive",
            workload="steady",
            dataset="clarknet"
        )
        
        run = logger.get_run(run_id)
        
        assert run['id'] == run_id
        assert run['scenario'] == 's3-hybrid-reactive'
        assert run['workload'] == 'steady'
        assert run['dataset'] == 'clarknet'
        assert run['status'] == 'running'
    
    def test_get_run_not_found(self, logger):
        """Test getting non-existent run."""
        run = logger.get_run(9999)
        assert run is None
    
    def test_scenario_summary(self, logger):
        """Test getting scenario summary."""
        for i in range(3):
            run_id = logger.start_run("s3-hybrid-reactive", "steady")
            logger.log_metric(run_id, "p99_latency", 100 + i * 10)
            logger.end_run(run_id)
        
        summary = logger.get_scenario_summary("s3-hybrid-reactive")
        
        assert "p99_latency" in summary
        assert summary["p99_latency"]["avg"] == 110.0
        assert summary["p99_latency"]["min"] == 100.0
        assert summary["p99_latency"]["max"] == 120.0
        assert summary["p99_latency"]["count"] == 3
    
    def test_scenario_summary_empty(self, logger):
        """Test scenario summary with no matching runs."""
        summary = logger.get_scenario_summary("nonexistent-scenario")
        assert summary == {}


class TestExperimentLoggerListRuns:
    """Tests for listing runs."""
    
    @pytest.fixture
    def logger(self, temp_db):
        """Create logger with sample runs."""
        log = ExperimentLogger(db_path=str(temp_db))
        
        for scenario in ['s1', 's2', 's3']:
            for workload in ['steady', 'spike']:
                run_id = log.start_run(scenario, workload)
                log.end_run(run_id, status='completed' if scenario != 's3' else 'failed')
        
        return log
    
    def test_list_all_runs(self, logger):
        """Test listing all runs."""
        runs = logger.list_runs()
        assert len(runs) == 6
    
    def test_list_runs_by_scenario(self, logger):
        """Test filtering runs by scenario."""
        runs = logger.list_runs(scenario='s1')
        assert len(runs) == 2
        assert all(r['scenario'] == 's1' for r in runs)
    
    def test_list_runs_by_workload(self, logger):
        """Test filtering runs by workload."""
        runs = logger.list_runs(workload='spike')
        assert len(runs) == 3
        assert all(r['workload'] == 'spike' for r in runs)
    
    def test_list_runs_by_status(self, logger):
        """Test filtering runs by status."""
        runs = logger.list_runs(status='completed')
        assert len(runs) == 4
        assert all(r['status'] == 'completed' for r in runs)
    
    def test_list_runs_with_limit(self, logger):
        """Test limiting run results."""
        runs = logger.list_runs(limit=3)
        assert len(runs) == 3


class TestExperimentLoggerCheckpoints:
    """Tests for checkpoint functionality."""
    
    @pytest.fixture
    def logger(self, temp_db):
        """Create logger with temp database."""
        return ExperimentLogger(db_path=str(temp_db))
    
    def test_save_checkpoint(self, logger):
        """Test saving a checkpoint."""
        run_id = logger.start_run("test", "test")
        
        checkpoint_data = {
            'weights': {'k3s': 75, 'knative': 25},
            'metrics': {'p50': 25, 'p99': 100}
        }
        
        logger.save_checkpoint(run_id, 'mid-run', checkpoint_data)


class TestExperimentLoggerExport:
    """Tests for export functionality."""
    
    @pytest.fixture
    def logger(self, temp_db):
        """Create logger with sample run."""
        log = ExperimentLogger(db_path=str(temp_db))
        run_id = log.start_run("test-scenario", "test-workload")
        log.log_metrics(run_id, {'p50': 25, 'p99': 100, 'error_rate': 0.01})
        log.end_run(run_id, status='completed')
        return log, run_id
    
    def test_export_run_to_json(self, logger):
        """Test exporting run to JSON."""
        log, run_id = logger
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            output_path = f.name
        
        result = log.export_run_to_json(run_id, output_path)
        
        assert result == output_path
        assert Path(output_path).exists()
        
        import json
        with open(output_path) as f:
            data = json.load(f)
        
        assert data['id'] == run_id
        assert len(data['metrics']) == 3
        
        Path(output_path).unlink()
    
    def test_export_nonexistent_run(self, temp_db):
        """Test exporting non-existent run."""
        log = ExperimentLogger(db_path=str(temp_db))
        
        with pytest.raises(ValueError, match="not found"):
            log.export_run_to_json(9999)
