#!/usr/bin/env python3
"""
Test connection to traffic database
"""

import pymysql
import sys
from tabulate import tabulate

def test_traffic_connection():
    """Test connection to traffic database"""
    
    print("🔄 Testing Traffic Database Connection")
    print("=" * 50)
    
    # Get connection details from user
    print("Please provide your traffic database connection details:")
    
    host = input("Database Host: ").strip()
    port = int(input("Database Port (3306): ").strip() or "3306")
    database = input("Database Name (traffic_db): ").strip() or "traffic_db"
    
    # Use the read-only user we just created
    user = "traffic_readonly"
    password = input("Password for traffic_readonly: ").strip()
    
    try:
        # Test connection
        print(f"\n🔄 Connecting to {host}:{port}/{database} as {user}...")
        
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        print("✅ Connection successful!")
        
        # Test key tables
        tables_to_check = ['escalas', 'vessels', 'ports']
        
        for table in tables_to_check:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Table {table}: {count:,} records")
                
                # Show sample structure
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"📋 {table} structure:")
                print(tabulate(columns, headers=['Column', 'Type', 'Null', 'Key', 'Default', 'Extra']))
                print()
                
            except Exception as e:
                print(f"❌ Error checking table {table}: {e}")
        
        # Test a sample query that our system will use
        print("🔍 Testing sample validation query...")
        
        sample_query = """
        SELECT e.imo, v.vessel_name, e.portname, e.start_time
        FROM escalas e
        JOIN vessels v ON e.imo = v.imo
        WHERE e.start_time >= '2024-01-01'
        LIMIT 5
        """
        
        cursor.execute(sample_query)
        results = cursor.fetchall()
        
        if results:
            print("✅ Sample query successful:")
            headers = ['IMO', 'Vessel Name', 'Port', 'Start Time']
            print(tabulate(results, headers=headers))
        else:
            print("⚠️  No recent data found (may be normal)")
        
        conn.close()
        
        # Save connection details for .env file
        print(f"\n📝 Add these to your .env file:")
        print(f"TRAFFIC_DB_HOST={host}")
        print(f"TRAFFIC_DB_PORT={port}")
        print(f"TRAFFIC_DB_USER=traffic_readonly")
        print(f"TRAFFIC_DB_PASSWORD={password}")
        print(f"TRAFFIC_DB_NAME={database}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure you ran setup_traffic_db.sql on your traffic database")
        print("2. Check that the database server is accessible")
        print("3. Verify the password for traffic_readonly user")
        return False

if __name__ == "__main__":
    try:
        import tabulate
    except ImportError:
        print("Installing required package...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "tabulate"], check=True)
        import tabulate
    
    success = test_traffic_connection()
    exit(0 if success else 1)