# ---------------------------------------------------------------------------
# IoT service — SQL queries
# ---------------------------------------------------------------------------

IOT_MQTT_CONFIG_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS iot_mqtt_config (
        id SERIAL PRIMARY KEY,
        plant_id INTEGER NOT NULL UNIQUE,
        host VARCHAR(255) NOT NULL DEFAULT 'localhost',
        port INTEGER NOT NULL DEFAULT 1883,
        username VARCHAR(255),
        password VARCHAR(255),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );
"""

IOT_SENSOR_CONFIG_CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS iot_sensor_config (
        id SERIAL PRIMARY KEY,
        plant_id INTEGER NOT NULL,
        machine VARCHAR(64) NOT NULL,
        sensor_name VARCHAR(128) NOT NULL,
        unit VARCHAR(32) NOT NULL DEFAULT '',
        min_value DOUBLE PRECISION NOT NULL DEFAULT 0,
        max_value DOUBLE PRECISION NOT NULL DEFAULT 100,
        enabled BOOLEAN NOT NULL DEFAULT TRUE,
        updated_at TIMESTAMPTZ DEFAULT NOW(),
        UNIQUE (plant_id, machine, sensor_name)
    );
"""

IOT_MQTT_SELECT_BY_PLANT = """
    SELECT id, plant_id, host, port, username, password, updated_at
    FROM iot_mqtt_config
    WHERE plant_id = %s;
"""

IOT_MQTT_UPSERT = """
    INSERT INTO iot_mqtt_config (plant_id, host, port, username, password, updated_at)
    VALUES (%s, %s, %s, %s, %s, NOW())
    ON CONFLICT (plant_id) DO UPDATE
    SET host = EXCLUDED.host,
        port = EXCLUDED.port,
        username = EXCLUDED.username,
        password = EXCLUDED.password,
        updated_at = NOW()
    RETURNING id, plant_id, host, port, username, password, updated_at;
"""

IOT_SENSOR_SELECT_BY_PLANT = """
    SELECT id, plant_id, machine, sensor_name, unit, min_value, max_value, enabled, updated_at
    FROM iot_sensor_config
    WHERE plant_id = %s
    ORDER BY machine ASC, sensor_name ASC;
"""

IOT_SENSOR_UPSERT = """
    INSERT INTO iot_sensor_config
        (plant_id, machine, sensor_name, unit, min_value, max_value, enabled, updated_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (plant_id, machine, sensor_name) DO UPDATE
    SET unit = EXCLUDED.unit,
        min_value = EXCLUDED.min_value,
        max_value = EXCLUDED.max_value,
        enabled = EXCLUDED.enabled,
        updated_at = NOW()
    RETURNING id, plant_id, machine, sensor_name, unit, min_value, max_value, enabled, updated_at;
"""
