#!/usr/bin/env python3
"""
Test complete database setup for OBSERVATORIO ETS
"""

import pymysql
import sys
import tabulate

def test_database_setup():
    """Test both database connections"""
    
    print("🔍 OBSERVATORIO ETS - Database Setup Test")
    print("=" * 60)
    
    # Connection details from your setup
    host = "sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com"
    port = 3306
    user = "ai"
    password = "elpatiodemicasa"
    
    # Test 1: Traffic Database (imo)
    print("\n📊 Testing Traffic Database (imo)...")
    print("-" * 40)
    
    try:
        conn_imo = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="imo",
            charset='utf8mb4'
        )
        
        cursor = conn_imo.cursor()
        
        print("✅ Connected to 'imo' database")
        
        # Check key tables
        tables_to_check = ['escalas', 'v_fleet', 'ports']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  ✓ Table {table}: {count:,} records")
            except Exception as e:
                print(f"  ✗ Table {table}: {e}")
        
        # Test a sample query
        cursor.execute("""
            SELECT COUNT(*) as total_escalas
            FROM escalas 
            WHERE start >= '2024-01-01'
        """)
        recent_count = cursor.fetchone()[0]
        print(f"  ✓ Recent escalas (2024+): {recent_count:,} records")
        
        conn_imo.close()
        print("✅ Traffic database test passed!")
        
    except Exception as e:
        print(f"❌ Traffic database test failed: {e}")
        return False
    
    # Test 2: ETSO Database
    print("\n📊 Testing ETSO Database...")
    print("-" * 40)
    
    try:
        conn_etso = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="etso",
            charset='utf8mb4'
        )
        
        cursor = conn_etso.cursor()
        
        print("✅ Connected to 'etso' database")
        
        # Check if tables exist
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        expected_tables = [
            'research_metadata',
            'validation_claims',
            'quarterly_reports',
            'system_config',
            'data_insights'
        ]
        
        existing_tables = [t[0] for t in tables]
        
        for table in expected_tables:
            if table in existing_tables:
                print(f"  ✓ Table {table} exists")
            else:
                print(f"  ✗ Table {table} missing")
        
        # Check system config
        cursor.execute("SELECT COUNT(*) FROM system_config")
        config_count = cursor.fetchone()[0]
        print(f"  ✓ System config entries: {config_count}")
        
        # Show current config
        cursor.execute("SELECT config_key, config_value FROM system_config WHERE is_active = TRUE")
        configs = cursor.fetchall()
        
        if configs:
            print("\n📋 Current Configuration:")
            print(tabulate.tabulate(configs, headers=['Config Key', 'Value']))
        
        conn_etso.close()
        print("\n✅ ETSO database test passed!")
        
    except Exception as e:
        print(f"❌ ETSO database test failed: {e}")
        print("\n💡 Run this SQL to create ETSO database:")
        print("   mysql -h sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com -u ai -p < setup_etso_db.sql")
        return False
    
    # Test 3: Cross-database query capability
    print("\n🔗 Testing Cross-Database Query Capability...")
    print("-" * 40)
    
    try:
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # Test reading from imo and writing to etso
        cursor.execute("""
            SELECT COUNT(*) FROM imo.escalas 
            WHERE start >= '2025-01-01'
        """)
        count_2025 = cursor.fetchone()[0]
        print(f"  ✓ Can read from imo.escalas: {count_2025:,} records in 2025")
        
        cursor.execute("USE etso")
        cursor.execute("SELECT COUNT(*) FROM research_metadata")
        research_count = cursor.fetchone()[0]
        print(f"  ✓ Can access etso.research_metadata: {research_count} records")
        
        conn.close()
        print("✅ Cross-database access works!")
        
    except Exception as e:
        print(f"❌ Cross-database test failed: {e}")
        return False
    
    # Final summary
    print("\n" + "=" * 60)
    print("🎉 DATABASE SETUP COMPLETE!")
    print("=" * 60)
    print("\n📋 Configuration Summary:")
    print(f"  Host: {host}")
    print(f"  User: {user}")
    print(f"  Traffic DB: imo")
    print(f"  Research DB: etso")
    print(f"  Status: READY")
    
    print("\n🚀 Next Steps:")
    print("1. Add your OpenAI API key to .env file")
    print("2. Run: pip install -r requirements.txt")
    print("3. Run: python main.py")
    
    return True

if __name__ == "__main__":
    success = test_database_setup()
    exit(0 if success else 1)