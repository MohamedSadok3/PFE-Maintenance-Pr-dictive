import json
import threading
from flask_socketio import SocketIO

from shared.config import get_env
from .alert_service import AlertService
from .serializers import serialize_alert


class RedisConsumer:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.alert_service = AlertService()
        self.predictions_channel = "ml_predictions"
        self.consumer_thread = None

    def consume_predictions(self):
        """Consume ML predictions from Redis and create alerts."""
        pubsub = self.alert_service.redis_client.pubsub()
        pubsub.subscribe(self.predictions_channel)

        for message in pubsub.listen():
            if message.get("type") != "message":
                continue

            try:
                prediction = json.loads(message.get("data", "{}"))
                defect_scores = prediction.get("defect_scores") or {}

                if isinstance(defect_scores, dict) and defect_scores:
                    top_defect, top_score = max(defect_scores.items(), key=lambda item: float(item[1]))
                    score = float(top_score)
                    defect_name = top_defect
                else:
                    score = float(prediction.get("defect_score", prediction.get("anomaly_score", 0)))
                    defect_name = prediction.get("defect", "anomaly_detected")

                severity = self.alert_service.severity_from_score(score)

                # Always emit raw prediction for live charts
                self.socketio.emit("sensor:data", prediction)

                if not severity:
                    continue

                # Get plant_id from prediction or use default
                incoming_plant_id = prediction.get("plant_id")
                if incoming_plant_id:
                    plant_id = int(incoming_plant_id)
                else:
                    plant_id = self.alert_service.get_default_plant_id()

                if not plant_id:
                    continue

                # Create alert
                alert = self.alert_service.insert_alert(
                    plant_id=plant_id,
                    machine=prediction.get("machine", "unknown"),
                    defect=defect_name,
                    defect_score=score,
                    confidence=float(prediction.get("confidence", 0)),
                    severity=severity,
                )

                # Emit new alert via SocketIO
                self.socketio.emit("alert:new", serialize_alert(alert))

            except Exception as e:
                # Log error but continue processing
                print(f"Error processing prediction: {e}")
                continue

    def start_consumer_thread(self):
        """Start the Redis consumer thread."""
        self.consumer_thread = threading.Thread(target=self.consume_predictions, daemon=True)
        self.consumer_thread.start()

    def stop_consumer_thread(self):
        """Stop the Redis consumer thread."""
        if self.consumer_thread and self.consumer_thread.is_alive():
            # Note: Daemon threads will be terminated when main thread exits
            pass