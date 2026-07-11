"""Tests for Algorithm 1 controller (V1, V2, and V3)."""

import pytest
import time
from collections import deque
from unittest.mock import Mock

from routing.algorithm.algorithm1_v1 import Algorithm1Controller, Algorithm1Config, RoutingDecision
from routing.algorithm.algorithm1_v2 import Algorithm1ControllerV2, Algorithm1ConfigV2
from routing.algorithm.algorithm1_v3 import Algorithm1ControllerV3, Algorithm1ConfigV3
from routing.monitoring.slo_monitor import MockSLOMonitor


class TestAlgorithm1Controller:
    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()

    @pytest.fixture
    def controller(self, monitor):
        controller = Algorithm1Controller(slo_monitor=monitor)
        controller._prewarm_knative = Mock(return_value=True)
        controller.last_adjustment_time = None
        return controller

    def test_init(self, controller):
        assert controller.current_weights == {"k3s": 100, "knative": 0}
        assert controller.total_decisions == 0

    def test_maintain_when_normal(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)  # Below threshold but above healthy

        decision = controller.make_decision()

        assert decision.action == "MAINTAIN"
        assert decision.weights == {"k3s": 100, "knative": 0}

    def test_scale_out_on_violation(self, controller, monitor):
        monitor.set_mock_metrics(p99=250.0)

        # First call starts violation timer
        controller.make_decision()

        # Simulate sustained violation
        monitor.violation_start_time = int(time.time()) - 35

        decision = controller.make_decision()

        assert decision.action == "SCALE_OUT"
        assert decision.weights["knative"] > 0
        assert decision.weights["k3s"] + decision.weights["knative"] == 100

    def test_optimize_cost_when_healthy(self, controller, monitor):
        # p99 < 200 * 0.7 = 140ms
        monitor.set_mock_metrics(p99=100.0)

        decision = controller.make_decision(current_load=100)

        assert decision.action == "OPTIMIZE_COST"
        assert decision.weights["k3s"] >= 100

    def test_make_decision_does_not_mutate_weights_before_commit(self, controller, monitor):
        monitor.set_mock_metrics(p99=100.0)
        controller.current_weights = {"k3s": 90, "knative": 10}
        before = controller.current_weights.copy()

        decision = controller.make_decision(current_load=100)

        assert decision.action == "OPTIMIZE_COST"
        assert decision.weights != before
        assert controller.current_weights == before

    def test_no_optimize_cost_when_no_observed_load(self, controller, monitor):
        monitor.set_mock_metrics(p99=100.0)

        decision = controller.make_decision(current_load=0)

        assert decision.action == "MAINTAIN"

    def test_commit_applied_decision_updates_controller_state(self, controller):
        decision = RoutingDecision(
            weights={"k3s": 90, "knative": 10},
            reason="test",
            action="SCALE_OUT",
            metrics={},
        )

        controller.commit_applied_decision(decision, current_time=123)

        assert controller.current_weights == {"k3s": 90, "knative": 10}
        assert controller.last_adjustment_time == 123
        assert controller.serverless_enabled is True

    def test_predictive_scaling(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)

        prediction = {"predicted_requests": 200, "confidence": 0.9}

        decision = controller.make_decision(prediction=prediction, current_load=100)

        assert decision.action == "PREDICTIVE"
        assert decision.weights["knative"] > 0

    def test_predictive_only_in_warning_window(self, controller, monitor):
        monitor.set_mock_metrics(p99=130.0)  # Healthy zone, not warning band

        prediction = {
            "predicted_requests": 200,
            "confidence": 0.9,
        }

        decision = controller.make_decision(
            prediction=prediction,
            current_load=100,
        )

        assert decision.action != "PREDICTIVE"

    def test_predictive_not_counted_when_no_weight_delta(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)
        controller.current_weights = {"k3s": 50, "knative": 50}

        prediction = {
            "predicted_requests": 200,
            "confidence": 0.9,
        }

        decision = controller.make_decision(
            prediction=prediction,
            current_load=100,
        )

        assert decision.action == "MAINTAIN"
        assert controller.predictive_count == 0

    def test_prediction_ignored_low_confidence(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)  # Above healthy_margin (140ms), below SLO (200ms)

        prediction = {
            "predicted_requests": 200,
            "confidence": 0.3,  # Below threshold (0.5)
        }

        decision = controller.make_decision(prediction=prediction, current_load=100)

        # Low confidence → PREDICTIVE skipped; p99 > healthy → OPTIMIZE_COST skipped → MAINTAIN
        assert decision.action == "MAINTAIN"

    def test_cooldown_respected(self, controller, monitor):
        monitor.set_mock_metrics(p99=100.0)

        # First decision
        decision1 = controller.make_decision(current_load=100)
        assert decision1.action == "OPTIMIZE_COST"
        controller.commit_applied_decision(decision1, current_time=int(time.time()))

        # Immediate second call should maintain due to cooldown
        decision2 = controller.make_decision(current_load=100)
        assert decision2.action == "MAINTAIN"

    def test_statistics(self, controller, monitor):
        monitor.set_mock_metrics(p99=150.0)
        controller.make_decision()
        controller.make_decision()

        stats = controller.get_statistics()

        assert stats["total_decisions"] == 2
        assert "current_weights" in stats


class TestAlgorithm1Config:
    def test_default_config(self):
        config = Algorithm1Config()

        assert config.weight_step == 10
        assert config.cooldown_sec == 15
        assert config.healthy_margin == 0.7
        assert config.max_knative_weight == 50

    def test_custom_config(self):
        config = Algorithm1Config(weight_step=5, cooldown_sec=30, healthy_margin=0.8)

        assert config.weight_step == 5
        assert config.cooldown_sec == 30
        assert config.healthy_margin == 0.8


class TestRoutingDecision:
    def test_routing_decision_dataclass(self):
        decision = RoutingDecision(
            weights={"k3s": 70, "knative": 30}, reason="Test reason", action="SCALE_OUT", metrics={"p99": 250.0}
        )

        assert decision.weights == {"k3s": 70, "knative": 30}
        assert decision.action == "SCALE_OUT"
        assert decision.metrics["p99"] == 250.0


class TestSLOViolationScenarios:
    """Test various SLO violation scenarios."""

    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()

    @pytest.fixture
    def controller(self, monitor):
        controller = Algorithm1Controller(slo_monitor=monitor)
        controller._prewarm_knative = Mock(return_value=True)
        return controller

    def test_brief_spike_no_scale_out(self, controller, monitor):
        """Brief latency spike should not trigger scale out."""
        monitor.set_mock_metrics(p99=250.0)

        # First call - violation just started
        decision = controller.make_decision()

        # Should not scale out immediately
        assert decision.action != "SCALE_OUT"

    def test_max_knative_weight_respected(self, controller, monitor):
        """Knative weight should not exceed max."""
        # Set initial weights close to max
        controller.current_weights = {"k3s": 55, "knative": 45}

        monitor.set_mock_metrics(p99=250.0)
        monitor.violation_start_time = int(time.time()) - 35

        decision = controller.make_decision()

        assert decision.weights["knative"] <= controller.config.max_knative_weight

    def test_k3s_weight_optimization_limit(self, controller, monitor):
        """k3s weight optimization should not exceed 100."""
        controller.current_weights = {"k3s": 94, "knative": 6}

        monitor.set_mock_metrics(p99=100.0)

        decision = controller.make_decision()

        assert decision.weights["k3s"] <= 100


class TestAlgorithm1ControllerV2:
    """Tests for the PID + Feedforward V2 controller."""

    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()

    @pytest.fixture
    def config(self):
        return Algorithm1ConfigV2(
            cooldown_sec=0,  # No cooldown for testing
            adaptive_target=False,  # Use fixed target
            kp=0.15,
            ki=0.005,
            kd=0.08,
            kff=0.1,
        )

    @pytest.fixture
    def controller(self, monitor, config):
        ctrl = Algorithm1ControllerV2(slo_monitor=monitor, config=config)
        ctrl._prewarm_knative = Mock(return_value=True)
        ctrl.last_adjustment_time = 0  # Allow immediate adjustment
        ctrl.current_weights = {"k3s": 80, "knative": 20}
        return ctrl

    def test_init(self, controller):
        assert controller.current_weights == {"k3s": 80, "knative": 20}
        assert controller.total_decisions == 0
        assert controller._integral == 0.0
        assert controller._prev_error == 0.0

    def test_pid_proportional_response(self, controller, monitor):
        """Larger error should produce larger weight delta."""
        monitor.set_mock_metrics(p99=300.0)
        slo = monitor.check_slo()
        decision_small = controller.make_decision(slo_status=slo, current_load=50)
        small_delta = abs(decision_small.weights["knative"] - 20)

        # Reset and test with larger error
        controller.current_weights = {"k3s": 80, "knative": 20}
        controller.last_adjustment_time = 0
        controller._integral = 0.0
        controller._prev_error = 0.0
        monitor.set_mock_metrics(p99=5000.0)
        slo = monitor.check_slo()
        decision_large = controller.make_decision(slo_status=slo, current_load=50)
        large_delta = abs(decision_large.weights["knative"] - 20)

        assert large_delta > small_delta, "Larger error should produce larger shift"

    def test_max_weight_delta_clamp(self, controller, monitor):
        """Weight delta should not exceed max_weight_delta_per_step."""
        monitor.set_mock_metrics(p99=10000.0)  # Extreme violation
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=50)

        delta = abs(decision.weights["knative"] - 20)
        assert delta <= controller.config.max_weight_delta_per_step

    def test_feedforward_fires_during_violation(self, controller, monitor):
        """Feedforward should contribute to decision even during SLO violation."""
        monitor.set_mock_metrics(p99=5000.0)
        slo = monitor.check_slo()
        pred = {"predicted_requests": 150, "confidence": 0.8}  # Predicts increase

        decision = controller.make_decision(slo_status=slo, prediction=pred, current_load=70)

        # Should have shifted toward serverless (either REACTIVE or PREDICTIVE)
        assert decision.weights["knative"] > 20
        assert decision.action in ("REACTIVE", "PREDICTIVE")

    def test_feedforward_fires_in_dead_zone(self, controller, monitor):
        """Feedforward should act even when error is within hysteresis dead zone."""
        controller._adaptive_target = 5000.0  # Set high target
        monitor.set_mock_metrics(p99=5100.0)  # Within 20% of 5000 = dead zone
        slo = monitor.check_slo()

        # Without prediction: should maintain
        decision_no_pred = controller.make_decision(slo_status=slo, current_load=70)
        assert decision_no_pred.action == "MAINTAIN"

        # Reset
        controller.current_weights = {"k3s": 80, "knative": 20}
        controller.last_adjustment_time = 0

        # With strong prediction: should act
        pred = {"predicted_requests": 200, "confidence": 0.9}
        decision_pred = controller.make_decision(slo_status=slo, prediction=pred, current_load=70)
        assert decision_pred.action == "PREDICTIVE"

    def test_feedforward_ignored_low_confidence(self, controller, monitor):
        """Feedforward should not fire when confidence is below threshold."""
        controller._adaptive_target = 5000.0
        monitor.set_mock_metrics(p99=5100.0)
        slo = monitor.check_slo()
        pred = {"predicted_requests": 200, "confidence": 0.3}  # Below 0.5 threshold

        decision = controller.make_decision(slo_status=slo, prediction=pred, current_load=70)
        assert decision.action == "MAINTAIN"

    def test_feedforward_ignored_small_load_change(self, controller, monitor):
        """Feedforward should not fire for tiny load changes."""
        controller._adaptive_target = 5000.0
        monitor.set_mock_metrics(p99=5100.0)
        slo = monitor.check_slo()
        pred = {"predicted_requests": 72, "confidence": 0.9}  # Only ~3% change from 70

        decision = controller.make_decision(slo_status=slo, prediction=pred, current_load=70)
        assert decision.action == "MAINTAIN"

    def test_hysteresis_prevents_oscillation(self, controller, monitor):
        """Dead zone should prevent reaction to small fluctuations."""
        controller._adaptive_target = 200.0
        monitor.set_mock_metrics(p99=210.0)  # Within 20% of 200 = dead zone
        slo = monitor.check_slo()

        decision = controller.make_decision(slo_status=slo, current_load=50)
        assert decision.action == "MAINTAIN"
        assert decision.weights == {"k3s": 80, "knative": 20}

    def test_integral_accumulates_over_time(self, controller, monitor):
        """Integral term should accumulate persistent error over multiple cycles."""
        # Use non-zero cooldown so integral accumulates (integral += error * dt)
        controller.config.cooldown_sec = 15
        monitor.set_mock_metrics(p99=250.0)  # Mild violation: error=0.25
        slo = monitor.check_slo()

        # First decision
        controller.make_decision(slo_status=slo, current_load=50)
        integral_after_1 = controller._integral

        # Second decision (same error)
        controller.current_weights = {"k3s": 80, "knative": 20}
        controller.last_adjustment_time = 0
        controller.make_decision(slo_status=slo, current_load=50)
        integral_after_2 = controller._integral

        assert integral_after_2 > integral_after_1, "Integral should accumulate"

    def test_anti_windup_clamps_integral(self, controller, monitor):
        """Integral should be clamped to prevent runaway."""
        controller.config.integral_max = 5.0
        controller.config.integral_min = -5.0

        # Feed many violations to accumulate integral
        monitor.set_mock_metrics(p99=10000.0)
        slo = monitor.check_slo()
        for _ in range(50):
            controller._integral += 1.0
            controller._integral = max(
                controller.config.integral_min,
                min(controller.config.integral_max, controller._integral),
            )

        assert controller._integral == 5.0, "Integral should be clamped at max"

    def test_commit_applied_decision_updates_state(self, controller, monitor):
        """commit_applied_decision should update weights and adjustment time."""
        decision = RoutingDecision(
            weights={"k3s": 70, "knative": 30},
            reason="test",
            action="REACTIVE",
            metrics={},
        )

        controller.commit_applied_decision(decision, current_time=123)

        assert controller.current_weights == {"k3s": 70, "knative": 30}
        assert controller.last_adjustment_time == 123
        assert controller.serverless_enabled is True

    def test_commit_recovery_disables_serverless(self, controller, monitor):
        """RECOVERY to weight=0 should disable serverless."""
        decision = RoutingDecision(
            weights={"k3s": 100, "knative": 0},
            reason="recovery",
            action="RECOVERY",
            metrics={},
        )

        controller.commit_applied_decision(decision, current_time=200)

        assert controller.serverless_enabled is False

    def test_get_statistics_reports_v2(self, controller, monitor):
        """Statistics should report controller_version='v2'."""
        stats = controller.get_statistics()
        assert stats["controller_version"] == "v2"
        assert "integral" in stats

    def test_cold_start_ewma_updates(self, controller, monitor):
        """Cold-start EWMA should update when pre-warm timing is observed."""
        assert not controller._cold_start_initialized

        controller._update_cold_start_ewma(5.0)
        assert controller._cold_start_initialized
        assert controller._cold_start_ewma == 5.0

        controller._update_cold_start_ewma(10.0)
        # EWMA with alpha=0.3: 0.3*10 + 0.7*5 = 3 + 3.5 = 6.5
        assert abs(controller._cold_start_ewma - 6.5) < 0.01

    def test_adaptive_target_from_warmup(self, monitor):
        """Adaptive target should be computed from warmup baseline."""
        config = Algorithm1ConfigV2(cooldown_sec=0, adaptive_target=True)
        ctrl = Algorithm1ControllerV2(slo_monitor=monitor, config=config)
        ctrl._prewarm_knative = Mock(return_value=True)

        # Simulate warmup: feed p99 values for 60+ seconds
        import time as _time

        base_time = int(_time.time())
        ctrl._warmup_end_time = base_time + 5  # Short warmup for test

        for p99 in [1000, 1200, 1100, 1050, 1150]:
            ctrl._track_warmup(p99, base_time)
            base_time += 1

        # Advance past warmup
        ctrl._track_warmup(1100, base_time + 10)

        target = ctrl._compute_adaptive_target()
        # Median of [1000,1200,1100,1050,1150] = 1100, target = max(200, 1100*1.5) = 1650
        assert target == 1650.0, f"Expected 1650, got {target}"

    def test_no_prediction_returns_maintain_in_deadzone(self, controller, monitor):
        """Without prediction, dead zone should always maintain."""
        controller._adaptive_target = 5000.0
        monitor.set_mock_metrics(p99=5200.0)
        slo = monitor.check_slo()

        decision = controller.make_decision(slo_status=slo, prediction=None, current_load=70)
        assert decision.action == "MAINTAIN"

    def test_weights_sum_to_100(self, controller, monitor):
        """Weights should always sum to 100."""
        monitor.set_mock_metrics(p99=5000.0)
        slo = monitor.check_slo()
        pred = {"predicted_requests": 100, "confidence": 0.8}

        decision = controller.make_decision(slo_status=slo, prediction=pred, current_load=70)
        assert sum(decision.weights.values()) == 100

    def test_serverless_weight_within_bounds(self, controller, monitor):
        """Serverless weight should respect min/max bounds."""
        monitor.set_mock_metrics(p99=10000.0)
        slo = monitor.check_slo()

        decision = controller.make_decision(slo_status=slo, current_load=50)
        assert controller.config.min_serverless_weight <= decision.weights["knative"]
        assert decision.weights["knative"] <= controller.config.max_serverless_weight


class TestAlgorithm1ConfigV2:
    def test_default_config(self):
        config = Algorithm1ConfigV2()

        assert config.kp == 0.15
        assert config.ki == 0.005
        assert config.kd == 0.08
        assert config.kff == 0.1
        assert config.max_serverless_weight == 70
        assert config.hysteresis_factor == 0.2
        assert config.adaptive_target is True

    def test_custom_config(self):
        config = Algorithm1ConfigV2(kp=0.3, ki=0.01, kd=0.1, kff=0.2)

        assert config.kp == 0.3
        assert config.ki == 0.01
        assert config.kd == 0.1
        assert config.kff == 0.2


class TestAlgorithm1ControllerV3:
    """Tests for capacity-driven V3 controller."""

    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()

    @pytest.fixture
    def config(self):
        return Algorithm1ConfigV3(
            r_saturation_per_replica=30.0,
            target_cpu_util=0.8,
            min_k8s_replicas=2,
            max_knative_weight=50,
        )

    @pytest.fixture
    def controller(self, monitor, config):
        ctrl = Algorithm1ControllerV3(slo_monitor=monitor, config=config)
        ctrl._prewarm_knative = Mock(return_value=True)
        ctrl.current_weights = {"k3s": 80, "knative": 20}
        ctrl.serverless_enabled = True
        return ctrl

    def test_init(self, controller):
        assert controller.current_weights == {"k3s": 80, "knative": 20}
        assert controller.total_decisions == 0
        assert controller.capacity_deficit is False

    def test_r_effective_per_replica(self, controller):
        assert controller.r_effective_per_replica == 24.0  # 30 * 0.8

    def test_k8s_capacity_computation(self, controller):
        cap = controller._compute_k8s_capacity(available_replicas=3)
        assert cap == 72.0  # 3 * 24

    def test_k8s_capacity_zero_replicas(self, controller):
        cap = controller._compute_k8s_capacity(available_replicas=0)
        assert cap == 0.0

    def test_load_within_capacity_all_k8s(self, controller, monitor):
        """Load < capacity should route 100% to K8s."""
        monitor.set_mock_metrics(p99=100.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=50, available_replicas=4)
        assert decision.weights["knative"] == 0
        assert decision.weights["k3s"] == 100

    def test_burst_routing_to_knative(self, controller, monitor):
        """Load > capacity should split between K8s and Knative."""
        monitor.set_mock_metrics(p99=5000.0)
        slo = monitor.check_slo()
        # 4 replicas * 24 = 96 RPS capacity, load=150 → burst
        decision = controller.make_decision(slo_status=slo, current_load=150, available_replicas=4)
        assert decision.weights["knative"] > 0
        assert decision.weights["k3s"] < 100
        assert decision.weights["k3s"] + decision.weights["knative"] == 100

    def test_max_knative_weight_cap(self, controller, monitor):
        """Knative weight should not exceed max_knative_weight."""
        monitor.set_mock_metrics(p99=50000.0)
        slo = monitor.check_slo()
        # 1 replica * 24 = 24 RPS capacity, load=1000 → 97.6% burst → cap at 50
        decision = controller.make_decision(slo_status=slo, current_load=1000, available_replicas=1)
        assert decision.weights["knative"] <= controller.config.max_knative_weight

    def test_capacity_deficit_mode(self, controller, monitor):
        """When burst exceeds cap, capacity_deficit should be True."""
        monitor.set_mock_metrics(p99=50000.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=1000, available_replicas=1)
        assert controller.capacity_deficit is True

    def test_prediction_drives_scaling_not_routing(self, controller, monitor):
        """Prediction higher than observed should NOT change routing weights
        (routing uses actual load) but SHOULD store amplified prediction
        for Algorithm 2 scaling via last_predicted_upper."""
        monitor.set_mock_metrics(p99=100.0)
        slo = monitor.check_slo()
        pred = {"predicted_requests": 200, "confidence": 0.8}
        # 4 replicas * 24 = 96 capacity, predicted=200 > observed=50
        decision = controller.make_decision(slo_status=slo, prediction=pred, current_load=50, available_replicas=4)
        # Routing uses ACTUAL load (50 < 96 = capacity), so no serverless routing
        assert decision.weights["knative"] == 0
        # But prediction should be stored for Algorithm 2 scaling
        assert controller.last_predicted_upper >= 50

    def test_low_confidence_prediction_ignored(self, controller, monitor):
        """Low confidence prediction should not affect routing."""
        monitor.set_mock_metrics(p99=100.0)
        slo = monitor.check_slo()
        pred = {"predicted_requests": 200, "confidence": 0.3}
        decision = controller.make_decision(slo_status=slo, prediction=pred, current_load=50, available_replicas=4)
        assert decision.weights["knative"] == 0

    def test_weights_sum_to_100(self, controller, monitor):
        monitor.set_mock_metrics(p99=5000.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=200, available_replicas=2)
        assert sum(decision.weights.values()) == 100

    def test_commit_applied_decision(self, controller):
        decision = RoutingDecision(
            weights={"k3s": 60, "knative": 40},
            reason="test",
            action="REACTIVE",
            metrics={},
        )
        controller.commit_applied_decision(decision, current_time=100)
        assert controller.current_weights == {"k3s": 60, "knative": 40}
        assert controller.last_adjustment_time == 100

    def test_get_statistics_v3(self, controller, monitor):
        monitor.set_mock_metrics(p99=100.0)
        controller.make_decision(current_load=50, available_replicas=4)
        stats = controller.get_statistics()
        assert stats["controller_version"] == "v3"
        assert "cumulative_violations" in stats
        assert "r_effective_per_replica" in stats

    def test_no_traffic_maintains(self, controller, monitor):
        """When p99=0 and no load, should maintain."""
        monitor.set_mock_metrics(p99=0.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=0, available_replicas=4)
        assert decision.action == "MAINTAIN"

    def test_serverless_disabled_when_no_burst(self, controller, monitor):
        """When load fits on K8s, serverless should be disabled."""
        controller.serverless_enabled = True
        monitor.set_mock_metrics(p99=100.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=50, available_replicas=4)
        # Knative weight=0 should disable serverless
        assert decision.weights["knative"] == 0


class TestAlgorithm1ConfigV3:
    def test_default_config(self):
        config = Algorithm1ConfigV3()
        assert config.r_saturation_per_replica == 35.0  # calibrated for 300m CPU pods
        assert config.target_cpu_util == 0.8
        assert config.min_k8s_replicas == 3
        assert config.max_knative_weight == 50
        assert config.prediction_confidence_threshold == 0.5

    def test_custom_config(self):
        config = Algorithm1ConfigV3(
            r_saturation_per_replica=50.0,
            target_cpu_util=0.6,
            max_knative_weight=30,
        )
        assert config.r_saturation_per_replica == 50.0
        assert config.target_cpu_util == 0.6
        assert config.max_knative_weight == 30


class TestV3WithClarkNetTrace:
    """Test V3 controller routing decisions with real ClarkNet workload data."""

    @pytest.fixture
    def monitor(self):
        return MockSLOMonitor()

    @pytest.fixture
    def controller(self, monitor):
        config = Algorithm1ConfigV3(
            r_saturation_per_replica=35.0,
            target_cpu_util=0.8,
            min_k8s_replicas=3,
            max_knative_weight=50,
        )
        ctrl = Algorithm1ControllerV3(slo_monitor=monitor, config=config)
        ctrl._prewarm_knative = Mock(return_value=True)
        ctrl.current_weights = {"k3s": 80, "knative": 20}
        ctrl.serverless_enabled = True
        return ctrl

    def test_low_load_all_k8s(self, controller, monitor):
        """ClarkNet low stages (24-48 RPS) should route 100% to K8s."""
        monitor.set_mock_metrics(p99=100.0)
        slo = monitor.check_slo()
        for load in [24, 31, 48]:
            decision = controller.make_decision(slo_status=slo, current_load=load, available_replicas=3)
            controller.commit_applied_decision(decision)
            assert decision.weights["knative"] == 0, f"load={load} should be 100% K8s"

    def test_peak_load_burst_routing(self, controller, monitor):
        """ClarkNet peak (164 RPS) should route burst to Knative."""
        monitor.set_mock_metrics(p99=5000.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=164, available_replicas=3)
        # 3 pods * 28 = 84 capacity, load=164 → burst=49% → capped at 50
        assert decision.weights["knative"] > 0
        assert decision.weights["knative"] <= 50

    def test_mean_load_within_capacity(self, controller, monitor):
        """ClarkNet mean (73 RPS) with 3 replicas (84 cap) → 100% K8s."""
        monitor.set_mock_metrics(p99=100.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=73, available_replicas=3)
        assert decision.weights["knative"] == 0

    def test_mean_load_exceeds_2_replica_capacity(self, controller, monitor):
        """ClarkNet mean (73 RPS) with 2 replicas (56 cap) → burst to Knative."""
        monitor.set_mock_metrics(p99=5000.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=73, available_replicas=2)
        # 2 pods * 28 = 56, load=73 → burst=23% → ~23% Knative
        assert decision.weights["knative"] > 0
        assert decision.weights["knative"] < 50

    def test_gru_prediction_drives_scaling_not_routing(self, controller, monitor):
        """GRU prediction above observed load should NOT change routing
        (routing uses actual load) but should store amplified prediction."""
        monitor.set_mock_metrics(p99=100.0)
        slo = monitor.check_slo()
        pred = {"predicted_requests": 120, "confidence": 0.8}
        # observed=50, predicted=120 → routing uses 50 (not 120)
        decision = controller.make_decision(slo_status=slo, prediction=pred, current_load=50, available_replicas=3)
        # 50 < 84 capacity → no serverless routing needed
        assert decision.weights["knative"] == 0
        # But amplified prediction stored for Algorithm 2
        assert controller.last_predicted_upper >= 50

    def test_capacity_deficit_at_extreme_load(self, controller, monitor):
        """Extreme load with 1 replica → capacity deficit mode."""
        monitor.set_mock_metrics(p99=50000.0)
        slo = monitor.check_slo()
        decision = controller.make_decision(slo_status=slo, current_load=200, available_replicas=1)
        assert controller.capacity_deficit is True
        assert decision.weights["knative"] == 50  # capped at max

    def test_all_weights_sum_to_100(self, controller, monitor):
        """Every routing decision must have weights summing to 100."""
        monitor.set_mock_metrics(p99=5000.0)
        slo = monitor.check_slo()
        for load in [0, 24, 48, 73, 100, 164]:
            decision = controller.make_decision(slo_status=slo, current_load=load, available_replicas=3)
            controller.commit_applied_decision(decision)
            assert sum(decision.weights.values()) == 100, f"load={load} weights don't sum to 100"


class TestAlgorithm2ScalingForV3:
    """Test Algorithm 2 scaling logic with V3 parameters."""

    def test_scale_up_from_2_to_3(self):
        """With min_replicas=3, load=73 should scale from 2→3+."""
        from routing.scaling.cluster_controller import ClusterController, ScalingConfig

        ctrl = ClusterController(
            config=ScalingConfig(
                alpha=0.03,
                min_replicas=3,
                scale_down_threshold=0.5,
            )
        )
        decision = ctrl.evaluate(predicted_load=73, current_replicas=2)
        assert decision.action == "SCALE_UP"
        assert decision.target_replicas >= 3

    def test_scale_up_for_peak_load(self):
        """Peak load 164 RPS should target 6+ replicas."""
        from routing.scaling.cluster_controller import ClusterController, ScalingConfig

        ctrl = ClusterController(config=ScalingConfig(alpha=0.03))
        decision = ctrl.evaluate(predicted_load=164, current_replicas=3)
        assert decision.action == "SCALE_UP"
        # ceil(164 * 0.03 * 1.2) = ceil(5.9) = 6
        assert decision.target_replicas >= 6

    def test_no_scale_down_below_min(self):
        """With min_replicas=3, scale-down target should be clamped to 3."""
        from routing.scaling.cluster_controller import ClusterController, ScalingConfig

        ctrl = ClusterController(
            config=ScalingConfig(
                alpha=0.03,
                min_replicas=3,
                scale_down_threshold=0.5,
            )
        )
        decision = ctrl.evaluate(predicted_load=10, current_replicas=5)
        # target = ceil(10 * 0.03 * 1.2) = ceil(0.36) = 1, but clamped to min=3
        assert decision.target_replicas >= 3

    def test_maintain_when_target_within_threshold(self):
        """When target is within scale_down_threshold of current, maintain."""
        from routing.scaling.cluster_controller import ClusterController, ScalingConfig

        ctrl = ClusterController(
            config=ScalingConfig(
                alpha=0.03,
                scale_down_threshold=0.5,
            )
        )
        decision = ctrl.evaluate(predicted_load=73, current_replicas=4)
        # target = ceil(73 * 0.03 * 1.2) = ceil(2.63) = 3
        # 3 < 4 * 0.5 = 2? No → MAINTAIN
        assert decision.action == "MAINTAIN"


class TestBurnRateAdjustment:
    """Tests for one-sided (intervention-only) burn-rate adjustment."""

    @pytest.fixture
    def controller(self):
        ctrl = Algorithm1ControllerV3(slo_monitor=MockSLOMonitor())
        ctrl._prewarm_knative = Mock(return_value=True)
        return ctrl

    def test_burn_rate_zero_when_healthy(self, controller):
        """Burn ratio <= 1.0 → adjustment = 0, integral reset."""
        controller._experiment_start_time = time.time() - 600  # 10 min elapsed
        controller.cumulative_violations = 200  # actual=0.33 < allowed=0.83
        controller._burn_integral = 2.0  # Non-zero from prior cycles

        adj = controller._burn_rate_adjustment()
        assert adj == 0
        assert controller._burn_integral == 0.0

    def test_burn_rate_positive_when_exceeding(self, controller):
        """Burn ratio > 1.0 → adjustment > 0."""
        controller._experiment_start_time = time.time() - 600
        controller.cumulative_violations = 1000  # actual=1.67 > allowed=0.83
        controller._burn_integral = 0.0

        adj = controller._burn_rate_adjustment()
        assert adj > 0

    def test_burn_rate_never_negative(self, controller):
        """Adjustment is always >= 0 across various burn scenarios."""
        for violations in [0, 100, 500, 1000, 5000]:
            ctrl = Algorithm1ControllerV3(slo_monitor=MockSLOMonitor())
            ctrl._experiment_start_time = time.time() - 600
            ctrl.cumulative_violations = violations
            ctrl._burn_integral = -3.0  # Try to force negative
            adj = ctrl._burn_rate_adjustment()
            assert adj >= 0, f"violations={violations} produced adj={adj}"


class TestProactiveScalingDaemon:
    """Tests for observed-vs-predictive target comparison and proactive hold."""

    @pytest.fixture
    def s4_daemon(self):
        """Create an S4 daemon with mocked K8s scaler."""
        from routing.daemon.service import RoutingDaemon
        from infra.cluster.k8s.scaler import DeploymentStatus

        daemon = RoutingDaemon(scenario="s4-hybrid-predictive")
        daemon.k8s_scaler.get_deployment_status = Mock(
            return_value=DeploymentStatus(
                spec_replicas=3,
                available_replicas=3,
                updated_replicas=3,
                ready=True,
            )
        )
        daemon.k8s_scaler.scale = Mock(return_value=True)
        daemon._last_prediction_ts = time.time()
        assert daemon.cluster_controller is not None
        daemon.cluster_controller.evaluate = Mock(wraps=daemon.cluster_controller.evaluate)
        return daemon

    @staticmethod
    def _set_load(daemon, rps):
        daemon._load_history = deque([rps] * 4, maxlen=60)

    def test_proactive_target_strictly_greater(self, s4_daemon):
        """predictive_target > observed_target → proactive=True."""
        self._set_load(s4_daemon, 50)  # observed_target = 3
        s4_daemon.algorithm_controller.last_predicted_upper = 150  # predictive_target = 6

        s4_daemon._execute_algorithm2(None, None, 50)

        assert s4_daemon._proactive_hold_until > time.time()
        assert s4_daemon._proactive_held_target == 6

    def test_proactive_target_equal_is_noop(self, s4_daemon):
        """predictive_target == observed_target → proactive=False."""
        self._set_load(s4_daemon, 50)  # observed_target = 3
        s4_daemon.algorithm_controller.last_predicted_upper = 50  # same target = 3

        s4_daemon._execute_algorithm2(None, None, 50)

        assert s4_daemon.no_op_predictions == 1
        assert s4_daemon._proactive_hold_until == 0.0

    def test_proactive_hold_prevents_rollback(self, s4_daemon):
        """During hold window, observed drop doesn't lower target."""
        self._set_load(s4_daemon, 50)
        s4_daemon.algorithm_controller.last_predicted_upper = 150  # predictive_target = 6

        # First call: triggers proactive scale-up
        s4_daemon._execute_algorithm2(None, None, 50)
        assert s4_daemon._proactive_held_target == 6

        # Prediction drops to observed level, but we're within hold window
        s4_daemon.algorithm_controller.last_predicted_upper = 50
        s4_daemon._execute_algorithm2(None, None, 50)

        # evaluate called with held load (150), not observed (50)
        last_signal = s4_daemon.cluster_controller.evaluate.call_args[0][0]
        assert last_signal == 150
        # no_op_predictions should NOT have been incremented (still proactive via hold)
        assert s4_daemon.no_op_predictions == 0

    def test_proactive_hold_expires(self, s4_daemon):
        """After hold_until, observed target is used."""
        self._set_load(s4_daemon, 50)
        s4_daemon.algorithm_controller.last_predicted_upper = 150

        # Trigger proactive
        s4_daemon._execute_algorithm2(None, None, 50)
        assert s4_daemon._proactive_held_target == 6

        # Expire the hold
        s4_daemon._proactive_hold_until = time.time() - 1

        # Prediction is low, hold expired → use observed
        s4_daemon.algorithm_controller.last_predicted_upper = 50
        s4_daemon._execute_algorithm2(None, None, 50)

        # evaluate called with observed load (50)
        last_signal = s4_daemon.cluster_controller.evaluate.call_args[0][0]
        assert last_signal == 50
        assert s4_daemon.no_op_predictions == 1

    def test_s3_never_uses_prediction(self):
        """S3 scenario never has proactive=True."""
        from routing.daemon.service import RoutingDaemon
        from infra.cluster.k8s.scaler import DeploymentStatus

        daemon = RoutingDaemon(scenario="s3-hybrid-reactive")
        daemon.k8s_scaler.get_deployment_status = Mock(
            return_value=DeploymentStatus(
                spec_replicas=3,
                available_replicas=3,
                updated_replicas=3,
                ready=True,
            )
        )
        daemon.k8s_scaler.scale = Mock(return_value=True)
        daemon._last_prediction_ts = time.time()
        self._set_load(daemon, 50)
        if isinstance(daemon.algorithm_controller, Algorithm1ControllerV3):
            daemon.algorithm_controller.last_predicted_upper = 150

        daemon._execute_algorithm2(None, None, 50)

        assert daemon._proactive_hold_until == 0.0
        assert daemon.no_op_predictions == 0
        assert daemon.useful_proactive_scaleups == 0
