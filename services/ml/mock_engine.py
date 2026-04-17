import math
import random


class MockMLEngine:
    DEFECT_RULES = {
        "moteur": [
            {
                "name": "degradation_roulement",
                "required_sensors": ["vibration"],
                "score_fn": lambda s: max(0.0, (float(s.get("vibration", 0.0)) - 0.75) / 0.9),
            },
            {
                "name": "desequilibre_desalignement",
                "required_sensors": ["vibration", "current"],
                "score_fn": lambda s: max(
                    0.0,
                    (
                        (float(s.get("vibration", 0.0)) - 0.55) / 0.8
                        + (float(s.get("current", 0.0)) - 13.0) / 9.0
                    )
                    / 2,
                ),
            },
        ],
        "pompe": [
            {
                "name": "cavitation",
                "required_sensors": ["vibration", "pressure_in", "pressure_out"],
                "score_fn": lambda s: max(
                    0.0,
                    (
                        (float(s.get("vibration", 0.0)) - 0.65) / 0.9
                        + (4.0 - (float(s.get("pressure_out", 0.0)) - float(s.get("pressure_in", 0.0)))) / 3.0
                    )
                    / 2,
                ),
            },
            {
                "name": "usure_garniture_mecanique",
                "required_sensors": ["vibration"],
                "score_fn": lambda s: max(0.0, (float(s.get("vibration", 0.0)) - 0.85) / 0.9),
            },
        ],
        "compresseur": [
            {
                "name": "usure_soupapes",
                "required_sensors": ["pressure", "current"],
                "score_fn": lambda s: max(
                    0.0,
                    (
                        (9.5 - float(s.get("pressure", 0.0))) / 5.0
                        + (float(s.get("current", 0.0)) - 14.0) / 9.0
                    )
                    / 2,
                ),
            },
            {
                "name": "refroidissement_huile",
                "required_sensors": ["temperature_oil", "temperature_air"],
                "score_fn": lambda s: max(
                    0.0,
                    (
                        (float(s.get("temperature_oil", 0.0)) - 82.0) / 26.0
                        + (float(s.get("temperature_air", 0.0)) - 58.0) / 22.0
                    )
                    / 2,
                ),
            },
        ],
        "echangeur": [
            {
                "name": "encrassement_progressif",
                "required_sensors": ["temp_in_hot", "temp_out_hot", "flow_rate"],
                "score_fn": lambda s: max(
                    0.0,
                    (
                        (26.0 - (float(s.get("temp_in_hot", 0.0)) - float(s.get("temp_out_hot", 0.0)))) / 15.0
                        + (120.0 - float(s.get("flow_rate", 0.0))) / 80.0
                    )
                    / 2,
                ),
            },
            {
                "name": "fuite_interne",
                "required_sensors": ["temp_in_hot", "temp_out_hot", "temp_in_cold", "temp_out_cold"],
                "score_fn": lambda s: max(
                    0.0,
                    (
                        (float(s.get("temp_out_cold", 0.0)) - float(s.get("temp_in_cold", 0.0)) - 8.0) / 14.0
                        + (14.0 - (float(s.get("temp_in_hot", 0.0)) - float(s.get("temp_out_hot", 0.0)))) / 12.0
                    )
                    / 2,
                ),
            },
        ],
    }

    def _clamp(self, value, low=0.0, high=1.0):
        return max(low, min(high, value))

    def _with_noise_and_spike(self, base_score):
        score = base_score + random.uniform(-0.05, 0.05)
        if random.random() < 0.05:
            score = max(score, random.uniform(0.86, 0.98))
        return self._clamp(score)

    def predict(self, machine, sensors):
        machine = (machine or "").lower()
        sensors = sensors or {}

        defect_name = "normal_operation"
        required_sensors = []
        confidence = 0.6
        base_score = 0.2

        rules = self.DEFECT_RULES.get(machine)
        if not rules:
            base_score = 0.3
            defect_name = "unknown_machine"
            confidence = 0.5
            defect_scores = {"unknown_machine": round(base_score, 4)}
        else:
            best = {"score": 0.0, "name": "normal_operation", "required_sensors": []}
            defect_scores = {}
            for rule in rules:
                score = self._clamp(rule["score_fn"](sensors))
                score = self._with_noise_and_spike(score)
                defect_scores[rule["name"]] = round(score, 4)
                if score > best["score"]:
                    best = {
                        "score": score,
                        "name": rule["name"],
                        "required_sensors": rule["required_sensors"],
                    }
            base_score = best["score"]
            if base_score > 0.55:
                defect_name = best["name"]
                required_sensors = best["required_sensors"]
            confidence = 0.58 + 0.37 * base_score

        score = self._with_noise_and_spike(base_score)
        confidence = self._clamp(confidence + random.uniform(-0.04, 0.04))

        # Ensure confidence stays realistic and slightly linked to score intensity.
        confidence = self._clamp((confidence + math.sqrt(score)) / 2)

        if score > 0.85 and defect_name == "normal_operation":
            defect_name = "anomaly_detected"

        return {
            "defect_score": round(score, 4),
            "anomaly_score": round(score, 4),  # Backward compatibility during transition.
            "defect_scores": defect_scores,
            "defect": defect_name,
            "confidence": round(confidence, 4),
            "required_sensors": required_sensors,
        }
