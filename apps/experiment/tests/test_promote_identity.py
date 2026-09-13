"""Promotion identity: the artifact a study names is the artifact that lands.

On 2026-09-12 the synthetic-arm artifact was promoted although its study had
recorded no winner, and both September paired batches then ran with a model
nobody had selected. These tests pin the two checks that were missing: the
promotion refuses a file whose bytes do not hash to the winner's recorded
sha256, and a run manifest's recorded hash can be compared against whatever is
deployed on disk.
"""

import hashlib
import json
from pathlib import Path

import pytest
from experiment.tuning import gru_study


@pytest.fixture()
def deployed_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point DEPLOYED_ARTIFACT at a scratch file seeded with stale bytes."""
    target = tmp_path / "gru_model.pt"
    target.write_bytes(b"previous model")
    monkeypatch.setattr(gru_study, "DEPLOYED_ARTIFACT", target)
    return target


def _winner(tmp_path: Path, payload: bytes, name: str = "winner.pt") -> dict[str, str]:
    artifact = tmp_path / name
    artifact.write_bytes(payload)
    return {
        "artifact": str(artifact),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def test_promotion_copies_the_winner_and_backs_up_the_previous(deployed_path: Path, tmp_path: Path) -> None:
    """A matching hash promotes; the old bytes survive beside it."""
    winner = _winner(tmp_path, b"the clarknet winner")

    result = gru_study.promote_winner(winner)

    assert deployed_path.read_bytes() == b"the clarknet winner"
    assert result["sha256"] == winner["sha256"]
    backup = Path(result["backup"])
    assert backup.exists()
    assert backup.read_bytes() == b"previous model"


def test_promotion_refuses_a_file_that_does_not_match_the_record(deployed_path: Path, tmp_path: Path) -> None:
    """The 2026-09-12 failure: the promoted file is not the recorded winner."""
    winner = _winner(tmp_path, b"some other model")
    winner["sha256"] = hashlib.sha256(b"the recorded winner").hexdigest()

    with pytest.raises(ValueError, match="refusing to promote"):
        gru_study.promote_winner(winner)

    assert deployed_path.read_bytes() == b"previous model"


def test_promotion_refuses_a_missing_artifact(deployed_path: Path, tmp_path: Path) -> None:
    """A winner record pointing at nothing fails before any copy happens."""
    winner = {
        "artifact": str(tmp_path / "absent.pt"),
        "sha256": hashlib.sha256(b"irrelevant").hexdigest(),
    }

    with pytest.raises(FileNotFoundError):
        gru_study.promote_winner(winner)

    assert deployed_path.read_bytes() == b"previous model"


def test_verify_deployed_artifact_compares_a_manifest_against_disk(deployed_path: Path, tmp_path: Path) -> None:
    """A batch's verdict is attributed to the model its manifest recorded."""
    deployed_path.write_bytes(b"the clarknet winner")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "predictor": {
                    "reported": {
                        "artifact_sha256": hashlib.sha256(b"the clarknet winner").hexdigest(),
                    }
                }
            }
        )
    )

    result = gru_study.verify_deployed_artifact(manifest)
    assert result["match"] == "yes"

    manifest.write_text(
        json.dumps(
            {
                "predictor": {
                    "reported": {
                        "artifact_sha256": hashlib.sha256(b"the synthetic winner").hexdigest(),
                    }
                }
            }
        )
    )
    result = gru_study.verify_deployed_artifact(manifest)
    assert result["match"] == "no"
    assert result["recorded_sha256"] != result["deployed_sha256"]


def test_verify_deployed_artifact_raises_without_a_recorded_hash(deployed_path: Path, tmp_path: Path) -> None:
    """A manifest with no predictor block cannot be attributed."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"scenario": "s4-hybrid-predictive"}))

    with pytest.raises(ValueError, match="records no predictor artifact hash"):
        gru_study.verify_deployed_artifact(manifest)
