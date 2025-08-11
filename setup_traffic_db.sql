
-- Check that tables exist and are accessible
SELECT 'Checking escalas table...' as status;
SELECT COUNT(*) as escalas_count FROM escalas LIMIT 1;

SELECT 'Checking vessels table...' as status;
SELECT COUNT(*) as vessels_count FROM v_fleet LIMIT 1;

SELECT 'Checking ports table...' as status;
SELECT COUNT(*) as ports_count FROM ports LIMIT 1;

-- Show sample data structure (first few records)
SELECT 'Sample escalas structure:' as status;
SELECT * FROM escalas LIMIT 3;

SELECT 'Sample vessels structure:' as status;
SELECT * FROM v_fleet LIMIT 3;

SELECT 'Sample ports structure:' as status;
SELECT * FROM ports LIMIT 3;

-- =====================================================
-- STEP 3: Verify user permissions
-- =====================================================

-- Show grants for the new user
SHOW GRANTS FOR 'ai'@'%';

-- Success message
SELECT 'Traffic database setup completed successfully!' as status;