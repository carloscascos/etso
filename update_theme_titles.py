#!/usr/bin/env python3
"""Add theme_title column and populate with brief titles"""

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

def add_theme_title_column():
    """Add theme_title column to research_metadata table"""
    with db_manager.get_etso_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # Check if column already exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE()
                AND TABLE_NAME = 'research_metadata' 
                AND COLUMN_NAME = 'theme_title'
            """)
            
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    ALTER TABLE research_metadata 
                    ADD COLUMN theme_title VARCHAR(100) DEFAULT NULL
                    AFTER user_guidance
                """)
                conn.commit()
                logger.info("✅ Added theme_title column to research_metadata table")
            else:
                logger.info("ℹ️ theme_title column already exists")
                
        except Exception as e:
            logger.error(f"Error adding column: {e}")
            raise

def generate_theme_titles():
    """Generate brief titles based on user_guidance content"""
    
    theme_titles = {
        # EU ETS themes
        41: "Long Beach Port Volume Analysis Q2 2025",
        38: "Eastern Med Transshipment Hub Analysis",
        37: "Eastern Med Hub Carbon Compliance Study",
        36: "Transpacific Trade & Long Beach Volumes",
        34: "Asia-America Long Beach Container Traffic",
        33: "Eastern Mediterranean Hub Development",
        32: "Maersk GEMINI Carbon Strategy",
        30: "Piraeus Port Traffic Analysis",
        29: "Eastern Med Hub Vessel Patterns",
        28: "Mediterranean Carbon Compliance Study",
        27: "Eastern Med Transshipment Development",
        26: "Maersk GEMINI Alliance Strategy",
        23: "Maersk GEMINI Carbon Compliance",
        21: "Eastern Mediterranean Hub Growth",
        20: "Maersk GEMINI Carbon Planning",
        17: "Maersk Alliance Carbon Strategy",
        14: "Maersk GEMINI Compliance Analysis",
        11: "Maersk Carbon Strategy Overview",
        8: "Maersk GEMINI Carbon Roadmap",
        5: "Maersk Alliance Carbon Initiative",
        
        # Regional themes  
        24: "Eastern Med Hub Infrastructure",
        18: "Mediterranean Port Development",
        15: "Eastern Med Hub Expansion",
        12: "Mediterranean Transshipment Growth",
        9: "Eastern Med Port Network",
        6: "Mediterranean Hub Strategy",
        
        # Routes themes
        42: "Transpacific Container Volume Trends Q2 2025",
        40: "Asia-America Trade Route Analysis",
        39: "Long Beach-Asia Trade Patterns",
        35: "Red Sea Crisis Route Impact",
        31: "Red Sea-Europe Route Disruption",
        25: "Red Sea Container Route Changes",
        22: "Red Sea Crisis Shipping Impact",
        19: "Red Sea Route Alternatives",
        16: "Asia-Europe Route Adjustments",
        13: "Red Sea Trade Flow Changes",
        10: "Asia-Europe Route Impacts",
        7: "Red Sea Crisis Container Analysis",
        4: "Asia-Europe Route Disruptions"
    }
    
    with db_manager.get_etso_connection() as conn:
        cursor = conn.cursor()
        
        try:
            for theme_id, title in theme_titles.items():
                cursor.execute("""
                    UPDATE research_metadata 
                    SET theme_title = %s 
                    WHERE id = %s
                """, (title, theme_id))
            
            conn.commit()    
            logger.info(f"✅ Updated {len(theme_titles)} theme titles")
            
            # Log themes without titles for verification
            cursor.execute("""
                SELECT id, LEFT(user_guidance, 50) 
                FROM research_metadata 
                WHERE theme_title IS NULL
            """)
            
            missing = cursor.fetchall()
            if missing:
                logger.warning(f"⚠️ {len(missing)} themes still without titles")
                for theme_id, guidance in missing:
                    logger.info(f"  - ID {theme_id}: {guidance}...")
                    
        except Exception as e:
            logger.error(f"Error updating titles: {e}")
            raise

def main():
    logger.info("🔧 Updating theme titles in ETSO database")
    
    # Add column if it doesn't exist
    add_theme_title_column()
    
    # Generate and update titles
    generate_theme_titles()
    
    logger.info("✅ Theme titles update complete")

if __name__ == "__main__":
    main()