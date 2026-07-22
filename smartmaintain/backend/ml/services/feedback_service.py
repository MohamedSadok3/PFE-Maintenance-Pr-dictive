"""
Feedback Service for ML Prediction Logging and Fine-Tuning Data Collection.

This service handles:
1. Storing predictions for future analysis
2. Collecting ground truth labels from technicians
3. Exporting labeled data for external model retraining (Google Colab)

NO training happens in this service - only data collection and export.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from shared.database import get_db_connection
from models.prediction_log import PredictionLog, PredictionFeedback, TrainingDataExport

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for prediction logging and feedback collection."""

    def __init__(self):
        pass

    # ================================================================
    # Prediction Logging
    # ================================================================

    def log_prediction(
        self,
        machine: str,
        sensors: dict,
        predicted_defect: str,
        defect_score: float,
        confidence: float,
        defect_scores: dict,
        model_name: str,
        timestamp: Optional[str] = None,
        plant_id: Optional[int] = None,
        component_id: Optional[int] = None,
    ) -> Optional[int]:
        """
        Log a prediction to the database for future fine-tuning.
        
        Args:
            machine: Machine type (moteur, pompe, etc.)
            sensors: Raw sensor readings (input to model)
            predicted_defect: Model's prediction
            defect_score: Overall defect probability
            confidence: Prediction confidence
            defect_scores: Per-class probabilities
            model_name: Model version used
            timestamp: When prediction was made (ISO format)
            plant_id: Optional plant identifier
            component_id: Optional component identifier
        
        Returns:
            prediction_log_id if successful, None otherwise
        """
        try:
            # Parse timestamp
            if timestamp:
                if isinstance(timestamp, str):
                    ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                else:
                    ts = timestamp
            else:
                ts = datetime.now(timezone.utc)

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO prediction_log (
                            machine, plant_id, component_id, sensors,
                            predicted_defect, defect_score, confidence,
                            defect_scores, model_name, timestamp
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            machine,
                            plant_id,
                            component_id,
                            json.dumps(sensors),
                            predicted_defect,
                            defect_score,
                            confidence,
                            json.dumps(defect_scores),
                            model_name,
                            ts,
                        ),
                    )
                    result = cur.fetchone()
                    prediction_id = result["id"] if result else None
                    conn.commit()
                    
                    if prediction_id:
                        logger.debug(
                            f"Logged prediction #{prediction_id} for {machine}: {predicted_defect}"
                        )
                    
                    return prediction_id

        except Exception as e:
            logger.error(f"Failed to log prediction: {e}", exc_info=True)
            return None

    def get_prediction_log(self, prediction_id: int) -> Optional[PredictionLog]:
        """Retrieve a prediction log by ID."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT * FROM prediction_log WHERE id = %s
                        """,
                        (prediction_id,),
                    )
                    row = cur.fetchone()
                    return PredictionLog.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch prediction log {prediction_id}: {e}")
            return None

    def get_recent_predictions(
        self, machine: Optional[str] = None, limit: int = 100
    ) -> List[PredictionLog]:
        """Get recent predictions, optionally filtered by machine type."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if machine:
                        cur.execute(
                            """
                            SELECT * FROM prediction_log
                            WHERE machine = %s
                            ORDER BY created_at DESC
                            LIMIT %s
                            """,
                            (machine, limit),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT * FROM prediction_log
                            ORDER BY created_at DESC
                            LIMIT %s
                            """,
                            (limit,),
                        )
                    rows = cur.fetchall()
                    return PredictionLog.from_rows(rows)
        except Exception as e:
            logger.error(f"Failed to fetch recent predictions: {e}")
            return []

    # ================================================================
    # Feedback Collection
    # ================================================================

    def add_feedback(
        self,
        prediction_log_id: int,
        actual_defect: str,
        feedback_source: str = "technician",
        technician_id: Optional[int] = None,
        notes: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> Optional[int]:
        """
        Add ground truth label for a prediction.
        
        Args:
            prediction_log_id: ID of the prediction to label
            actual_defect: Ground truth defect name
            feedback_source: Source of feedback (technician, maintenance_report, auto)
            technician_id: User who provided feedback
            notes: Additional context
            severity: Defect severity (low, medium, high, critical)
        
        Returns:
            feedback_id if successful, None otherwise
        """
        try:
            # Verify prediction exists
            prediction = self.get_prediction_log(prediction_log_id)
            if not prediction:
                logger.warning(f"Prediction log {prediction_log_id} not found")
                return None

            # Check if prediction was correct
            is_correct = prediction.predicted_defect == actual_defect

            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO prediction_feedback (
                            prediction_log_id, actual_defect, is_correct,
                            feedback_source, technician_id, notes, severity
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            prediction_log_id,
                            actual_defect,
                            is_correct,
                            feedback_source,
                            technician_id,
                            notes,
                            severity,
                        ),
                    )
                    result = cur.fetchone()
                    feedback_id = result["id"] if result else None
                    conn.commit()
                    
                    if feedback_id:
                        logger.info(
                            f"Feedback #{feedback_id} added for prediction #{prediction_log_id}: "
                            f"actual={actual_defect}, correct={is_correct}"
                        )
                    
                    return feedback_id

        except Exception as e:
            logger.error(f"Failed to add feedback: {e}", exc_info=True)
            return None

    def get_feedback(self, prediction_log_id: int) -> Optional[PredictionFeedback]:
        """Get feedback for a specific prediction."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT * FROM prediction_feedback
                        WHERE prediction_log_id = %s
                        """,
                        (prediction_log_id,),
                    )
                    row = cur.fetchone()
                    return PredictionFeedback.from_row(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch feedback: {e}")
            return None

    def get_unlabeled_predictions(
        self, machine: Optional[str] = None, limit: int = 100
    ) -> List[PredictionLog]:
        """Get predictions that don't have feedback yet."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    if machine:
                        cur.execute(
                            """
                            SELECT pl.* FROM prediction_log pl
                            LEFT JOIN prediction_feedback pf ON pl.id = pf.prediction_log_id
                            WHERE pf.id IS NULL AND pl.machine = %s
                            ORDER BY pl.created_at DESC
                            LIMIT %s
                            """,
                            (machine, limit),
                        )
                    else:
                        cur.execute(
                            """
                            SELECT pl.* FROM prediction_log pl
                            LEFT JOIN prediction_feedback pf ON pl.id = pf.prediction_log_id
                            WHERE pf.id IS NULL
                            ORDER BY pl.created_at DESC
                            LIMIT %s
                            """,
                            (limit,),
                        )
                    rows = cur.fetchall()
                    return PredictionLog.from_rows(rows)
        except Exception as e:
            logger.error(f"Failed to fetch unlabeled predictions: {e}")
            return []

    # ================================================================
    # Training Data Export (for external retraining)
    # ================================================================

    def export_training_data(
        self,
        machine: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_confidence: Optional[float] = None,
        include_incorrect: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Export labeled predictions for external model retraining.
        
        This data is used in Google Colab for fine-tuning models.
        Only returns predictions that have ground truth labels.
        
        Args:
            machine: Filter by machine type
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            min_confidence: Only export predictions with confidence >= this
            include_incorrect: Include incorrectly predicted samples (useful for learning)
        
        Returns:
            List of training samples ready for Colab
        """
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Build dynamic query
                    conditions = ["pf.id IS NOT NULL"]  # Only labeled data
                    params = []

                    if machine:
                        conditions.append("pl.machine = %s")
                        params.append(machine)

                    if start_date:
                        conditions.append("pl.timestamp >= %s")
                        params.append(start_date)

                    if end_date:
                        conditions.append("pl.timestamp <= %s")
                        params.append(end_date)

                    if min_confidence is not None:
                        conditions.append("pl.confidence >= %s")
                        params.append(min_confidence)

                    if not include_incorrect:
                        conditions.append("pf.is_correct = TRUE")

                    where_clause = " AND ".join(conditions)

                    query = f"""
                        SELECT 
                            pl.id AS prediction_id,
                            pl.machine,
                            pl.sensors,
                            pl.predicted_defect,
                            pl.defect_score,
                            pl.confidence,
                            pl.model_name,
                            pl.timestamp,
                            pf.actual_defect,
                            pf.is_correct,
                            pf.severity,
                            pf.notes
                        FROM prediction_log pl
                        INNER JOIN prediction_feedback pf ON pl.id = pf.prediction_log_id
                        WHERE {where_clause}
                        ORDER BY pl.timestamp ASC
                    """

                    cur.execute(query, params)
                    rows = cur.fetchall()

                    # Convert to export format
                    exports = []
                    for row in rows:
                        exports.append({
                            "prediction_id": row["prediction_id"],
                            "machine": row["machine"],
                            "sensors": row["sensors"],
                            "predicted_defect": row["predicted_defect"],
                            "actual_defect": row["actual_defect"],
                            "is_correct": row["is_correct"],
                            "confidence": float(row["confidence"]),
                            "defect_score": float(row["defect_score"]),
                            "model_name": row["model_name"],
                            "timestamp": row["timestamp"].isoformat() if row["timestamp"] else None,
                            "severity": row["severity"],
                            "notes": row["notes"],
                        })

                    logger.info(
                        f"Exported {len(exports)} training samples "
                        f"(machine={machine or 'all'}, labeled only)"
                    )

                    return exports

        except Exception as e:
            logger.error(f"Failed to export training data: {e}", exc_info=True)
            return []

    def get_statistics(self, machine: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics about logged predictions and feedback."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    machine_filter = "WHERE machine = %s" if machine else ""
                    params = [machine] if machine else []

                    # Total predictions
                    cur.execute(
                        f"SELECT COUNT(*) as count FROM prediction_log {machine_filter}",
                        params,
                    )
                    total_predictions = cur.fetchone()["count"]

                    # Labeled predictions
                    cur.execute(
                        f"""
                        SELECT COUNT(*) as count FROM prediction_log pl
                        INNER JOIN prediction_feedback pf ON pl.id = pf.prediction_log_id
                        {machine_filter}
                        """,
                        params,
                    )
                    labeled_predictions = cur.fetchone()["count"]

                    # Correct predictions
                    cur.execute(
                        f"""
                        SELECT COUNT(*) as count FROM prediction_log pl
                        INNER JOIN prediction_feedback pf ON pl.id = pf.prediction_log_id
                        WHERE pf.is_correct = TRUE {' AND pl.' + machine_filter.split('WHERE ')[1] if machine_filter else ''}
                        """,
                        params,
                    )
                    correct_predictions = cur.fetchone()["count"]

                    accuracy = (
                        (correct_predictions / labeled_predictions * 100)
                        if labeled_predictions > 0
                        else 0
                    )

                    return {
                        "machine": machine or "all",
                        "total_predictions": total_predictions,
                        "labeled_predictions": labeled_predictions,
                        "unlabeled_predictions": total_predictions - labeled_predictions,
                        "correct_predictions": correct_predictions,
                        "incorrect_predictions": labeled_predictions - correct_predictions,
                        "accuracy": round(accuracy, 2),
                        "labeling_progress": (
                            round(labeled_predictions / total_predictions * 100, 2)
                            if total_predictions > 0
                            else 0
                        ),
                    }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "machine": machine or "all",
                "error": str(e),
            }
