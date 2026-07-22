-- Migration: Prediction Logging for Fine-Tuning
-- Purpose: Store ML predictions and ground truth labels for model retraining
-- Date: 2026-07-20

-- ============================================================
-- Table: prediction_log
-- Purpose: Log every ML prediction with sensor inputs and outputs
-- ============================================================
CREATE TABLE IF NOT EXISTS prediction_log (
    id SERIAL PRIMARY KEY,
    machine VARCHAR(50) NOT NULL,
    plant_id INTEGER,
    component_id INTEGER,
    sensors JSONB NOT NULL,  -- Raw sensor readings (input)
    predicted_defect VARCHAR(100) NOT NULL,  -- Model prediction
    defect_score REAL NOT NULL,  -- Overall defect probability
    confidence REAL NOT NULL,  -- Prediction confidence
    defect_scores JSONB NOT NULL,  -- Per-class probabilities
    model_name VARCHAR(100) NOT NULL,  -- Model version used
    timestamp TIMESTAMPTZ NOT NULL,  -- When prediction was made
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_prediction_log_machine ON prediction_log(machine);
CREATE INDEX IF NOT EXISTS idx_prediction_log_timestamp ON prediction_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_prediction_log_plant ON prediction_log(plant_id);
CREATE INDEX IF NOT EXISTS idx_prediction_log_component ON prediction_log(component_id);
CREATE INDEX IF NOT EXISTS idx_prediction_log_created_at ON prediction_log(created_at);

-- ============================================================
-- Table: prediction_feedback
-- Purpose: Ground truth labels from technicians/maintenance reports
-- ============================================================
CREATE TABLE IF NOT EXISTS prediction_feedback (
    id SERIAL PRIMARY KEY,
    prediction_log_id INTEGER NOT NULL REFERENCES prediction_log(id) ON DELETE CASCADE,
    actual_defect VARCHAR(100) NOT NULL,  -- Ground truth label
    is_correct BOOLEAN NOT NULL,  -- Was the prediction correct?
    feedback_source VARCHAR(50) NOT NULL,  -- 'technician', 'maintenance_report', 'auto'
    technician_id INTEGER,  -- User who provided feedback
    notes TEXT,  -- Additional context
    severity VARCHAR(20),  -- 'low', 'medium', 'high', 'critical'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_prediction_feedback_log ON prediction_feedback(prediction_log_id);
CREATE INDEX IF NOT EXISTS idx_prediction_feedback_created_at ON prediction_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_prediction_feedback_technician ON prediction_feedback(technician_id);

-- Ensure only one feedback per prediction
CREATE UNIQUE INDEX IF NOT EXISTS idx_prediction_feedback_unique 
    ON prediction_feedback(prediction_log_id);

-- ============================================================
-- View: training_data_export
-- Purpose: Join predictions with feedback for easy export
-- ============================================================
CREATE OR REPLACE VIEW training_data_export AS
SELECT 
    pl.id AS prediction_id,
    pl.machine,
    pl.plant_id,
    pl.component_id,
    pl.sensors,
    pl.predicted_defect,
    pl.defect_score,
    pl.confidence,
    pl.defect_scores,
    pl.model_name,
    pl.timestamp,
    pf.actual_defect,
    pf.is_correct,
    pf.feedback_source,
    pf.technician_id,
    pf.notes,
    pf.severity,
    pf.created_at AS feedback_created_at
FROM prediction_log pl
INNER JOIN prediction_feedback pf ON pl.id = pf.prediction_log_id;

COMMENT ON TABLE prediction_log IS 'Logs all ML predictions for fine-tuning and analysis';
COMMENT ON TABLE prediction_feedback IS 'Ground truth labels for predictions (used in model retraining)';
COMMENT ON VIEW training_data_export IS 'Combined view of predictions + feedback for export to Colab';
