"""The prediction seam: a client can be substituted, and the protocol is honoured.

RoutingDaemon builds a GRUClient today. That default stays; what changes is that a
caller may supply the client, which is what a test or a different predictor needs.
"""

from unittest.mock import patch

import pytest

from routing.clients.gru_client import GRUClient
from routing.daemon.service import RoutingDaemon
from shared.models.prediction import PredictionResult
from shared.protocols.prediction import PredictionClient


def _result(predicted: float = 42.0) -> PredictionResult:
    return PredictionResult(
        predicted_requests=predicted,
        confidence=0.9,
        horizon_values=[int(predicted)],
        latency_ms=1.0,
    )


class FakePredictor:
    """A prediction client with no network and no server."""

    def __init__(self, value: float = 42.0):
        self.value = value
        self.calls: list[tuple[float, ...]] = []

    def predict(self, history, horizon: int = 5) -> PredictionResult:
        self.calls.append(tuple(history))
        return _result(self.value)

    def is_healthy(self) -> bool:
        return True


def test_daemon_defaults_to_the_gru_client():
    daemon = RoutingDaemon(scenario="s4-hybrid-predictive")

    assert isinstance(daemon.gru_client, GRUClient)


def test_daemon_uses_an_injected_client():
    fake = FakePredictor(value=250.0)

    daemon = RoutingDaemon(scenario="s4-hybrid-predictive", prediction_client=fake)

    assert daemon.gru_client is fake
    assert daemon.gru_client.predict([1.0, 2.0, 3.0]).predicted_requests == 250
    assert fake.calls == [(1.0, 2.0, 3.0)]


def test_injected_client_satisfies_the_protocol_statically():
    """ty proves the conformance; this pins the members the daemon relies on."""
    fake: PredictionClient = FakePredictor()

    assert fake.is_healthy() is True
    assert fake.predict([1.0]).success is True


@pytest.mark.parametrize("history", [(1.0, 2.0), [1.0, 2.0]])
def test_gru_client_takes_any_sequence(history):
    """The protocol's history is a Sequence, so a tuple caller is not a type error."""
    client = GRUClient(base_url="http://localhost:9")

    with patch("routing.clients.gru_client.requests.post") as post:
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "predicted_requests": 12,
            "confidence": 0.8,
            "horizon_values": [12],
            "latency_ms": 1.0,
        }
        result = client.predict(history)

    assert isinstance(result, PredictionResult)
    assert result.predicted_requests == 12
