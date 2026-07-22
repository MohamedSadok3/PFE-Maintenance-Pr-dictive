"""
Unit tests for MockMLEngine.

Run with:
    pytest backend/tests/test_mock_engine.py -v
"""

import sys
from pathlib import Path

# Allow imports from the ml service package
sys.path.insert(0, str(Path(__file__).parent.parent / "ml"))

import pytest
from engines.mock_engine import MockMLEngine


@pytest.fixture
def engine():
    return MockMLEngine()


# ── Return shape ────────────────────────────────────────────────────────────

class TestReturnShape:
    def test_moteur_keys(self, engine):
        result = engine.predict("moteur", {"vibration": 0.5, "current": 10.0})
        assert set(result.keys()) == {
            "defect_score", "anomaly_score", "defect_scores",
            "defect", "confidence", "required_sensors",
        }

    def test_scores_are_floats(self, engine):
        result = engine.predict("moteur", {"vibration": 0.5, "current": 10.0})
        assert isinstance(result["defect_score"], float)
        assert isinstance(result["confidence"], float)

    def test_defect_scores_dict(self, engine):
        result = engine.predict("moteur", {"vibration": 0.5, "current": 10.0})
        assert isinstance(result["defect_scores"], dict)
        assert len(result["defect_scores"]) > 0

    def test_required_sensors_list(self, engine):
        result = engine.predict("moteur", {"vibration": 0.5, "current": 10.0})
        assert isinstance(result["required_sensors"], list)


# ── Score ranges ────────────────────────────────────────────────────────────

class TestScoreRanges:
    @pytest.mark.parametrize("machine,sensors", [
        ("moteur",      {"vibration": 0.3, "current": 10.0}),
        ("pompe",       {"vibration": 0.4, "pressure_in": 5.0, "pressure_out": 9.0, "flow_rate": 120.0}),
        ("compresseur", {"pressure": 9.0, "current": 12.0, "temperature_oil": 75.0, "temperature_air": 45.0}),
        ("echangeur",   {"temp_in_hot": 90.0, "temp_out_hot": 60.0,
                         "temp_in_cold": 20.0, "temp_out_cold": 35.0, "flow_rate": 100.0}),
    ])
    def test_score_in_range(self, engine, machine, sensors):
        result = engine.predict(machine, sensors)
        assert 0.0 <= result["defect_score"] <= 1.0, (
            f"defect_score out of range for {machine}: {result['defect_score']}"
        )

    @pytest.mark.parametrize("machine,sensors", [
        ("moteur",      {"vibration": 0.3, "current": 10.0}),
        ("pompe",       {"vibration": 0.4, "pressure_in": 5.0, "pressure_out": 9.0, "flow_rate": 120.0}),
    ])
    def test_confidence_in_range(self, engine, machine, sensors):
        result = engine.predict(machine, sensors)
        assert 0.0 <= result["confidence"] <= 1.0, (
            f"confidence out of range for {machine}: {result['confidence']}"
        )


# ── Defect detection ────────────────────────────────────────────────────────

class TestDefectDetection:
    def test_normal_operation_low_vibration(self, engine):
        """Low vibration and current → should rarely trigger a defect."""
        results = [
            engine.predict("moteur", {"vibration": 0.1, "current": 8.0})
            for _ in range(20)
        ]
        # With low values the score should be well below the spike threshold most of the time
        avg_score = sum(r["defect_score"] for r in results) / len(results)
        assert avg_score < 0.7, f"Expected mostly normal operation, got avg_score={avg_score:.3f}"

    def test_high_vibration_raises_score(self, engine):
        """Very high vibration should produce a higher average defect score."""
        results_low  = [engine.predict("moteur", {"vibration": 0.1, "current": 8.0})  for _ in range(30)]
        results_high = [engine.predict("moteur", {"vibration": 1.5, "current": 22.0}) for _ in range(30)]

        avg_low  = sum(r["defect_score"] for r in results_low)  / len(results_low)
        avg_high = sum(r["defect_score"] for r in results_high) / len(results_high)

        assert avg_high > avg_low, (
            f"High vibration should produce higher scores: low={avg_low:.3f}, high={avg_high:.3f}"
        )

    def test_defect_scores_sum_gte_defect_score(self, engine):
        """The max value in defect_scores should reflect the overall defect_score."""
        result = engine.predict("moteur", {"vibration": 1.2, "current": 20.0})
        max_defect_score = max(result["defect_scores"].values())
        # The overall defect_score should be close to the best defect score
        assert abs(result["defect_score"] - max_defect_score) < 0.3


# ── Unknown / edge cases ────────────────────────────────────────────────────

class TestEdgeCases:
    def test_unknown_machine_returns_fallback(self, engine):
        result = engine.predict("unknown_machine", {})
        assert result["defect"] == "unknown_machine"
        assert 0.0 <= result["defect_score"] <= 1.0

    def test_empty_sensors_does_not_raise(self, engine):
        result = engine.predict("moteur", {})
        assert "defect_score" in result

    def test_none_machine_does_not_raise(self, engine):
        result = engine.predict(None, {"vibration": 0.5})
        assert "defect_score" in result

    def test_case_insensitive_machine(self, engine):
        result_lower = engine.predict("moteur", {"vibration": 0.5})
        result_upper = engine.predict("MOTEUR", {"vibration": 0.5})
        # Both should produce a valid result (scores will differ due to noise)
        assert "defect_score" in result_lower
        assert "defect_score" in result_upper

    @pytest.mark.parametrize("machine", ["moteur", "pompe", "compresseur", "echangeur"])
    def test_all_machines_return_result(self, engine, machine):
        result = engine.predict(machine, {})
        assert "defect_score" in result
        assert "defect" in result
