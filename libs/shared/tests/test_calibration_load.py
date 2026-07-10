"""Tests for CalibrationConfig.load() and get_calibration() merge semantics."""

import json


import pytest
from pydantic import ValidationError

from shared.models.calibration import CALIBRATION, CalibrationConfig, get_calibration


class TestCalibrationLoad:
    """CalibrationConfig.load() classmethod — merge, validate, fail loudly."""

    def test_load_no_args_equals_defaults(self):
        cfg = CalibrationConfig.load()
        assert cfg.target_cpu_util == 0.5
        assert cfg.kp_burn == 0.5
        assert cfg.fib_n == 33

    def test_load_partial_json_merges(self, tmp_path):
        """Partial JSON overrides only specified fields, keeps defaults for rest."""
        config_file = tmp_path / "partial.json"
        config_file.write_text(json.dumps({"target_cpu_util": 0.45, "kp_burn": 0.6}))

        cfg = CalibrationConfig.load(path=config_file)
        assert cfg.target_cpu_util == 0.45
        assert cfg.kp_burn == 0.6
        # Unchanged fields keep defaults
        assert cfg.fib_n == 33
        assert cfg.proactive_trend_threshold == 3.0

    def test_load_empty_json_keeps_defaults(self, tmp_path):
        config_file = tmp_path / "empty.json"
        config_file.write_text("{}")
        cfg = CalibrationConfig.load(path=config_file)
        assert cfg.target_cpu_util == 0.5

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError, match="Calibration override not found"):
            CalibrationConfig.load(path="/nonexistent/calibration.json")

    def test_load_unknown_key_raises(self, tmp_path):
        """extra='forbid' on CalibrationConfig must reject unknown keys."""
        config_file = tmp_path / "bad.json"
        config_file.write_text(json.dumps({"target_cpu_util": 0.45, "unknown_field": 123}))
        with pytest.raises(ValidationError):
            CalibrationConfig.load(path=config_file)

    def test_load_nested_params_key_raises(self, tmp_path):
        """Nested {'params': {...}} must fail loudly, not silently drop."""
        config_file = tmp_path / "nested.json"
        config_file.write_text(json.dumps({"params": {"target_cpu_util": 0.45}}))
        with pytest.raises(ValidationError):
            CalibrationConfig.load(path=config_file)

    def test_load_invalid_type_raises(self, tmp_path):
        config_file = tmp_path / "badtype.json"
        config_file.write_text(json.dumps({"target_cpu_util": "not_a_float"}))
        with pytest.raises(ValidationError):
            CalibrationConfig.load(path=config_file)

    def test_load_non_object_json_raises(self, tmp_path):
        config_file = tmp_path / "array.json"
        config_file.write_text("[1, 2, 3]")
        with pytest.raises(TypeError, match="must be an object"):
            CalibrationConfig.load(path=config_file)

    def test_load_overrides_dict(self):
        cfg = CalibrationConfig.load(overrides={"target_cpu_util": 0.42})
        assert cfg.target_cpu_util == 0.42
        assert cfg.kp_burn == 0.5  # unchanged

    def test_load_path_and_overrides_combine(self, tmp_path):
        config_file = tmp_path / "base.json"
        config_file.write_text(json.dumps({"target_cpu_util": 0.45}))
        cfg = CalibrationConfig.load(path=config_file, overrides={"kp_burn": 0.7})
        assert cfg.target_cpu_util == 0.45
        assert cfg.kp_burn == 0.7


class TestGetCalibration:
    """get_calibration() resolves CALIBRATION_OVERRIDE env at call time."""

    def test_get_calibration_no_env_returns_defaults(self, monkeypatch):
        monkeypatch.delenv("CALIBRATION_OVERRIDE", raising=False)
        cfg = get_calibration()
        assert cfg.target_cpu_util == 0.5

    def test_get_calibration_with_env_merges(self, tmp_path, monkeypatch):
        config_file = tmp_path / "override.json"
        config_file.write_text(json.dumps({"target_cpu_util": 0.45, "kp_burn": 0.6}))
        monkeypatch.setenv("CALIBRATION_OVERRIDE", str(config_file))

        cfg = get_calibration()
        assert cfg.target_cpu_util == 0.45
        assert cfg.kp_burn == 0.6


class TestModuleLevelSingleton:
    """Module-level CALIBRATION must NEVER be mutated by env at import time."""

    def test_calibration_singleton_has_defaults(self):
        assert CALIBRATION.target_cpu_util == 0.5
        assert CALIBRATION.kp_burn == 0.5

    def test_import_with_env_does_not_mutate_singleton(self, tmp_path, monkeypatch):
        """Even if CALIBRATION_OVERRIDE is set, the module-level singleton
        keeps defaults. Only get_calibration() reads env."""
        config_file = tmp_path / "override.json"
        config_file.write_text(json.dumps({"target_cpu_util": 0.99}))
        monkeypatch.setenv("CALIBRATION_OVERRIDE", str(config_file))

        # Re-import to prove import-time block is gone
        import importlib

        import shared.models.calibration as cal_mod

        importlib.reload(cal_mod)
        assert cal_mod.CALIBRATION.target_cpu_util == 0.5  # NOT 0.99

        # But get_calibration() does see the env
        resolved = cal_mod.get_calibration()
        assert resolved.target_cpu_util == 0.99
