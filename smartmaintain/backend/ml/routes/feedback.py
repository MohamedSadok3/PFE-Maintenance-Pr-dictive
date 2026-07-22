"""
API endpoints for prediction feedback and training data export.

These endpoints enable:
1. Collecting ground truth labels from technicians
2. Exporting labeled data for external model retraining (Colab)
3. Viewing prediction logs and statistics
"""
from flask import Blueprint, request

from shared.auth import require_auth
from shared.http import get_json_body, json_error, json_response
from services.feedback_service import FeedbackService

feedback_bp = Blueprint("feedback", __name__)


@feedback_bp.route("/predictions", methods=["GET"])
@require_auth()
def get_predictions():
    """
    Get recent predictions (optionally filtered by machine).
    
    Query params:
        - machine: Filter by machine type (optional)
        - limit: Maximum results (default: 100)
        - unlabeled_only: Only show predictions without feedback (default: false)
    """
    machine = request.args.get("machine")
    limit = int(request.args.get("limit", 100))
    unlabeled_only = request.args.get("unlabeled_only", "false").lower() == "true"

    service = FeedbackService()

    if unlabeled_only:
        predictions = service.get_unlabeled_predictions(machine=machine, limit=limit)
    else:
        predictions = service.get_recent_predictions(machine=machine, limit=limit)

    return json_response({
        "predictions": [p.to_dict() for p in predictions],
        "count": len(predictions),
        "machine": machine or "all",
        "unlabeled_only": unlabeled_only,
    })


@feedback_bp.route("/predictions/<int:prediction_id>", methods=["GET"])
@require_auth()
def get_prediction(prediction_id):
    """Get a specific prediction by ID."""
    service = FeedbackService()
    prediction = service.get_prediction_log(prediction_id)

    if not prediction:
        return json_error("Prediction not found", 404)

    # Check if feedback exists
    feedback = service.get_feedback(prediction_id)

    return json_response({
        "prediction": prediction.to_dict(),
        "feedback": feedback.to_dict() if feedback else None,
    })


@feedback_bp.route("/predictions/<int:prediction_id>/feedback", methods=["POST"])
@require_auth(require_role=["admin", "technician", "operator"])
def add_feedback(prediction_id):
    """
    Add ground truth label for a prediction.
    
    Body:
        {
            "actual_defect": "degradation_roulement",
            "feedback_source": "technician",  // optional
            "notes": "Confirmed during maintenance",  // optional
            "severity": "high"  // optional
        }
    """
    body = get_json_body()
    actual_defect = body.get("actual_defect")

    if not actual_defect:
        return json_error("actual_defect is required")

    # Get current user from request context (set by @require_auth)
    current_user = request.current_user
    technician_id = current_user.get("id") if current_user else None

    service = FeedbackService()
    feedback_id = service.add_feedback(
        prediction_log_id=prediction_id,
        actual_defect=actual_defect,
        feedback_source=body.get("feedback_source", "technician"),
        technician_id=technician_id,
        notes=body.get("notes"),
        severity=body.get("severity"),
    )

    if not feedback_id:
        return json_error("Failed to add feedback. Prediction may not exist or feedback already provided.", 400)

    # Get the created feedback
    feedback = service.get_feedback(prediction_id)

    return json_response({
        "message": "Feedback added successfully",
        "feedback_id": feedback_id,
        "feedback": feedback.to_dict() if feedback else None,
    }, 201)


@feedback_bp.route("/predictions/<int:prediction_id>/feedback", methods=["GET"])
@require_auth()
def get_prediction_feedback(prediction_id):
    """Get feedback for a specific prediction."""
    service = FeedbackService()
    feedback = service.get_feedback(prediction_id)

    if not feedback:
        return json_error("Feedback not found", 404)

    return json_response(feedback.to_dict())


@feedback_bp.route("/export/training-data", methods=["GET"])
@require_auth(require_role=["admin"])
def export_training_data():
    """
    Export labeled predictions for external model retraining.
    
    This endpoint is called from Google Colab to download production data.
    
    Query params:
        - machine: Filter by machine type (optional)
        - start_date: Start date ISO format (optional)
        - end_date: End date ISO format (optional)
        - min_confidence: Minimum confidence filter (optional)
        - include_incorrect: Include wrong predictions (default: true)
        - format: Export format - 'json' or 'csv' (default: json)
    """
    machine = request.args.get("machine")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    min_confidence = request.args.get("min_confidence")
    include_incorrect = request.args.get("include_incorrect", "true").lower() == "true"
    export_format = request.args.get("format", "json").lower()

    if min_confidence:
        try:
            min_confidence = float(min_confidence)
        except ValueError:
            return json_error("min_confidence must be a number")

    service = FeedbackService()
    data = service.export_training_data(
        machine=machine,
        start_date=start_date,
        end_date=end_date,
        min_confidence=min_confidence,
        include_incorrect=include_incorrect,
    )

    if export_format == "csv":
        # Convert to CSV format for easier use in Colab
        import csv
        from io import StringIO
        
        if not data:
            return json_error("No training data available", 404)

        output = StringIO()
        
        # Flatten sensors dict for CSV
        fieldnames = [
            "prediction_id", "machine", "actual_defect", "predicted_defect",
            "is_correct", "confidence", "defect_score", "model_name",
            "timestamp", "severity", "notes"
        ]
        
        # Add sensor fields from first row
        if data:
            sensor_keys = list(data[0]["sensors"].keys())
            fieldnames.extend([f"sensor_{k}" for k in sensor_keys])
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in data:
            csv_row = {
                "prediction_id": row["prediction_id"],
                "machine": row["machine"],
                "actual_defect": row["actual_defect"],
                "predicted_defect": row["predicted_defect"],
                "is_correct": row["is_correct"],
                "confidence": row["confidence"],
                "defect_score": row["defect_score"],
                "model_name": row["model_name"],
                "timestamp": row["timestamp"],
                "severity": row["severity"],
                "notes": row["notes"],
            }
            # Add sensor values
            for k, v in row["sensors"].items():
                csv_row[f"sensor_{k}"] = v
            
            writer.writerow(csv_row)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=training_data_{machine or 'all'}.csv"
            }
        )
    
    # JSON format (default)
    return json_response({
        "data": data,
        "count": len(data),
        "machine": machine or "all",
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "min_confidence": min_confidence,
            "include_incorrect": include_incorrect,
        },
    })


@feedback_bp.route("/statistics", methods=["GET"])
@require_auth()
def get_statistics():
    """
    Get statistics about predictions and feedback.
    
    Query params:
        - machine: Filter by machine type (optional)
    """
    machine = request.args.get("machine")
    service = FeedbackService()
    stats = service.get_statistics(machine=machine)

    return json_response(stats)


@feedback_bp.route("/batch-feedback", methods=["POST"])
@require_auth(require_role=["admin", "technician"])
def add_batch_feedback():
    """
    Add feedback for multiple predictions at once.
    
    Useful for importing feedback from maintenance reports.
    
    Body:
        {
            "feedbacks": [
                {
                    "prediction_id": 123,
                    "actual_defect": "degradation_roulement",
                    "notes": "Found during inspection",
                    "severity": "high"
                },
                ...
            ]
        }
    """
    body = get_json_body()
    feedbacks = body.get("feedbacks", [])

    if not feedbacks or not isinstance(feedbacks, list):
        return json_error("feedbacks array is required")

    current_user = request.current_user
    technician_id = current_user.get("id") if current_user else None

    service = FeedbackService()
    results = {
        "success": [],
        "failed": [],
    }

    for item in feedbacks:
        prediction_id = item.get("prediction_id")
        actual_defect = item.get("actual_defect")

        if not prediction_id or not actual_defect:
            results["failed"].append({
                "prediction_id": prediction_id,
                "error": "Missing prediction_id or actual_defect"
            })
            continue

        feedback_id = service.add_feedback(
            prediction_log_id=prediction_id,
            actual_defect=actual_defect,
            feedback_source=item.get("feedback_source", "technician"),
            technician_id=technician_id,
            notes=item.get("notes"),
            severity=item.get("severity"),
        )

        if feedback_id:
            results["success"].append({
                "prediction_id": prediction_id,
                "feedback_id": feedback_id,
            })
        else:
            results["failed"].append({
                "prediction_id": prediction_id,
                "error": "Failed to add feedback"
            })

    return json_response({
        "message": f"Processed {len(feedbacks)} feedbacks",
        "success_count": len(results["success"]),
        "failed_count": len(results["failed"]),
        "results": results,
    })
