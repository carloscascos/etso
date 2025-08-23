#!/usr/bin/env python3
"""Update database schema for validation_weight and sources"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from config import SystemConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = SystemConfig()
db_manager = DatabaseManager(config)

def update_schema():
    """Add validation_weight to validation_claims and sources to research_metadata"""
    with db_manager.get_etso_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Add validation_weight column to validation_claims
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'validation_claims' 
                AND COLUMN_NAME = 'validation_weight'
            """)
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE validation_claims 
                    ADD COLUMN validation_weight DECIMAL(5,2) DEFAULT 50.00
                    COMMENT 'Validation weight percentage 0-100'
                    AFTER validation_logic
                """)
                logger.info("✅ Added validation_weight column to validation_claims")
            else:
                logger.info("ℹ️ validation_weight column already exists")
            
            # Add sources column to research_metadata
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'research_metadata' 
                AND COLUMN_NAME = 'sources'
            """)
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE research_metadata 
                    ADD COLUMN sources JSON DEFAULT NULL
                    COMMENT 'JSON array of source URLs and titles'
                    AFTER research_content_preview
                """)
                logger.info("✅ Added sources column to research_metadata")
            else:
                logger.info("ℹ️ sources column already exists")
                
            conn.commit()
            logger.info("✅ Schema update complete")
                
        except Exception as e:
            logger.error(f"Error updating schema: {e}")
            raise

if __name__ == "__main__":
    logger.info("🔧 Updating database schema for claims refactor")
    update_schema()