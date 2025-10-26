"""
Helper to get the config.json path flexibly
"""
import os

def get_config_path():
    """Get the path to config.json, checking multiple locations"""
    possible_paths = [
        'config.json',  # Current directory
        os.path.join(os.path.dirname(__file__), 'config.json'),  # Script directory
        '/opt/crypto-trading/config.json',  # Legacy path
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # If no config.json found, return current directory (will use env vars)
    return 'config.json'
