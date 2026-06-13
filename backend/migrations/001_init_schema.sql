-- ============================================================================
-- LLM Observability Dashboard - Initial Schema
-- Version: 1.0.0
-- Description: Core tables for LLM request tracking, evaluation, and metadata
-- ============================================================================

-- Drop existing tables (if they exist)
-- WARNING: This will delete all data!
-- DROP TABLE IF EXISTS eval_results CASCADE;
-- DROP TABLE IF EXISTS completions CASCADE;
-- DROP TABLE IF EXISTS traces CASCADE;
-- DROP TABLE IF EXISTS metrics CASCADE;
-- DROP TABLE IF EXISTS models CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;

-- ============================================================================
-- USERS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE,
    api_key_hash VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    CONSTRAINT users_email_format CHECK (email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================================
-- MODELS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL, -- 'anthropic', 'openai', 'meta', 'google', etc.
    version VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);

-- ============================================================================
-- COMPLETIONS TABLE (LLM Requests & Responses)
-- ============================================================================
CREATE TABLE IF NOT EXISTS completions (
    id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(100),
    model VARCHAR(100) NOT NULL,

    -- Input/Output content (optional - for privacy, may store hashes only)
    prompt TEXT,
    prompt_hash VARCHAR(64), -- SHA-256 hash for privacy
    response TEXT,
    response_hash VARCHAR(64),

    -- Token metrics
    prompt_tokens INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    total_tokens INT GENERATED ALWAYS AS (prompt_tokens + completion_tokens) STORED,

    -- Performance metrics
    latency_ms FLOAT,
    time_to_first_token_ms FLOAT,

    -- Cost tracking
    cost_usd FLOAT DEFAULT 0.0,

    -- Model parameters
    temperature FLOAT,
    max_tokens INT,
    top_p FLOAT,

    -- Status & Error tracking
    success BOOLEAN DEFAULT TRUE,
    error_code VARCHAR(50),
    error_message TEXT,

    -- Timestamps
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT completions_tokens_positive CHECK (prompt_tokens >= 0 AND completion_tokens >= 0),
    CONSTRAINT completions_latency_positive CHECK (latency_ms >= 0),
    CONSTRAINT completions_cost_positive CHECK (cost_usd >= 0),
    CONSTRAINT completions_temperature_valid CHECK (temperature IS NULL OR (temperature >= 0 AND temperature <= 2))
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_completions_timestamp ON completions(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_completions_model ON completions(model);
CREATE INDEX IF NOT EXISTS idx_completions_user_id ON completions(user_id);
CREATE INDEX IF NOT EXISTS idx_completions_conversation_id ON completions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_completions_success ON completions(success);
CREATE INDEX IF NOT EXISTS idx_completions_user_timestamp ON completions(user_id, timestamp DESC);

-- Optional: TimescaleDB hypertable for time-series optimization
-- SELECT create_hypertable('completions', 'timestamp', if_not_exists => TRUE);

-- ============================================================================
-- TRACES TABLE (Distributed Tracing)
-- ============================================================================
CREATE TABLE IF NOT EXISTS traces (
    id VARCHAR(50) PRIMARY KEY,
    completion_id INT REFERENCES completions(id) ON DELETE CASCADE,
    parent_trace_id VARCHAR(50),

    -- Trace metadata
    trace_name VARCHAR(255),
    trace_type VARCHAR(50), -- 'request', 'span', 'event'
    span_name VARCHAR(255),

    -- Timing
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms FLOAT GENERATED ALWAYS AS (EXTRACT(EPOCH FROM (end_time - start_time)) * 1000) STORED,

    -- Trace data (JSON)
    trace_data JSONB,
    attributes JSONB,
    events JSONB,

    -- Status
    status VARCHAR(20), -- 'unset', 'ok', 'error'
    error_message TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT traces_end_after_start CHECK (end_time >= start_time)
);

CREATE INDEX IF NOT EXISTS idx_traces_completion_id ON traces(completion_id);
CREATE INDEX IF NOT EXISTS idx_traces_parent_trace_id ON traces(parent_trace_id);
CREATE INDEX IF NOT EXISTS idx_traces_start_time ON traces(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_traces_trace_data ON traces USING GIN (trace_data);

-- ============================================================================
-- EVALUATION RESULTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS eval_results (
    id SERIAL PRIMARY KEY,
    completion_id INT NOT NULL REFERENCES completions(id) ON DELETE CASCADE,

    -- Evaluation metadata
    eval_type VARCHAR(50) NOT NULL, -- 'llm_judge', 'bleu', 'rouge', 'semantic_similarity'
    eval_model VARCHAR(100), -- Model used for evaluation (if applicable)

    -- Scores (0-1 normalized)
    score FLOAT,
    raw_score FLOAT,

    -- Evaluation details
    criteria VARCHAR(255), -- What was evaluated
    explanation TEXT, -- Why this score
    eval_data JSONB, -- Additional evaluation data

    -- Metadata
    evaluator VARCHAR(100), -- Who/what evaluated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT eval_results_score_range CHECK (score IS NULL OR (score >= 0 AND score <= 1)),
    CONSTRAINT eval_results_raw_score_positive CHECK (raw_score IS NULL OR raw_score >= 0)
);

CREATE INDEX IF NOT EXISTS idx_eval_results_completion_id ON eval_results(completion_id);
CREATE INDEX IF NOT EXISTS idx_eval_results_eval_type ON eval_results(eval_type);
CREATE INDEX IF NOT EXISTS idx_eval_results_created_at ON eval_results(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_eval_results_score ON eval_results(score DESC);

-- ============================================================================
-- METRICS TABLE (Aggregated Metrics & Analytics)
-- ============================================================================
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,

    -- Metric metadata
    metric_name VARCHAR(100) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'gauge', 'counter', 'histogram', 'summary'

    -- Values
    metric_value FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    avg_value FLOAT,

    -- Dimensions/Tags
    model VARCHAR(100),
    user_id VARCHAR(100),
    provider VARCHAR(50),

    -- Time window (for aggregated metrics)
    window_start TIMESTAMP,
    window_end TIMESTAMP,

    -- Timestamps
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT metrics_valid_values CHECK (metric_value IS NULL OR (min_value IS NULL OR min_value <= max_value))
);

CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_recorded_at ON metrics(recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_metrics_model ON metrics(model);
CREATE INDEX IF NOT EXISTS idx_metrics_user_id ON metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_metrics_window ON metrics(window_start, window_end);

-- ============================================================================
-- ALERTS TABLE
-- ============================================================================
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,

    -- Alert metadata
    alert_name VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50), -- 'threshold', 'anomaly', 'error_rate'
    severity VARCHAR(20), -- 'info', 'warning', 'critical'

    -- Trigger
    triggered_condition VARCHAR(255),
    threshold_value FLOAT,

    -- Related metrics
    completion_id INT REFERENCES completions(id) ON DELETE SET NULL,
    metric_name VARCHAR(100),
    metric_value FLOAT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_resolved BOOLEAN DEFAULT FALSE,

    -- Timestamps
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT alerts_resolved_after_triggered CHECK (resolved_at IS NULL OR resolved_at >= triggered_at)
);

CREATE INDEX IF NOT EXISTS idx_alerts_triggered_at ON alerts(triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_is_active ON alerts(is_active);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- ============================================================================
-- CACHE/SESSION TABLE (optional)
-- ============================================================================
CREATE TABLE IF NOT EXISTS sessions (
    id VARCHAR(100) PRIMARY KEY,
    user_id VARCHAR(100) REFERENCES users(user_id) ON DELETE CASCADE,
    session_data JSONB,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT sessions_future_expiry CHECK (expires_at > CURRENT_TIMESTAMP)
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);

-- ============================================================================
-- AUDIT LOG TABLE (optional - for compliance)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id INT,
    changes JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);

-- ============================================================================
-- MATERIALIZED VIEWS (for analytics queries)
-- ============================================================================

-- Daily model performance summary
CREATE MATERIALIZED VIEW IF NOT EXISTS model_daily_performance AS
SELECT
    DATE(timestamp) as date,
    model,
    COUNT(*) as request_count,
    AVG(latency_ms) as avg_latency,
    MIN(latency_ms) as min_latency,
    MAX(latency_ms) as max_latency,
    SUM(cost_usd) as total_cost,
    COUNT(CASE WHEN success = TRUE THEN 1 END) as success_count,
    ROUND(100.0 * COUNT(CASE WHEN success = TRUE THEN 1 END) / COUNT(*), 2) as success_rate,
    AVG(prompt_tokens) as avg_prompt_tokens,
    AVG(completion_tokens) as avg_completion_tokens
FROM completions
GROUP BY DATE(timestamp), model;

CREATE INDEX IF NOT EXISTS idx_model_daily_date ON model_daily_performance(date DESC);

-- User daily usage summary
CREATE MATERIALIZED VIEW IF NOT EXISTS user_daily_usage AS
SELECT
    DATE(timestamp) as date,
    user_id,
    COUNT(*) as request_count,
    SUM(prompt_tokens + completion_tokens) as total_tokens,
    SUM(cost_usd) as total_cost,
    COUNT(DISTINCT model) as unique_models,
    ROUND(100.0 * COUNT(CASE WHEN success = TRUE THEN 1 END) / COUNT(*), 2) as success_rate
FROM completions
WHERE user_id IS NOT NULL
GROUP BY DATE(timestamp), user_id;

CREATE INDEX IF NOT EXISTS idx_user_daily_date ON user_daily_usage(date DESC);

-- ============================================================================
-- STORED PROCEDURES/FUNCTIONS
-- ============================================================================

-- Function: Get model statistics for a given time period
CREATE OR REPLACE FUNCTION get_model_stats(
    p_model VARCHAR,
    p_start_date TIMESTAMP,
    p_end_date TIMESTAMP
) RETURNS TABLE (
    metric_name VARCHAR,
    metric_value FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'request_count'::VARCHAR, COUNT(*)::FLOAT
    FROM completions
    WHERE model = p_model AND timestamp BETWEEN p_start_date AND p_end_date
    UNION ALL
    SELECT 'avg_latency', AVG(latency_ms)::FLOAT
    FROM completions
    WHERE model = p_model AND timestamp BETWEEN p_start_date AND p_end_date
    UNION ALL
    SELECT 'total_cost', SUM(cost_usd)::FLOAT
    FROM completions
    WHERE model = p_model AND timestamp BETWEEN p_start_date AND p_end_date
    UNION ALL
    SELECT 'success_rate', (COUNT(CASE WHEN success = TRUE THEN 1 END)::FLOAT / COUNT(*) * 100)::FLOAT
    FROM completions
    WHERE model = p_model AND timestamp BETWEEN p_start_date AND p_end_date;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS & DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE completions IS 'Core table for LLM API requests and responses';
COMMENT ON TABLE eval_results IS 'Evaluation scores and feedback for completions';
COMMENT ON TABLE traces IS 'Distributed tracing data for request flows';
COMMENT ON TABLE metrics IS 'Aggregated metrics and time-series data';
COMMENT ON TABLE alerts IS 'Alert events triggered by monitoring rules';
COMMENT ON TABLE users IS 'Dashboard users and API key holders';
COMMENT ON TABLE models IS 'Metadata about available LLM models';

COMMENT ON COLUMN completions.prompt_hash IS 'SHA-256 hash of prompt for privacy';
COMMENT ON COLUMN completions.conversation_id IS 'Group related requests into conversations';
COMMENT ON COLUMN completions.total_tokens IS 'Auto-calculated: prompt_tokens + completion_tokens';
COMMENT ON COLUMN eval_results.score IS 'Normalized score 0-1 (for consistency across eval types)';
COMMENT ON COLUMN traces.duration_ms IS 'Auto-calculated: time difference in milliseconds';

-- ============================================================================
-- GRANTS (if using roles)
-- ============================================================================
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO app_role;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_role;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
-- Version: 1.0.0
-- Created: 2026-06-11
-- Status: Production-ready
