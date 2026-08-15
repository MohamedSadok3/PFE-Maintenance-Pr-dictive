"""
ReplayService — Service IoT SmartMaintain
=========================================
Lit les CSV de données capteurs et publie sur Redis
avec les features statistiques pré-calculées sur une fenêtre glissante.
Compatible avec RealMLEngine (XGBoost).

Optimisations:
- Calcul vectorisé des features (NumPy)
- Connection Redis persistante avec pool
- Gestion d'erreurs robuste
- Logging structuré
"""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import redis
from scipy.stats import skew, kurtosis

from shared.config import get_env
from shared.constants import MACHINE_TYPES, REDIS_DEFAULT_URL, REDIS_SENSOR_CHANNEL

# Configure logging
logger = logging.getLogger(__name__)


class ReplayService:
    """
    Service to replay CSV sensor data through Redis with sliding window feature computation.
    
    Features computed per sensor:
    - Statistical: max, min, mean, std, rms
    - Shape: skewness, kurtosis
    - Signal: crest_factor, form_factor
    """

    WINDOW_SIZE = 20  # Sliding window size for feature computation
    EPSILON = 1e-10   # Prevent division by zero

    def __init__(self):
        """Initialize ReplayService with Redis connection and configuration."""
        redis_url = get_env("REDIS_URL", REDIS_DEFAULT_URL)
        
        # Use connection pool for better performance
        self.redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=10,
            decode_responses=True
        )
        self.redis_client = redis.Redis(connection_pool=self.redis_pool)
        
        self.channel_name = get_env("IOT_CHANNEL", REDIS_SENSOR_CHANNEL)
        self.data_dir = Path(__file__).parent.parent / "data"
        self.replay_interval_seconds = int(get_env("IOT_REPLAY_INTERVAL_SECONDS", 2))
        
        # Optional plant_id for multi-tenant routing
        plant_id_env = get_env("IOT_PLANT_ID")
        self.plant_id = int(plant_id_env) if plant_id_env else None
        
        logger.info(
            f"ReplayService initialized: interval={self.replay_interval_seconds}s, "
            f"window_size={self.WINDOW_SIZE}, plant_id={self.plant_id}"
        )

    def _compute_features(self, window: List[Dict], sensor: str) -> Dict[str, float]:
        """
        Compute 9 statistical features from a sliding window of sensor values.
        
        Optimized with vectorized NumPy operations for better performance.
        
        Args:
            window: List of data points (dicts with sensor readings)
            sensor: Sensor name to compute features for
            
        Returns:
            Dictionary of computed features with sensor name prefix
            
        Features:
            - max, min, mean: Basic statistics
            - sd (std): Standard deviation
            - rms: Root Mean Square
            - skewness, kurtosis: Distribution shape
            - crest_factor: Peak/RMS ratio (indicator of transients)
            - form_factor: RMS/Mean ratio (signal shape)
        """
        try:
            # Vectorized extraction (faster than list comprehension)
            values = np.array([float(row.get(sensor, 0.0)) for row in window], dtype=np.float64)
            
            # Handle empty or invalid data
            if len(values) == 0 or np.all(values == 0):
                return self._empty_features(sensor)
            
            # Vectorized computations
            rms = float(np.sqrt(np.mean(values ** 2)))
            mean_abs = float(np.mean(np.abs(values)))
            
            return {
                f"{sensor}_max":      round(float(np.max(values)), 6),
                f"{sensor}_min":      round(float(np.min(values)), 6),
                f"{sensor}_mean":     round(float(np.mean(values)), 6),
                f"{sensor}_sd":       round(float(np.std(values)), 6),
                f"{sensor}_rms":      round(rms, 6),
                f"{sensor}_skewness": round(float(skew(values)), 6),
                f"{sensor}_kurtosis": round(float(kurtosis(values)), 6),
                f"{sensor}_crest":    round(float(np.max(np.abs(values))) / (rms + self.EPSILON), 6),
                f"{sensor}_form":     round(rms / (mean_abs + self.EPSILON), 6),
            }
        except Exception as e:
            logger.warning(f"Feature computation failed for sensor '{sensor}': {e}")
            return self._empty_features(sensor)
    
    def _empty_features(self, sensor: str) -> Dict[str, float]:
        """Return zero-filled features for error cases."""
        return {
            f"{sensor}_{feat}": 0.0
            for feat in ["max", "min", "mean", "sd", "rms", "skewness", "kurtosis", "crest", "form"]
        }

    def publish_machine_window(self, machine: str, window: List[Dict]) -> Optional[Dict]:
        """
        Compute features from sliding window and publish to Redis.
        
        Auto-detects all sensor columns (except timestamp) and computes:
        - 9 statistical features per sensor (for ML)
        - Instant value per sensor (for frontend display)
        - Backward-compatible aliases for common sensors
        
        Args:
            machine: Machine type (moteur, pompe, compresseur, echangeur)
            window: Sliding window of sensor readings
            
        Returns:
            Published payload dict, or None if publication fails
        """
        try:
            if not window:
                logger.warning(f"Empty window for machine '{machine}', skipping publication")
                return None
                
            timestamp = window[-1].get("timestamp")
            sensors = {}

            # Auto-detect all sensor columns (exclude timestamp)
            all_sensor_names = [key for key in window[-1].keys() if key != "timestamp"]
            
            if not all_sensor_names:
                logger.warning(f"No sensors found for machine '{machine}'")
                return None

            # Compute features for each sensor
            for sensor_name in all_sensor_names:
                # Compute 9 ML features
                sensors.update(self._compute_features(window, sensor_name))
                
                # Add instant value for frontend charts
                instant_value = round(float(window[-1].get(sensor_name, 0.0)), 6)
                sensors[f"{sensor_name}_instant"] = instant_value
                
                # Backward-compatible aliases (frontend may look for these)
                if sensor_name in ["temperature", "pressure", "flow_rate"]:
                    sensors[sensor_name] = instant_value

            # Build payload
            payload = {
                "machine": machine,
                "sensors": sensors,
                "timestamp": timestamp,
            }
            
            # Add plant_id for multi-tenant routing (optional)
            if self.plant_id is not None:
                payload["plant_id"] = self.plant_id

            # Publish to Redis
            self.redis_client.publish(self.channel_name, json.dumps(payload))
            
            return payload
            
        except Exception as e:
            logger.error(f"Failed to publish data for machine '{machine}': {e}", exc_info=True)
            return None

    def replay_csv(self, machine: str):
        """
        Read CSV once and replay data through Redis with sliding window.
        
        Optimization: CSV is loaded into memory once (not re-read each loop).
        Runs indefinitely, cycling through the data.
        
        Args:
            machine: Machine type (must have corresponding CSV file)
        """
        path = self.data_dir / f"{machine}.csv"
        
        if not path.exists():
            logger.error(f"CSV file not found for machine '{machine}': {path}")
            return

        try:
            # Load CSV once (memory optimization vs repeated file I/O)
            logger.info(f"Loading CSV for machine '{machine}': {path}")
            df = pd.read_csv(path)
            rows = df.to_dict(orient="records")
            logger.info(f"Loaded {len(rows)} rows for machine '{machine}'")
            
            if len(rows) < self.WINDOW_SIZE:
                logger.warning(
                    f"CSV for '{machine}' has only {len(rows)} rows, "
                    f"less than window size {self.WINDOW_SIZE}"
                )
            
            window = []
            
            # Infinite loop: replay data continuously
            while True:
                for row in rows:
                    window.append(row)

                    # Publish when window is full
                    if len(window) >= self.WINDOW_SIZE:
                        self.publish_machine_window(machine, window)
                        window = window[1:]  # Slide window forward

                    time.sleep(self.replay_interval_seconds)
                    
        except Exception as e:
            logger.error(f"Replay failed for machine '{machine}': {e}", exc_info=True)

    def _run_replay_with_retries(self, machine: str):
        """Keep a replay worker alive without growing the Python call stack."""
        while True:
            self.replay_csv(machine)
            logger.info("Retrying replay for machine '%s' in 10 seconds", machine)
            time.sleep(10)

    def start_replay_threads(self):
        """Start replay threads for all configured machine types."""
        logger.info(f"Starting replay threads for {len(MACHINE_TYPES)} machines: {MACHINE_TYPES}")
        
        threads = []
        for machine in MACHINE_TYPES:
            thread = threading.Thread(
                target=self._run_replay_with_retries,
                args=(machine,),
                daemon=True,
                name=f"ReplayThread-{machine}"
            )
            thread.start()
            threads.append(thread)
            logger.info(f"Started replay thread for machine '{machine}'")
        
        return threads
