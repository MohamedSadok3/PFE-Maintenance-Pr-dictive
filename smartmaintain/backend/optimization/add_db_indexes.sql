-- SmartMaintain Database Performance Optimization
-- Execute this script to add missing indexes
-- Estimated performance improvement: 5-10x faster queries

-- ============================================
-- Users Table Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_users_plant_id 
ON users(plant_id);

CREATE INDEX IF NOT EXISTS idx_users_role 
ON users(role);

CREATE INDEX IF NOT EXISTS idx_users_verified 
ON users(verified);

COMMENT ON INDEX idx_users_plant_id IS 'Speed up user filtering by plant';
COMMENT ON INDEX idx_users_role IS 'Speed up RBAC queries';

-- ============================================
-- Components Table Indexes
-- ============================================

CREATE INDEX IF NOT EXISTS idx_components_plant_id 
ON components(plant_id);

CREATE INDEX IF NOT EXISTS idx_components_type 
ON components(type);

CREATE INDEX IF NOT EXISTS idx_components_enabled 
ON components(enabled);

CREATE INDEX IF NOT EXISTS idx_components_plant_type 
ON components(plant_id, type);

COMMENT ON INDEX idx_components_plant_type IS 'Composite index for plant+type queries';

-- ============================================
-- Alerts Table Indexes (Most Important)
-- ============================================

-- Status index (most queried field)
CREATE INDEX IF NOT EXISTS idx_alerts_status 
ON alerts(status);

-- Plant filtering
CREATE INDEX IF NOT EXISTS idx_alerts_plant_id 
ON alerts(plant_id);

-- Component filtering
CREATE INDEX IF NOT EXISTS idx_alerts_component_id 
ON alerts(component_id);

-- Time-based queries (dashboard, history)
CREATE INDEX IF NOT EXISTS idx_alerts_start_time 
ON alerts(start_time DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_end_time 
ON alerts(end_time DESC) WHERE end_time IS NOT NULL;

-- Severity filtering (dashboard)
CREATE INDEX IF NOT EXISTS idx_alerts_severity 
ON alerts(severity);

-- Machine type filtering
CREATE INDEX IF NOT EXISTS idx_alerts_machine 
ON alerts(machine);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_alerts_status_plant 
ON alerts(status, plant_id);

CREATE INDEX IF NOT EXISTS idx_alerts_status_severity 
ON alerts(status, severity);

CREATE INDEX IF NOT EXISTS idx_alerts_plant_start_time 
ON alerts(plant_id, start_time DESC);

COMMENT ON INDEX idx_alerts_status IS 'Most queried field - active vs resolved';
COMMENT ON INDEX idx_alerts_plant_start_time IS 'Dashboard timeline queries';

-- ============================================
-- Foreign Key Constraints (Data Integrity)
-- ============================================

-- Users → Plants
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_users_plant'
    ) THEN
        ALTER TABLE users 
        ADD CONSTRAINT fk_users_plant 
        FOREIGN KEY (plant_id) 
        REFERENCES plants(id) 
        ON DELETE SET NULL;
    END IF;
END $$;

-- Components → Plants
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_components_plant'
    ) THEN
        ALTER TABLE components 
        ADD CONSTRAINT fk_components_plant 
        FOREIGN KEY (plant_id) 
        REFERENCES plants(id) 
        ON DELETE CASCADE;
    END IF;
END $$;

-- Alerts → Components
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_alerts_component'
    ) THEN
        ALTER TABLE alerts 
        ADD CONSTRAINT fk_alerts_component 
        FOREIGN KEY (component_id) 
        REFERENCES components(id) 
        ON DELETE SET NULL;
    END IF;
END $$;

-- Alerts → Plants
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'fk_alerts_plant'
    ) THEN
        ALTER TABLE alerts 
        ADD CONSTRAINT fk_alerts_plant 
        FOREIGN KEY (plant_id) 
        REFERENCES plants(id) 
        ON DELETE CASCADE;
    END IF;
END $$;

-- ============================================
-- Analyze Tables (Update Statistics)
-- ============================================

ANALYZE users;
ANALYZE plants;
ANALYZE components;
ANALYZE alerts;

-- ============================================
-- Verification Queries
-- ============================================

-- Show all indexes
SELECT 
    tablename, 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE schemaname = 'public' 
ORDER BY tablename, indexname;

-- Show foreign keys
SELECT
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;

-- Show table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    pg_total_relation_size(schemaname||'.'||tablename) AS size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY size_bytes DESC;
