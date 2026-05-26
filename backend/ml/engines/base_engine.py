from abc import ABC, abstractmethod


class BaseMLEngine(ABC):
    """Base class for ML prediction engines."""

    @abstractmethod
    def predict(self, machine, sensors):
        """
        Predict defect for a machine based on sensor data.

        Args:
            machine (str): Machine type (moteur, pompe, compresseur, echangeur)
            sensors (dict): Sensor readings

        Returns:
            dict: Prediction result with keys:
                - defect_score (float): Overall defect score 0-1
                - anomaly_score (float): Alias for defect_score
                - defect (str): Defect name or "normal_operation"
                - defect_scores (dict): Individual defect scores
                - confidence (float): Prediction confidence 0-1
                - required_sensors (list): Sensors used for prediction
        """
        pass