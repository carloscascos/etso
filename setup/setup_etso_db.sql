-- OBSERVATORIO ETS - ETSO Database Setup
-- Run this on your RDS instance to create the new ETSO database

-- =====================================================
-- STEP 1: Create ETSO database
-- =====================================================

-- Create the new database for research findings
CREATE DATABASE IF NOT EXISTS etso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Show that it was created
SHOW DATABASES LIKE 'etso';

-- =====================================================
-- STEP 2: Create/Update user 'ai' with access to both databases
-- =====================================================

-- Since user 'ai' already exists, we'll grant permissions
-- Grant full access to ETSO database
GRANT ALL PRIVILEGES ON etso.* TO 'ai'@'%';

-- Ensure read access to imo database (traffic data)
GRANT SELECT ON imo.* TO 'ai'@'%';

-- Specifically grant SELECT on the tables we need
GRANT SELECT ON imo.escalas TO 'ai'@'%';
GRANT SELECT ON imo.vessels TO 'ai'@'%';
GRANT SELECT ON imo.ports TO 'ai'@'%';

-- Apply the changes
FLUSH PRIVILEGES;

-- =====================================================
-- STEP 3: Verify permissions
-- =====================================================

-- Show grants for user 'ai'
SHOW GRANTS FOR 'ai'@'%';

-- =====================================================
-- STEP 4: Switch to ETSO database and create schema
-- =====================================================

USE etso;

-- Now run the full schema creation
-- (This is the same as schema.sql but included here for convenience)

-- Research findings metadata table
CREATE TABLE IF NOT EXISTS research_metadata (
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
    INDEX idx_created_at (created_at)
);

-- Validation results for individual claims
CREATE TABLE IF NOT EXISTS validation_claims (
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
    INDEX idx_confidence (confidence_score)
);

-- Quarterly report generation metadata
CREATE TABLE IF NOT EXISTS quarterly_reports (
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
CREATE TABLE IF NOT EXISTS system_config (
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
CREATE TABLE IF NOT EXISTS data_insights (
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
    affected_vessels TEXT,
    affected_routes TEXT,
    quantitative_data JSON,
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
('report_generation_enabled', 'true', 'boolean', 'Enable automatic report generation')
ON DUPLICATE KEY UPDATE updated_at = NOW();

-- =====================================================
-- STEP 5: Verify setup
-- =====================================================

-- Check tables were created
SHOW TABLES;

-- Verify system config
SELECT * FROM system_config;

-- Success message
SELECT 'ETSO database setup completed successfully!' as status,
       'Database: etso' as database_name,
       'User: ai' as user_name,
       'Host: sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com' as host;