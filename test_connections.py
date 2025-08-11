#!/usr/bin/env python3
"""
Test both database connections for OBSERVATORIO ETS
"""

import pymysql
import sys

def test_imo_connection():
    """Test connection to IMO (traffic) database"""
    print("🔍 Testing IMO Database Connection")
    print("=" * 50)
    
    config = {
        'host': 'sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com',
        'port': 3306,
        'user': 'ai',
        'password': 'elpatiodemicasa',
        'database': 'imo',
        'charset': 'utf8mb4'
    }
    
    try:
        print(f"Connecting to {config['host']}/{config['database']}...")
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        # Test key tables
        tables = ['escalas', 'vessels', 'ports']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Table {table}: {count:,} records")
        
        conn.close()
        print("✅ IMO database connection successful!\n")
        return True
        
    except Exception as e:
        print(f"❌ IMO database connection failed: {e}\n")
        return False

def test_etso_connection():
    """Test connection to ETSO database"""
    print("🔍 Testing ETSO Database Connection")
    print("=" * 50)
    
    config = {
        'host': 'sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com',
        'port': 3306,
        'user': 'ai',
        'password': 'elpatiodemicasa',
        'database': 'etso',
        'charset': 'utf8mb4'
    }
    
    try:
        print(f"Connecting to {config['host']}/{config['database']}...")
        conn = pymysql.connect(**config)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT DATABASE()")
        db_name = cursor.fetchone()[0]
        print(f"✅ Connected to database: {db_name}")
        
        # Check for tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"   - {table[0]}")
        else:
            print("⚠️  No tables found (need to run schema.sql)")
        
        conn.close()
        print("✅ ETSO database connection successful!\n")
        return True
        
    except Exception as e:
        if "Unknown database" in str(e):
            print(f"❌ ETSO database does not exist yet!")
            print("   Run: mysql -h sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com -u ai -p < setup_etso_database.sql")
        else:
            print(f"❌ ETSO database connection failed: {e}")
        print()
        return False

def main():
    """Test both database connections"""
    print("🚀 OBSERVATORIO ETS - Database Connection Test")
    print("=" * 50)
    print()
    
    imo_ok = test_imo_connection()
    etso_ok = test_etso_connection()
    
    print("=" * 50)
    print("📊 Summary:")
    print(f"   IMO Database:  {'✅ OK' if imo_ok else '❌ Failed'}")
    print(f"   ETSO Database: {'✅ OK' if etso_ok else '❌ Failed'}")
    
    if not etso_ok:
        print("\n📝 Next Steps:")
        print("1. Create ETSO database:")
        print("   mysql -h sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com -u ai -p < setup_etso_database.sql")
        print("\n2. Create ETSO tables:")
        print("   mysql -h sbc-database.caa4nswcizpd.eu-west-1.rds.amazonaws.com -u ai -p etso < schema.sql")
    
    return imo_ok and etso_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)