"""
Universal configuration loader for agents
Supports both Railway (environment variables) and local (config.json)
"""
import os
import json

def load_agent_config(config_path='config.json'):
    """
    Load configuration for agents, with Railway environment variable support
    """
    # Check if we're on Railway (DATABASE_URL is set)
    if os.getenv('DATABASE_URL'):
        # Use config_loader for environment variables
        try:
            import sys
            # Add parent directory to path to import config_loader
            parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            from config_loader import load_config, get_database_config
            config = load_config()
            config['database'] = get_database_config()
            return config
        except Exception as e:
            print(f"Warning: Could not load config from environment: {e}")
            # Fall through to file-based config
    
    # Try to find config.json in multiple locations
    possible_paths = [
        config_path,
        'config.json',
        os.path.join(os.path.dirname(__file__), 'config.json'),
        os.path.join(os.path.dirname(__file__), '..', 'config.json'),
        '/opt/crypto-trading/config.json'
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    
    raise FileNotFoundError(f"Could not find config.json in any of: {possible_paths}")
