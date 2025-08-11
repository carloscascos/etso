-- OBSERVATORIO ETS - Create ETSO Database and User
-- Run this on your AWS RDS instance at sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com

-- =====================================================
-- STEP 1: Connect as admin user (ai)
-- =====================================================
-- mysql -h sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com -u ai -p

-- =====================================================
-- STEP 2: Create ETSO Database
-- =====================================================

-- Create the new database for OBSERVATORIO ETS
CREATE DATABASE IF NOT EXISTS etso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Show that it was created
SHOW DATABASES LIKE 'etso';

-- =====================================================
-- STEP 3: Create ETSO User with Full Access
-- =====================================================

-- Create the etso user (you can change this password)
CREATE USER IF NOT EXISTS 'etso'@'%' IDENTIFIED BY 'Etso_2025_Intelligence!';

-- Grant all privileges on etso database to etso user
GRANT ALL PRIVILEGES ON etso.* TO 'etso'@'%';

-- =====================================================
-- STEP 4: Also grant AI user full access to ETSO
-- =====================================================

-- Give your existing ai user full access to etso database
GRANT ALL PRIVILEGES ON etso.* TO 'ai'@'%';

-- Apply all privilege changes
FLUSH PRIVILEGES;

-- =====================================================
-- STEP 5: Verify Setup
-- =====================================================

-- Show grants for etso user
SELECT 'Grants for etso user:' as status;
SHOW GRANTS FOR 'etso'@'%';

-- Show grants for ai user on etso database
SELECT 'Grants for ai user on etso:' as status;
SHOW GRANTS FOR 'ai'@'%';

-- =====================================================
-- STEP 6: Test ETSO Database
-- =====================================================

-- Switch to etso database
USE etso;

-- Create a test table to verify permissions
CREATE TABLE IF NOT EXISTS test_setup (
    id INT AUTO_INCREMENT PRIMARY KEY,
    message VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test record
INSERT INTO test_setup (message) VALUES ('ETSO database created successfully!');

-- Verify
SELECT * FROM test_setup;

-- Clean up test table
DROP TABLE test_setup;

-- =====================================================
-- STEP 7: Success Message
-- =====================================================

SELECT 'ETSO database created successfully!' as status;
SELECT 'Database: etso' as info;
SELECT 'Users with access: etso, ai' as info;
SELECT 'Next step: Run schema.sql to create tables' as info;