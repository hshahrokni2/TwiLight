"""
Universal configuration loader for agents
Supports both Railway (environment variables) and local (config.json)
PRIORITY: Environment variables first, then config.json
"""
import os
import json
import sys

def load_agent_config(config_path='config.json'):
    """
    Load configuration for agents, with Railway environment variable support
    
    Priority:
    1. Environment variables (Railway/Docker)
    2. config.json file (local development)
    """
    
    # Check if we're in a cloud environment (Railway, Docker, etc.)
    # Railway always sets DATABASE_URL for PostgreSQL
    is_cloud_env = os.getenv('DATABASE_URL') is not None
    
    if is_cloud_env:
        print("🌐 Cloud environment detected - loading config from environment variables")
        
        try:
            # Add parent directory to path to import config_loader
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from config_loader import load_config, get_database_config
            
            config = load_config()
            config['database'] = get_database_config()
            
            print("✅ Configuration loaded from environment variables")
            return config
            
        except Exception as e:
            print(f"❌ CRITICAL ERROR: Could not load config from environment: {e}")
            print("⚠️  Railway deployment requires these environment variables:")
            print("   - DATABASE_URL (automatically set by Railway)")
            print("   - KRAKEN_API_KEY or BINANCE_API_KEY")
            print("   - KRAKEN_API_SECRET or BINANCE_API_SECRET")
            print("   - OPENAI_API_KEY")
            print("   - TELEGRAM_BOT_TOKEN (optional)")
            print("   - TELEGRAM_USER_ID (optional)")
            raise SystemExit(f"Configuration error: {e}")
    
    # Local development - try to find config.json
    print("🏠 Local environment detected - looking for config.json")
    
    possible_paths = [
        config_path,
        'config.json',
        os.path.join(os.path.dirname(__file__), 'config.json'),
        os.path.join(os.path.dirname(__file__), '..', 'config.json'),
        '/opt/crypto-trading/config.json'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Found config.json at: {path}")
            with open(path, 'r') as f:
                return json.load(f)
    
    print(f"❌ Could not find config.json in any of: {possible_paths}")
    print("⚠️  For local development, create config.json from config.json.template")
    raise FileNotFoundError(f"Could not find config.json in any of: {possible_paths}")
