#!/usr/bin/env python3
"""
OBSERVATORIO ETS - Database Schema Setup
Initialize ETSO database schema and verify setup
"""

import os
import logging
import pymysql
from typing import Optional
from config import SystemConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaSetup:
    """Setup and initialize ETSO database schema"""
    
    def __init__(self, config: SystemConfig):
        self.config = config
        self.etso_config = config.database.ETSO_DB
        
    def create_database(self) -> bool:
        """Create ETSO database if it doesn't exist"""
        try:
            # Connect without specifying database to create it
            temp_config = self.etso_config.copy()
            temp_config.pop('database')
            
            conn = pymysql.connect(**temp_config)
            cursor = conn.cursor()
            
            # Create database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.etso_config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute(f"USE {self.etso_config['database']}")
            
            logger.info(f"✅ Database '{self.etso_config['database']}' created/verified")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False
    
    def execute_schema_file(self) -> bool:
        """Execute schema.sql file to create tables and procedures"""
        try:
            # Read schema file
            schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
            
            if not os.path.exists(schema_path):
                logger.error(f"❌ Schema file not found: {schema_path}")
                return False
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Connect to database
            conn = pymysql.connect(**self.etso_config)
            cursor = conn.cursor()
            
            # Execute schema (split by semicolon and execute each statement)
            statements = self._split_sql_statements(schema_sql)
            
            for i, statement in enumerate(statements):
                if statement.strip():
                    try:
                        cursor.execute(statement)
                        conn.commit()
                    except Exception as e:
                        if "already exists" not in str(e).lower():
                            logger.warning(f"Statement {i+1} warning: {e}")
            
            logger.info("✅ Schema executed successfully")
            
            # Verify tables were created
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            expected_tables = ['research_metadata', 'validation_claims', 'quarterly_reports', 'system_config', 'data_insights', 'audit_log']
            
            missing_tables = [t for t in expected_tables if t not in tables]
            if missing_tables:
                logger.error(f"❌ Missing tables: {missing_tables}")
                return False
            
            logger.info(f"✅ All tables created: {tables}")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to execute schema: {e}")
            return False
    
    def _split_sql_statements(self, sql_content: str) -> list:
        """Split SQL content into individual statements, handling DELIMITER changes"""
        statements = []
        current_statement = ""
        current_delimiter = ";"
        
        lines = sql_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('--'):
                continue
            
            # Handle DELIMITER changes
            if line.upper().startswith('DELIMITER'):
                current_delimiter = line.split()[1]
                continue
            
            current_statement += line + '\n'
            
            # Check if statement ends with current delimiter
            if line.endswith(current_delimiter):
                # Remove delimiter and add to statements
                statement = current_statement.rstrip('\n').rstrip(current_delimiter).strip()
                if statement:
                    statements.append(statement)
                current_statement = ""
        
        # Add final statement if exists
        if current_statement.strip():
            statements.append(current_statement.strip())
        
        return statements
    
    def verify_schema(self) -> bool:
        """Verify schema is correctly set up"""
        try:
            conn = pymysql.connect(**self.etso_config)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            logger.info(f"📋 Tables: {tables}")
            
            # Check views
            cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
            views = [row[0] for row in cursor.fetchall()]
            logger.info(f"👁️  Views: {views}")
            
            # Check procedures
            cursor.execute("SHOW PROCEDURE STATUS WHERE Db = %s", (self.etso_config['database'],))
            procedures = [row[1] for row in cursor.fetchall()]
            logger.info(f"⚙️  Procedures: {procedures}")
            
            # Test basic operations
            cursor.execute("SELECT COUNT(*) FROM system_config")
            config_count = cursor.fetchone()[0]
            logger.info(f"🔧 System config entries: {config_count}")
            
            cursor.execute("SELECT COUNT(*) FROM research_metadata")
            research_count = cursor.fetchone()[0]
            logger.info(f"🔍 Research metadata entries: {research_count}")
            
            conn.close()
            logger.info("✅ Schema verification completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema verification failed: {e}")
            return False
    
    def setup_user_permissions(self) -> bool:
        """Setup proper user permissions for ETSO database"""
        try:
            # Connect as root/admin to set permissions
            admin_config = self.etso_config.copy()
            admin_config['user'] = 'root'  # Assumes root access for setup
            
            conn = pymysql.connect(**admin_config)
            cursor = conn.cursor()
            
            # Create ETSO user if not exists
            cursor.execute(f"CREATE USER IF NOT EXISTS '{self.etso_config['user']}'@'%' IDENTIFIED BY '{self.etso_config['password']}'")
            
            # Grant permissions
            cursor.execute(f"GRANT ALL PRIVILEGES ON {self.etso_config['database']}.* TO '{self.etso_config['user']}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            
            logger.info(f"✅ User permissions set for '{self.etso_config['user']}'")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.warning(f"⚠️  Could not set user permissions (may require root access): {e}")
            return False
    
    def full_setup(self) -> bool:
        """Run complete database setup"""
        logger.info("🚀 Starting ETSO database setup...")
        
        steps = [
            ("Creating database", self.create_database),
            ("Executing schema", self.execute_schema_file),
            ("Verifying schema", self.verify_schema),
            ("Setting permissions", self.setup_user_permissions)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"🔄 {step_name}...")
            if not step_func():
                logger.error(f"❌ Failed at step: {step_name}")
                return False
        
        logger.info("🎉 ETSO database setup completed successfully!")
        return True

def main():
    """Main setup function"""
    from config import config
    
    if not config.validate_config():
        logger.error("❌ Configuration validation failed")
        return False
    
    setup = SchemaSetup(config)
    return setup.full_setup()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)