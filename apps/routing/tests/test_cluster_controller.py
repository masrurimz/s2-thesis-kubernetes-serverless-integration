"""Tests for Algorithm 2: Cluster Controller."""

from routing.scaling.cluster_controller import ClusterController, ScalingConfig, ScalingDecision


class TestScalingConfig:
    def test_defaults(self):
        cfg = ScalingConfig()
        assert cfg.alpha == 0.04
        assert cfg.beta == 0.0
        assert cfg.buffer == 1.2
        assert cfg.min_replicas == 1
        assert cfg.max_replicas == 10


class TestComputeRequiredResources:
    def test_linear_formula(self):
        ctrl = ClusterController(config=ScalingConfig(alpha=0.01, beta=1.0))
        assert ctrl.compute_required_resources(0) == 1.0
        assert ctrl.compute_required_resources(100) == 2.0
        assert ctrl.compute_required_resources(500) == 6.0

    def test_custom_coefficients(self):
        ctrl = ClusterController(config=ScalingConfig(alpha=0.02, beta=2.0))
        assert ctrl.compute_required_resources(100) == 4.0

    def test_zero_alpha(self):
        ctrl = ClusterController(config=ScalingConfig(alpha=0.0, beta=3.0))
        assert ctrl.compute_required_resources(9999) == 3.0


class TestComputeTargetReplicas:
    def test_clamp_to_min(self):
        ctrl = ClusterController(config=ScalingConfig(alpha=0.001, beta=0.1, min_replicas=2))
        # Very low load → R is tiny, but min_replicas=2
        assert ctrl.compute_target_replicas(0) >= 2

    def test_clamp_to_max(self):
        ctrl = ClusterController(config=ScalingConfig(alpha=0.1, beta=5.0, max_replicas=8))
        # Very high load → exceeds max
        assert ctrl.compute_target_replicas(10000) == 8

    def test_buffer_applied(self):
        cfg = ScalingConfig(alpha=0.01, beta=1.0, buffer=1.5, min_replicas=1, max_replicas=100)
        ctrl = ClusterController(config=cfg)
        # R = 0.01*500 + 1.0 = 6.0, buffered = 9.0, rounded = 9
        assert ctrl.compute_target_replicas(500) == 9


class TestEvaluate:
    def test_scale_up(self):
        ctrl = ClusterController(
            config=ScalingConfig(alpha=0.01, beta=1.0),
            initial_replicas=1,
        )
        decision = ctrl.evaluate(predicted_load=500, current_replicas=1)
        assert decision.action == "SCALE_UP"
        assert decision.target_replicas > 1

    def test_scale_up_backward_compat(self):
        """evaluate() without current_replicas falls back to internal state."""
        ctrl = ClusterController(
            config=ScalingConfig(alpha=0.01, beta=1.0),
            initial_replicas=1,
        )
        decision = ctrl.evaluate(predicted_load=500)
        assert decision.action == "SCALE_UP"
        assert decision.current_replicas == 1

    def test_scale_down(self):
        ctrl = ClusterController(
            config=ScalingConfig(alpha=0.01, beta=1.0, scale_down_threshold=0.8),
            initial_replicas=8,
        )
        # Low load → target much less than 8 * 0.8
        decision = ctrl.evaluate(predicted_load=50, current_replicas=8)
        assert decision.action == "SCALE_DOWN"

    def test_maintain(self):
        ctrl = ClusterController(
            config=ScalingConfig(alpha=0.01, beta=1.0),
            initial_replicas=3,
        )
        # R = 0.01*100 + 1.0 = 2.0, buffered = 2.4, ceil = 3 → target=3 == current → MAINTAIN
        decision = ctrl.evaluate(predicted_load=100, current_replicas=3)
        assert decision.action == "MAINTAIN"

    def test_does_not_mutate_internal_state(self):
        ctrl = ClusterController(initial_replicas=1)
        ctrl.evaluate(predicted_load=500, current_replicas=1)
        assert ctrl.current_replicas == 1  # Not mutated

    def test_history_tracking(self):
        ctrl = ClusterController(initial_replicas=1)
        ctrl.evaluate(100)
        ctrl.evaluate(500)
        ctrl.evaluate(200)
        assert len(ctrl.history) == 3

    def test_decision_str(self):
        d = ScalingDecision(
            predicted_load=500.0,
            required_resources=6.0,
            target_replicas=7,
            current_replicas=2,
            action="SCALE_UP",
            reason="test",
        )
        s = str(d)
        assert "SCALE_UP" in s
        assert "500" in s
