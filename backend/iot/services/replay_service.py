"""
ReplayService — Service IoT SmartMaintain
=========================================
Lit les CSV de données capteurs et publie sur Redis
avec les features statistiques pré-calculées sur une fenêtre glissante.
Compatible avec RealMLEngine (XGBoost).
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import redis
from scipy.stats import skew, kurtosis

from shared.config import get_env
from shared.constants import MACHINE_TYPES, REDIS_DEFAULT_URL, REDIS_SENSOR_CHANNEL


class ReplayService:
    """Service to replay CSV sensor data through Redis."""

    WINDOW_SIZE = 20  # Nombre de lignes pour calculer les features statistiques

    def __init__(self):
        self.redis_client = redis.from_url(
            get_env("REDIS_URL", REDIS_DEFAULT_URL), decode_responses=True
        )
        self.channel_name         = get_env("IOT_CHANNEL", REDIS_SENSOR_CHANNEL)
        self.data_dir             = Path(__file__).parent.parent / "data"
        self.replay_interval_seconds = int(get_env("IOT_REPLAY_INTERVAL_SECONDS", 2))

    # ------------------------------------------------------------------
    # Calcul des features statistiques
    # ------------------------------------------------------------------

    def _compute_features(self, window: list, sensor: str) -> dict:
        """
        Calcule les 9 features statistiques depuis une fenêtre de valeurs.
        Correspond exactement aux colonnes du CSV CWRU et aux features
        attendues par RealMLEngine (XGBoost).

        Features : max, min, mean, sd, rms, skewness, kurtosis, crest, form
        """
        values   = np.array([float(row.get(sensor, 0.0)) for row in window])
        rms      = float(np.sqrt(np.mean(values ** 2)))
        mean_abs = float(np.mean(np.abs(values)))

        return {
            f"{sensor}_max":      round(float(np.max(values)),  6),
            f"{sensor}_min":      round(float(np.min(values)),  6),
            f"{sensor}_mean":     round(float(np.mean(values)), 6),
            f"{sensor}_sd":       round(float(np.std(values)),  6),
            f"{sensor}_rms":      round(rms, 6),
            f"{sensor}_skewness": round(float(skew(values)),     6),
            f"{sensor}_kurtosis": round(float(kurtosis(values)), 6),
            f"{sensor}_crest":    round(float(np.max(np.abs(values))) / (rms + 1e-10), 6),
            f"{sensor}_form":     round(rms / (mean_abs + 1e-10), 6),
        }

    # ------------------------------------------------------------------
    # Publication Redis
    # ------------------------------------------------------------------

    def publish_machine_window(self, machine: str, window: list) -> dict:
        """
        Calcule les features sur la fenêtre et publie sur Redis.
        Format compatible avec RealMLEngine (XGBoost).
        """
        timestamp = window[-1].get("timestamp")
        sensors   = {}

        # Features statistiques vibration (9 features → modèle XGBoost)
        sensors.update(self._compute_features(window, "vibration"))

        # Features statistiques current
        if "current" in window[-1]:
            sensors.update(self._compute_features(window, "current"))

        # Valeurs instantanées pour l'affichage frontend
        sensors["vibration_instant"] = round(float(window[-1].get("vibration", 0.0)), 6)
        if "current" in window[-1]:
            sensors["current_instant"] = round(float(window[-1].get("current", 0.0)), 6)
        if "temperature" in window[-1]:
            sensors["temperature"] = round(float(window[-1].get("temperature", 0.0)), 6)

        payload = {
            "machine":   machine,
            "sensors":   sensors,
            "timestamp": timestamp,
        }
        self.redis_client.publish(self.channel_name, json.dumps(payload))
        return payload

    # ------------------------------------------------------------------
    # Replay CSV
    # ------------------------------------------------------------------

    def replay_csv(self, machine: str):
        """
        Lit le CSV une seule fois (fix bug original : relecture à chaque loop)
        et publie des fenêtres glissantes sur Redis.
        """
        path = self.data_dir / f"{machine}.csv"
        if not path.exists():
            return

        # Lire une seule fois
        df   = pd.read_csv(path)
        rows = df.to_dict(orient="records")

        window = []
        while True:
            for row in rows:
                window.append(row)

                # Publier quand la fenêtre est pleine
                if len(window) >= self.WINDOW_SIZE:
                    self.publish_machine_window(machine, window)
                    window = window[1:]  # fenêtre glissante

                time.sleep(self.replay_interval_seconds)

    def start_replay_threads(self):
        for machine in MACHINE_TYPES:
            thread = threading.Thread(
                target=self.replay_csv, args=(machine,), daemon=True
            )
            thread.start()


class CSVGenerator:
    """Utility to generate CSV files for simulation."""

    def __init__(self):
        self.data_dir    = Path(__file__).parent.parent / "data"
        self.rows_per_file = int(get_env("IOT_ROWS_PER_FILE", 500))

    def _build_timestamps(self):
        start = datetime(2025, 1, 1, 0, 0, 0)
        return [(start + pd.Timedelta(minutes=i)).isoformat() for i in range(self.rows_per_file)]

    def generate_csv_files(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return
