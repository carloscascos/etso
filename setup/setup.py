#!/usr/bin/env python3
"""
OBSERVATORIO ETS - Setup and Installation Script
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 10):
        logger.error("❌ Python 3.10 or higher required")
        return False
    
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    return True

def install_dependencies():
    """Install Python dependencies"""
    logger.info("📦 Installing Python dependencies...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        
        logger.info("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        logger.error(f"Output: {e.stdout}")
        logger.error(f"Error: {e.stderr}")
        return False

def setup_environment():
    """Setup environment configuration"""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        logger.info("⚠️  .env file already exists")
        response = input("Do you want to recreate it? (y/N): ")
        if response.lower() != 'y':
            return True
    
    if env_example.exists():
        # Copy example to .env
        with open(env_example, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        
        logger.info("✅ Created .env file from template")
        logger.info("🔧 Please edit .env file with your actual configuration")
        return True
    else:
        logger.error("❌ .env.example file not found")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'chroma_data',
        'logs',
        'reports',
        'temp'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        logger.info(f"📁 Created directory: {directory}")
    
    return True

def setup_database():
    """Setup ETSO database schema"""
    logger.info("🗄️  Setting up ETSO database...")
    
    try:
        from schema_setup import main as setup_main
        success = setup_main()
        
        if success:
            logger.info("✅ Database setup completed")
        else:
            logger.error("❌ Database setup failed")
            logger.info("💡 You may need to run database setup manually later")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Database setup error: {e}")
        logger.info("💡 You can run 'python schema_setup.py' manually later")
        return False

def test_configuration():
    """Test system configuration"""
    logger.info("🧪 Testing configuration...")
    
    try:
        from config import config
        
        # Test config validation
        if not config.validate_config():
            logger.error("❌ Configuration validation failed")
            return False
        
        # Test database connections
        from database import create_database_manager
        db_manager = create_database_manager(config)
        
        if not db_manager.test_connections():
            logger.error("❌ Database connection test failed")
            return False
        
        logger.info("✅ Configuration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main setup function"""
    logger.info("🚀 OBSERVATORIO ETS Setup")
    logger.info("=" * 40)
    
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Setting up environment", setup_environment),
        ("Creating directories", create_directories),
        ("Setting up database", setup_database),
        ("Testing configuration", test_configuration)
    ]
    
    for step_name, step_func in steps:
        logger.info(f"🔄 {step_name}...")
        
        if not step_func():
            logger.error(f"❌ Setup failed at: {step_name}")
            return False
    
    logger.info("🎉 OBSERVATORIO ETS setup completed successfully!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Edit .env file with your database credentials")
    logger.info("2. Run 'python schema_setup.py' if database setup failed")
    logger.info("3. Test the system with 'python main.py'")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)