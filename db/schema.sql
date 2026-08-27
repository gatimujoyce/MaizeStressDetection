-- Core persistence schema for the Maize Stress Detection and Monitoring System.
-- PostgreSQL 13+ (uses built-in gen_random_uuid(), no extension required).

-- ============================================================
-- USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    phone_number TEXT UNIQUE,
    email TEXT UNIQUE,
    role TEXT NOT NULL DEFAULT 'farmer'
        CHECK (role IN ('farmer', 'admin')),
    preferred_language TEXT NOT NULL DEFAULT 'en',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- FARMS
-- soil_type, planting_date, has_npk_sensor live here — static,
-- onboarding-time attributes, not per-reading values.
-- ============================================================
CREATE TABLE IF NOT EXISTS farms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    name TEXT NOT NULL,
    location_lat DOUBLE PRECISION,
    location_lng DOUBLE PRECISION,
    soil_type TEXT NOT NULL
        CHECK (soil_type IN ('sandy_loam', 'clay', 'loam', 'silt_loam')),
    planting_date DATE,
    has_npk_sensor BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE,
    UNIQUE (owner_id, name)
);

-- ============================================================
-- SENSOR DEVICES
-- Represents a physical unit registered to a farm. device_type
-- distinguishes the core (moisture/temp/humidity) unit from the
-- optional NPK unit, so both are modeled consistently.
-- ============================================================
CREATE TABLE IF NOT EXISTS sensor_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL,
    device_identifier TEXT NOT NULL UNIQUE,
    device_type TEXT NOT NULL DEFAULT 'core'
        CHECK (device_type IN ('core', 'npk')),
    installed_at TIMESTAMPTZ,
    active BOOLEAN NOT NULL DEFAULT true,
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE
);

-- ============================================================
-- SENSOR READINGS (core unit: moisture, temp, humidity, leaf wetness)
-- growth_stage is farmer-reported at each check-in (Option A+C).
-- soil_type intentionally NOT here — it belongs to farms.
-- ============================================================
CREATE TABLE IF NOT EXISTS sensor_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,
    farm_id UUID NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    soil_moisture REAL,
    temperature_c REAL,
    humidity_percent REAL,
    leaf_wetness_proxy REAL,          -- derived (dew-point calc from temp+humidity), not farmer-submitted
    growth_stage TEXT
        CHECK (growth_stage IN ('V4', 'V6', 'V11', 'flowering', 'grain_filling', 'maturity')),
    FOREIGN KEY (device_id) REFERENCES sensor_devices (id) ON DELETE CASCADE,
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE
);

-- ============================================================
-- NPK READINGS (optional — only populated if farms.has_npk_sensor = true)
-- ============================================================
CREATE TABLE IF NOT EXISTS npk_readings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL,
    farm_id UUID NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    nitrogen REAL,
    phosphorus REAL,
    potassium REAL,
    zinc REAL,
    FOREIGN KEY (device_id) REFERENCES sensor_devices (id) ON DELETE CASCADE,
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE
);

-- ============================================================
-- LEAF IMAGES
-- Logged independently of any prediction, so gate rejections
-- and raw submissions are auditable on their own.
-- ============================================================
CREATE TABLE IF NOT EXISTS leaf_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL,
    image_uri TEXT NOT NULL,
    gate_passed BOOLEAN,               -- result of leaf/not-leaf rejection gate; NULL until processed
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE
);

-- ============================================================
-- STRESS PREDICTIONS (core fusion output ONLY)
-- fused_prediction combines disease_prediction + sensor_prediction.
-- Nutrient predictions are NEVER part of this fusion — see below.
-- ============================================================
CREATE TABLE IF NOT EXISTS stress_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL,
    reading_id UUID,                   -- which sensor reading fed this prediction
    image_id UUID,                     -- which leaf image fed this prediction
    disease_prediction TEXT
        CHECK (disease_prediction IN ('healthy', 'common_rust', 'northern_leaf_blight', 'gray_leaf_spot')),
    sensor_prediction TEXT
        CHECK (sensor_prediction IN ('normal', 'drought_stress', 'heat_stress', 'waterlogging_risk')),
    fused_prediction TEXT NOT NULL,    -- combined output of disease_prediction + sensor_prediction ONLY
    severity_level TEXT
        CHECK (severity_level IN ('low', 'medium', 'high')),
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    status TEXT NOT NULL DEFAULT 'confirmed'
        CHECK (status IN ('confirmed', 'uncertain')),  -- 'uncertain' = below confidence threshold, no alert generated
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE,
    FOREIGN KEY (reading_id) REFERENCES sensor_readings (id) ON DELETE SET NULL,
    FOREIGN KEY (image_id) REFERENCES leaf_images (id) ON DELETE SET NULL
);

-- ============================================================
-- NUTRIENT PREDICTIONS (separate output head — architecturally
-- independent of stress_predictions/fusion, per design decision)
-- ============================================================
CREATE TABLE IF NOT EXISTS nutrient_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL,
    image_id UUID NOT NULL,
    npk_reading_id UUID,               -- optional confirmatory sensor input, nullable
    deficiency_class TEXT NOT NULL
        CHECK (deficiency_class IN ('no_deficiency', 'nitrogen', 'phosphorus', 'potassium', 'zinc')),
    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE,
    FOREIGN KEY (image_id) REFERENCES leaf_images (id) ON DELETE CASCADE,
    FOREIGN KEY (npk_reading_id) REFERENCES npk_readings (id) ON DELETE SET NULL
);

-- ============================================================
-- ALERTS
-- References stress_predictions specifically (nutrient predictions
-- are displayed on the dashboard but do not currently trigger alerts).
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    farm_id UUID NOT NULL,
    stress_prediction_id UUID,
    severity TEXT NOT NULL
        CHECK (severity IN ('low', 'medium', 'high')),
    message TEXT NOT NULL,
    sms_sent BOOLEAN NOT NULL DEFAULT false,
    sms_sent_at TIMESTAMPTZ,
    acknowledged_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (farm_id) REFERENCES farms (id) ON DELETE CASCADE,
    FOREIGN KEY (stress_prediction_id) REFERENCES stress_predictions (id) ON DELETE SET NULL
);

-- ============================================================
-- FEEDBACK LOG
-- Farmer confirm/correct on alerts. Logged for future retraining
-- work; no automated retraining pipeline in this build (validation-
-- only approach — see architecture_decision_log.md).
-- ============================================================
CREATE TABLE IF NOT EXISTS feedback_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id UUID NOT NULL,
    user_id UUID NOT NULL,
    confirmed BOOLEAN NOT NULL,
    correction TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (alert_id) REFERENCES alerts (id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ============================================================
-- INDEXES — support trend/history dashboard queries and
-- response-time evaluation
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_sensor_readings_farm_recorded_at
    ON sensor_readings (farm_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_npk_readings_farm_recorded_at
    ON npk_readings (farm_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_leaf_images_farm_created_at
    ON leaf_images (farm_id, created_at);

CREATE INDEX IF NOT EXISTS idx_stress_predictions_farm_created_at
    ON stress_predictions (farm_id, created_at);

CREATE INDEX IF NOT EXISTS idx_nutrient_predictions_farm_created_at
    ON nutrient_predictions (farm_id, created_at);

CREATE INDEX IF NOT EXISTS idx_alerts_farm_created_at
    ON alerts (farm_id, created_at);