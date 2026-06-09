import json
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import redis

from shared.config import get_env
from shared.constants import MACHINE_TYPES, REDIS_DEFAULT_URL, REDIS_SENSOR_CHANNEL


class ReplayService:
    """Service to replay CSV sensor data through Redis."""

    def __init__(self):
        self.redis_client = redis.from_url(get_env("REDIS_URL", REDIS_DEFAULT_URL), decode_responses=True)
        self.channel_name = get_env("IOT_CHANNEL", REDIS_SENSOR_CHANNEL)
        self.data_dir = Path(__file__).parent.parent / "data"
        self.rows_per_file = int(get_env("IOT_ROWS_PER_FILE", 500))
        self.replay_interval_seconds = int(get_env("IOT_REPLAY_INTERVAL_SECONDS", 2))

    def publish_machine_row(self, machine, row):
        timestamp = row.get("timestamp")
        sensors = {k: v for k, v in row.items() if k != "timestamp"}
        payload = {"machine": machine, "sensors": sensors, "timestamp": timestamp}
        self.redis_client.publish(self.channel_name, json.dumps(payload))
        return payload

    def replay_csv(self, machine):
        path = self.data_dir / f"{machine}.csv"
        while True:
            frame = pd.read_csv(path)
            rows = frame.to_dict(orient="records")
            for row in rows:
                self.publish_machine_row(machine, row)
                time.sleep(self.replay_interval_seconds)

    def start_replay_threads(self):
        for machine in MACHINE_TYPES:
            thread = threading.Thread(target=self.replay_csv, args=(machine,), daemon=True)
            thread.start()


class CSVGenerator:
    """Utility to generate CSV files for simulation."""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.rows_per_file = int(get_env("IOT_ROWS_PER_FILE", 500))

    def _build_timestamps(self):
        start = datetime(2025, 1, 1, 0, 0, 0)
        return [(start + pd.Timedelta(minutes=i)).isoformat() for i in range(self.rows_per_file)]

    def _insert_spikes(self, values, ratio, low_factor=1.6, high_factor=2.4):
        values = pd.to_numeric(values, errors="coerce").fillna(0).to_numpy(copy=True)
        count = max(1, int(len(values) * ratio))
        spike_indexes = np.random.choice(len(values), count, replace=False)
        scale = np.random.uniform(low_factor, high_factor, size=count)
        values[spike_indexes] *= scale
        return values

    def generate_csv_files(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        timestamps = self._build_timestamps()

        # ... generator logic remains intentionally simplified for later extension
        return
