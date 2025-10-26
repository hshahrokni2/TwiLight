
import os
import json
from typing import Dict, Any, Optional
import urllib.parse as urlparse

def parse_redis_url(redis_url: str) -> Dict[str, Any]:
    """
    Parse Redis URL into connection parameters dict.
    Handles both Railway Redis URL format and local Redis.
    
    Examples:
    - redis://localhost:6379 -> {'host': 'localhost', 'port': 6379}
    - redis://:password@host:port/db -> {'host': 'host', 'port': port, 'password': 'password', 'db': db}
    """
    try:
        if not redis_url or redis_url == '':
            # Fallback to local Redis
            return {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'decode_responses': True
            }
        
        # Parse the URL
        parsed = urlparse.urlparse(redis_url)
        
        redis_config = {
            'host': parsed.hostname or 'localhost',
            'port': parsed.port or 6379,
            'decode_responses': True
        }
        
        # Add password if present
        if parsed.password:
            redis_config['password'] = parsed.password
        
        # Add database number if present in path
        if parsed.path and len(parsed.path) > 1:
            try:
                redis_config['db'] = int(parsed.path[1:])
            except ValueError:
                redis_config['db'] = 0
        else:
            redis_config['db'] = 0
        
        return redis_config
    except Exception as e:
        print(f"⚠️  Error parsing Redis URL: {e}")
        # Fallback to local Redis
        return {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'decode_responses': True
        }

def safe_int_conversion(value: str, default: int) -> int:
    """
    Safely convert a string to integer with fallback to default.
    Handles invalid/placeholder values gracefully.
    """
    try:
        # Strip whitespace and check if it's a valid integer
        if value and value.strip() and value.strip().lstrip('-').isdigit():
            return int(value.strip())
        else:
            return default
    except (ValueError, AttributeError):
        return default

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables with fallback to config.json
    Railway and other cloud platforms use environment variables for secrets
    """
    
    # Check if we're using environment variables (Railway, Docker, etc.)
    use_env = os.getenv('USE_ENV_CONFIG', 'true').lower() == 'true'
    
    if use_env and os.getenv('DATABASE_URL'):
        # Parse DATABASE_URL for Railway PostgreSQL
        db_url = os.getenv('DATABASE_URL', '')
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        
        config = {
            "initial_capital": float(os.getenv('INITIAL_CAPITAL', '100')),
            "exchanges": {
                "binance": {
                    "enabled": True,
                    "api_key": os.getenv('BINANCE_API_KEY', ''),
                    "api_secret": os.getenv('BINANCE_API_SECRET', '')
                },
                "kraken": {
                    "enabled": True,
                    "api_key": os.getenv('KRAKEN_API_KEY', ''),
                    "api_secret": os.getenv('KRAKEN_API_SECRET', '')
                }
            },
            "llm_providers": {
                "openai": {
                    "api_key": os.getenv('OPENAI_API_KEY', ''),
                    "model": "gpt-4"
                },
                "anthropic": {
                    "api_key": os.getenv('ANTHROPIC_API_KEY', ''),
                    "model": "claude-3-5-sonnet-20241022"
                },
                "grok": {
                    "api_key": os.getenv('GROK_API_KEY', ''),
                    "model": "grok-beta"
                },
                "perplexity": {
                    "api_key": os.getenv('PERPLEXITY_API_KEY', ''),
                    "model": "llama-3.1-sonar-large-128k-online"
                }
            },
            "database_url": db_url,
            "redis_url": redis_url,
            "redis": parse_redis_url(redis_url),  # Parse Redis URL into connection dict
            "risk_management": {
                "max_position_size": float(os.getenv('MAX_POSITION_SIZE', '0.1')),
                "max_daily_loss": float(os.getenv('MAX_DAILY_LOSS', '0.05')),
                "stop_loss_percentage": float(os.getenv('STOP_LOSS_PERCENTAGE', '0.02')),
                "take_profit_percentage": float(os.getenv('TAKE_PROFIT_PERCENTAGE', '0.05'))
            },
            "trading_pairs": [
                "BTC/USDT",
                "ETH/USDT",
                "SOL/USDT",
                "BNB/USDT"
            ],
            "telegram": {
                "bot_token": os.getenv('TELEGRAM_BOT_TOKEN', ''),
                "user_id": safe_int_conversion(os.getenv('TELEGRAM_USER_ID', '7171577450'), 7171577450),
                "group_chat_id": safe_int_conversion(os.getenv('TELEGRAM_GROUP_CHAT_ID', '-4800163944'), -4800163944)
            },
            # Legacy keys for backward compatibility
            "binance_api_key": os.getenv('BINANCE_API_KEY', ''),
            "binance_api_secret": os.getenv('BINANCE_API_SECRET', ''),
            "kraken_api_key": os.getenv('KRAKEN_API_KEY', ''),
            "kraken_api_secret": os.getenv('KRAKEN_API_SECRET', ''),
            "openai_api_key": os.getenv('OPENAI_API_KEY', ''),
            "anthropic_api_key": os.getenv('ANTHROPIC_API_KEY', ''),
            "grok_api_key": os.getenv('GROK_API_KEY', ''),
            "perplexity_api_key": os.getenv('PERPLEXITY_API_KEY', '')
        }
    else:
        # Fallback to config.json for local development
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
        except FileNotFoundError:
            raise Exception("config.json not found and environment variables not set")
    
    return config

def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration from environment or config.json
    """
    config = load_config()
    
    if 'database_url' in config:
        # Parse Railway DATABASE_URL
        import urllib.parse as urlparse
        url = urlparse.urlparse(config['database_url'])
        return {
            'host': url.hostname,
            'port': url.port or 5432,
            'database': url.path[1:],
            'user': url.username,
            'password': url.password
        }
    else:
        # Use config.json database section
        return config.get('database', {
            'host': 'localhost',
            'port': 5432,
            'database': 'crypto_trading',
            'user': 'trader',
            'password': 'trader_password_2024'
        })
