"""
OBSERVATORIO ETS - Database Configuration
Dual database setup: traffic_db (readonly) + etso_db (full access)
"""

import os
import logging
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database connection configuration for dual-database architecture"""
    
    @property
    def TRAFFIC_DB(self) -> Dict[str, Any]:
        """Traffic database configuration (READ-ONLY access)"""
        return {
            'host': os.getenv('TRAFFIC_DB_HOST', 'localhost'),
            'port': int(os.getenv('TRAFFIC_DB_PORT', '3306')),
            'user': os.getenv('TRAFFIC_DB_USER', 'traffic_readonly'),
            'password': os.getenv('TRAFFIC_DB_PASSWORD', ''),
            'database': os.getenv('TRAFFIC_DB_NAME', 'traffic_db'),
            'charset': 'utf8mb4',
            'autocommit': True,
            'read_timeout': 300,  # 5 minutes for complex queries
            'write_timeout': 300,
            'connect_timeout': 30
        }
    
    @property
    def ETSO_DB(self) -> Dict[str, Any]:
        """ETSO database configuration (FULL access)"""
        return {
            'host': os.getenv('ETSO_DB_HOST', 'localhost'),
            'port': int(os.getenv('ETSO_DB_PORT', '3306')),
            'user': os.getenv('ETSO_DB_USER', 'etso'),
            'password': os.getenv('ETSO_DB_PASSWORD', ''),
            'database': os.getenv('ETSO_DB_NAME', 'etso_db'),
            'charset': 'utf8mb4',
            'autocommit': False,  # We want transaction control
            'read_timeout': 30,
            'write_timeout': 30
        }

@dataclass
class ChromaConfig:
    """ChromaDB configuration"""
    
    @property
    def CHROMA_CONFIG(self) -> Dict[str, Any]:
        return {
            'persist_directory': os.getenv('CHROMA_PERSIST_DIR', './chroma_data'),
            'collection_name': os.getenv('CHROMA_COLLECTION', 'observatorio_research'),
            'host': os.getenv('CHROMA_HOST', 'localhost'),
            'port': int(os.getenv('CHROMA_PORT', '8000')),
            'use_server': os.getenv('CHROMA_USE_SERVER', 'false').lower() == 'true'
        }

@dataclass
class LLMConfig:
    """Large Language Model configuration"""
    
    @property
    def OPENAI_CONFIG(self) -> Dict[str, Any]:
        return {
            'api_key': os.getenv('OPENAI_API_KEY', ''),
            'model': os.getenv('OPENAI_MODEL', 'gpt-4'),
            'temperature': float(os.getenv('OPENAI_TEMPERATURE', '0.1')),
            'max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '4000'))
        }

@dataclass 
class ResearchConfig:
    """Research configuration"""
    @property
    def CURRENT_QUARTER(self) -> str:
        return os.getenv('CURRENT_QUARTER', '2025Q1')
    
    @property
    def VALIDATION_THRESHOLD(self) -> float:
        return float(os.getenv('VALIDATION_THRESHOLD', '0.7'))

class SystemConfig:
    """System-wide configuration"""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self.chroma = ChromaConfig()
        self.llm = LLMConfig()
        self.research = ResearchConfig()
    
    @property
    def SYSTEM_SETTINGS(self) -> Dict[str, Any]:
        return {
            'current_quarter': os.getenv('CURRENT_QUARTER', '2025Q1'),
            'validation_threshold': float(os.getenv('VALIDATION_THRESHOLD', '0.7')),
            'max_research_topics': int(os.getenv('MAX_RESEARCH_TOPICS', '10')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        }
    
    def validate_config(self) -> bool:
        """Validate that all required configuration is present"""
        required_env_vars = [
            'TRAFFIC_DB_HOST',
            'TRAFFIC_DB_PASSWORD',
            'ETSO_DB_HOST', 
            'ETSO_DB_PASSWORD',
            'OPENAI_API_KEY'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {missing_vars}")
            return False
        
        logger.info("✅ Configuration validation passed")
        return True

# Global configuration instance
config = SystemConfig()