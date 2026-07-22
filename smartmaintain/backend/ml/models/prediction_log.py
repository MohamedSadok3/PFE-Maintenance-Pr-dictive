"""
Database models for prediction logging and feedback collection.
These models enable fine-tuning by storing predictions and ground truth labels.
"""
from typing import List, Optional
from datetime import datetime

from shared.entity import isoformat_value, mapping_from_row


class PredictionLog:
    """
    Logs ML predictions for future fine-tuning.
    
    Each prediction is stored with:
    - Input sensors data
    - Model prediction
    - Confidence scores
    - Timestamp and metadata
    
    Later, technicians can add ground truth labels via PredictionFeedback.
    """

    def __init__(
        self,
        id: int,
        machine: str,
        plant_id: Optional[int],
        component_id: Optional[int],
        sensors: dict,
        predicted_defect: str,
        defect_score: float,
        confidence: float,
        defect_scores: dict,
        model_name: str,
        timestamp: datetime,
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.machine = machine
        self.plant_id = plant_id
        self.component_id = component_id
        self.sensors = sensors
        self.predicted_defect = predicted_defect
        self.defect_score = defect_score
        self.confidence = confidence
        self.defect_scores = defect_scores
        self.model_name = model_name
        self.timestamp = timestamp
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "machine": self.machine,
            "plant_id": self.plant_id,
            "component_id": self.component_id,
            "sensors": self.sensors,
            "predicted_defect": self.predicted_defect,
            "defect_score": self.defect_score,
            "confidence": self.confidence,
            "defect_scores": self.defect_scores,
            "model_name": self.model_name,
            "timestamp": isoformat_value(self.timestamp),
            "created_at": isoformat_value(self.created_at),
        }

    @staticmethod
    def from_row(row) -> Optional["PredictionLog"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return PredictionLog(
            id=data.get("id"),
            machine=data.get("machine"),
            plant_id=data.get("plant_id"),
            component_id=data.get("component_id"),
            sensors=data.get("sensors", {}),
            predicted_defect=data.get("predicted_defect"),
            defect_score=data.get("defect_score"),
            confidence=data.get("confidence"),
            defect_scores=data.get("defect_scores", {}),
            model_name=data.get("model_name"),
            timestamp=data.get("timestamp"),
            created_at=data.get("created_at"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["PredictionLog"]:
        return [log for row in rows if (log := cls.from_row(row))]


class PredictionFeedback:
    """
    Ground truth labels for predictions, used for fine-tuning.
    
    After a prediction is made, technicians can:
    - Confirm the predicted defect was correct
    - Provide the actual defect found during maintenance
    - Add notes about the issue
    
    This data is exported for model retraining in Google Colab.
    """

    def __init__(
        self,
        id: int,
        prediction_log_id: int,
        actual_defect: str,
        is_correct: bool,
        feedback_source: str,  # 'technician', 'maintenance_report', 'auto'
        technician_id: Optional[int] = None,
        notes: Optional[str] = None,
        severity: Optional[str] = None,  # 'low', 'medium', 'high', 'critical'
        created_at: Optional[datetime] = None,
    ):
        self.id = id
        self.prediction_log_id = prediction_log_id
        self.actual_defect = actual_defect
        self.is_correct = is_correct
        self.feedback_source = feedback_source
        self.technician_id = technician_id
        self.notes = notes
        self.severity = severity
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "prediction_log_id": self.prediction_log_id,
            "actual_defect": self.actual_defect,
            "is_correct": self.is_correct,
            "feedback_source": self.feedback_source,
            "technician_id": self.technician_id,
            "notes": self.notes,
            "severity": self.severity,
            "created_at": isoformat_value(self.created_at),
        }

    @staticmethod
    def from_row(row) -> Optional["PredictionFeedback"]:
        data = mapping_from_row(row)
        if not data:
            return None
        return PredictionFeedback(
            id=data.get("id"),
            prediction_log_id=data.get("prediction_log_id"),
            actual_defect=data.get("actual_defect"),
            is_correct=data.get("is_correct"),
            feedback_source=data.get("feedback_source"),
            technician_id=data.get("technician_id"),
            notes=data.get("notes"),
            severity=data.get("severity"),
            created_at=data.get("created_at"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["PredictionFeedback"]:
        return [feedback for row in rows if (feedback := cls.from_row(row))]


class TrainingDataExport:
    """
    Represents a labeled training sample ready for export.
    Combines PredictionLog + PredictionFeedback.
    """

    def __init__(
        self,
        machine: str,
        sensors: dict,
        actual_defect: str,
        predicted_defect: str,
        is_correct: bool,
        confidence: float,
        timestamp: datetime,
        model_name: str,
    ):
        self.machine = machine
        self.sensors = sensors
        self.actual_defect = actual_defect
        self.predicted_defect = predicted_defect
        self.is_correct = is_correct
        self.confidence = confidence
        self.timestamp = timestamp
        self.model_name = model_name

    def to_dict(self) -> dict:
        return {
            "machine": self.machine,
            "sensors": self.sensors,
            "actual_defect": self.actual_defect,
            "predicted_defect": self.predicted_defect,
            "is_correct": self.is_correct,
            "confidence": self.confidence,
            "timestamp": isoformat_value(self.timestamp),
            "model_name": self.model_name,
        }

    @staticmethod
    def from_joined_row(row) -> Optional["TrainingDataExport"]:
        """Create from a joined prediction_log + prediction_feedback query."""
        data = mapping_from_row(row)
        if not data:
            return None
        return TrainingDataExport(
            machine=data.get("machine"),
            sensors=data.get("sensors", {}),
            actual_defect=data.get("actual_defect"),
            predicted_defect=data.get("predicted_defect"),
            is_correct=data.get("is_correct"),
            confidence=data.get("confidence"),
            timestamp=data.get("timestamp"),
            model_name=data.get("model_name"),
        )

    @classmethod
    def from_rows(cls, rows) -> List["TrainingDataExport"]:
        return [export for row in rows if (export := cls.from_joined_row(row))]
