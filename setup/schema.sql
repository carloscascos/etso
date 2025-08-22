-- OBSERVATORIO ETS Database Schema
-- ETSO Database (etso_db) - Full access for research findings storage

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS etso_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE etso_db;

-- Drop tables in correct order (respecting foreign keys)
DROP TABLE IF EXISTS validation_claims;
DROP TABLE IF EXISTS quarterly_reports;
DROP TABLE IF EXISTS research_metadata;
DROP TABLE IF EXISTS system_config;

-- Research findings metadata table
CREATE TABLE research_metadata (
    id INT AUTO_INCREMENT PRIMARY KEY,
    chroma_id VARCHAR(100) UNIQUE NOT NULL,
    quarter VARCHAR(10) NOT NULL,
    theme_type ENUM(
        'eu_ets', 
        'routes', 
        'geopolitical', 
        'carrier', 
        'regional', 
        'data_insight'
    ) NOT NULL,
    user_guidance TEXT,
    enhanced_query TEXT,
    research_content_preview TEXT,
    validation_score DECIMAL(4,3) DEFAULT NULL,
    overall_confidence DECIMAL(4,3) DEFAULT NULL,
    status ENUM(
        'pending', 
        'researching', 
        'validating', 
        'completed', 
        'failed'
    ) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_quarter (quarter),
    INDEX idx_theme_type (theme_type),
    INDEX idx_status (status),
    INDEX idx_confidence (overall_confidence),
    INDEX idx_created_at (created_at),
    INDEX idx_chroma_lookup (chroma_id, quarter)
);

-- Validation results for individual claims extracted from research
CREATE TABLE validation_claims (
    id INT AUTO_INCREMENT PRIMARY KEY,
    research_metadata_id INT NOT NULL,
    claim_text TEXT NOT NULL,
    claim_type ENUM(
        'vessel_movement', 
        'fuel_consumption', 
        'transit_time', 
        'route_pattern', 
        'port_frequency',
        'service_change',
        'general'
    ) NOT NULL,
    vessel_filter VARCHAR(255),
    route_filter VARCHAR(255),
    period_filter VARCHAR(100),
    validation_query TEXT,
    validation_logic TEXT COMMENT 'Semantic meaning of the validation query - explains how it validates or refutes the claim',
    confidence_score DECIMAL(4,3) DEFAULT NULL,
    supports_claim BOOLEAN DEFAULT NULL,
    data_points_found INT DEFAULT 0,
    analysis_text TEXT,
    validation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (research_metadata_id) 
        REFERENCES research_metadata(id) 
        ON DELETE CASCADE,
    
    INDEX idx_research_id (research_metadata_id),
    INDEX idx_claim_type (claim_type),
    INDEX idx_confidence (confidence_score),
    INDEX idx_supports (supports_claim),
    INDEX idx_validation_time (validation_timestamp)
);

-- Quarterly report generation metadata
CREATE TABLE quarterly_reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quarter VARCHAR(10) NOT NULL,
    report_title VARCHAR(255),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_status ENUM('generating', 'completed', 'failed') DEFAULT 'generating',
    total_findings INT DEFAULT 0,
    validated_findings INT DEFAULT 0,
    average_confidence DECIMAL(4,3),
    high_confidence_findings INT DEFAULT 0,
    report_file_path VARCHAR(500),
    report_summary TEXT,
    generation_time_seconds INT DEFAULT NULL,
    
    UNIQUE KEY unique_quarter (quarter),
    INDEX idx_quarter (quarter),
    INDEX idx_status (report_status),
    INDEX idx_generated_at (generated_at)
);

-- System configuration and settings
CREATE TABLE system_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    config_type ENUM('string', 'integer', 'decimal', 'boolean', 'json') DEFAULT 'string',
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_key (config_key),
    INDEX idx_active (is_active)
);

-- Data insights discovered from traffic analysis
CREATE TABLE data_insights (
    id INT AUTO_INCREMENT PRIMARY KEY,
    quarter VARCHAR(10) NOT NULL,
    insight_type ENUM(
        'route_deviation',
        'fuel_anomaly', 
        'frequency_change',
        'corridor_shift',
        'seasonal_pattern'
    ) NOT NULL,
    insight_title VARCHAR(255) NOT NULL,
    insight_description TEXT,
    affected_vessels TEXT, -- JSON array of IMO numbers
    affected_routes TEXT,  -- JSON array of route patterns
    quantitative_data JSON, -- Structured data about the insight
    confidence_level DECIMAL(4,3) DEFAULT NULL,
    research_triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_quarter (quarter),
    INDEX idx_type (insight_type),
    INDEX idx_confidence (confidence_level),
    INDEX idx_created (created_at)
);

-- Insert default system configuration
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('current_quarter', '2025Q1', 'string', 'Current quarter being analyzed'),
('validation_threshold', '0.7', 'decimal', 'Minimum confidence score for validated findings'),
('max_research_topics', '10', 'integer', 'Maximum research topics per quarter'),
('chroma_collection', 'observatorio_research', 'string', 'ChromaDB collection name'),
('openai_model', 'gpt-4', 'string', 'OpenAI model for research and analysis'),
('enable_auto_validation', 'true', 'boolean', 'Automatically validate research findings'),
('max_validation_queries', '5', 'integer', 'Maximum validation queries per claim'),
('report_generation_enabled', 'true', 'boolean', 'Enable automatic report generation');

-- Create views for common queries
CREATE VIEW research_summary AS
SELECT 
    quarter,
    theme_type,
    COUNT(*) as total_findings,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_findings,
    COUNT(CASE WHEN overall_confidence >= 0.8 THEN 1 END) as high_confidence,
    COUNT(CASE WHEN overall_confidence >= 0.5 THEN 1 END) as medium_confidence,
    AVG(overall_confidence) as avg_confidence,
    MAX(updated_at) as last_updated
FROM research_metadata
GROUP BY quarter, theme_type;

CREATE VIEW validation_summary AS
SELECT 
    rm.quarter,
    rm.theme_type,
    COUNT(vc.id) as total_claims,
    COUNT(CASE WHEN vc.supports_claim = TRUE THEN 1 END) as supported_claims,
    COUNT(CASE WHEN vc.confidence_score >= 0.8 THEN 1 END) as high_confidence_claims,
    AVG(vc.confidence_score) as avg_claim_confidence,
    AVG(vc.data_points_found) as avg_data_points
FROM research_metadata rm
LEFT JOIN validation_claims vc ON rm.id = vc.research_metadata_id
GROUP BY rm.quarter, rm.theme_type;

-- Create stored procedures for common operations
DELIMITER //

CREATE PROCEDURE GetQuarterlySummary(IN target_quarter VARCHAR(10))
BEGIN
    SELECT 
        'Research Summary' as report_section,
        quarter,
        theme_type,
        total_findings,
        completed_findings,
        high_confidence,
        avg_confidence,
        last_updated
    FROM research_summary 
    WHERE quarter = target_quarter
    
    UNION ALL
    
    SELECT 
        'Validation Summary' as report_section,
        quarter,
        theme_type,
        CAST(total_claims as DECIMAL(10,3)) as total_findings,
        CAST(supported_claims as DECIMAL(10,3)) as completed_findings,
        CAST(high_confidence_claims as DECIMAL(10,3)) as high_confidence,
        avg_claim_confidence as avg_confidence,
        NULL as last_updated
    FROM validation_summary 
    WHERE quarter = target_quarter
    
    ORDER BY report_section, theme_type;
END //

CREATE PROCEDURE UpdateResearchStatus(
    IN research_id INT,
    IN new_status VARCHAR(50),
    IN confidence_score DECIMAL(4,3)
)
BEGIN
    UPDATE research_metadata 
    SET 
        status = new_status,
        overall_confidence = COALESCE(confidence_score, overall_confidence),
        updated_at = NOW()
    WHERE id = research_id;
    
    SELECT ROW_COUNT() as affected_rows;
END //

DELIMITER ;

-- Create triggers for audit logging
CREATE TABLE audit_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    table_name VARCHAR(50),
    operation VARCHAR(10),
    record_id INT,
    old_values JSON,
    new_values JSON,
    changed_by VARCHAR(100) DEFAULT USER(),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_table_operation (table_name, operation),
    INDEX idx_changed_at (changed_at)
);

DELIMITER //

CREATE TRIGGER research_metadata_audit_update
AFTER UPDATE ON research_metadata
FOR EACH ROW
BEGIN
    INSERT INTO audit_log (table_name, operation, record_id, old_values, new_values)
    VALUES (
        'research_metadata', 
        'UPDATE', 
        NEW.id,
        JSON_OBJECT(
            'status', OLD.status,
            'overall_confidence', OLD.overall_confidence,
            'updated_at', OLD.updated_at
        ),
        JSON_OBJECT(
            'status', NEW.status,
            'overall_confidence', NEW.overall_confidence,
            'updated_at', NEW.updated_at
        )
    );
END //

DELIMITER ;

-- Performance optimization indexes
CREATE INDEX idx_research_quarter_status ON research_metadata(quarter, status, overall_confidence);
CREATE INDEX idx_validation_research_confidence ON validation_claims(research_metadata_id, confidence_score);
CREATE INDEX idx_insights_quarter_type ON data_insights(quarter, insight_type, confidence_level);

-- Sample data for testing (remove in production)
INSERT INTO research_metadata (chroma_id, quarter, theme_type, user_guidance, status) VALUES
('test-chroma-id-1', '2025Q1', 'eu_ets', 'Analyze EU ETS impact on container shipping', 'pending'),
('test-chroma-id-2', '2025Q1', 'routes', 'Study Red Sea diversions', 'pending'),
('test-chroma-id-3', '2025Q1', 'carrier', 'Maersk carbon compliance strategy', 'pending');

-- Show created objects
SHOW TABLES;
SHOW VIEWS;
SHOW PROCEDURE STATUS WHERE Db = 'etso_db';

-- Final check
SELECT 'Schema creation completed successfully' as status;