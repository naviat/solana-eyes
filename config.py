import os
import yaml
from loguru import logger

HEADERS = {'Content-Type': 'application/json'}

def get_config_value(env_key, yaml_key, default_value, config_dict=None, value_type=str):
    """
    Get configuration value with priority:
    1. Environment variable
    2. YAML config file
    3. Default value
    """
    # Try environment variable first
    env_value = os.getenv(env_key)
    if env_value is not None:
        try:
            return value_type(env_value)
        except ValueError as e:
            logger.warning(f"Invalid {env_key} value: {env_value}, using default")
            return value_type(default_value)

    # Try YAML config
    if config_dict and yaml_key in config_dict:
        try:
            return value_type(config_dict[yaml_key])
        except ValueError as e:
            logger.warning(f"Invalid {yaml_key} value in config.yml, using default")
            return value_type(default_value)

    # Use default
    return value_type(default_value)

# Try to load config.yml if it exists
config = {}
try:
    with open("config.yml", "r") as config_file:
        config = yaml.safe_load(config_file) or {}
    logger.info("Loaded configuration from config.yml")
except FileNotFoundError:
    logger.info("No config.yml found, will use environment variables or defaults")
except Exception as e:
    logger.warning(f"Error reading config.yml: {e}, will use environment variables or defaults")

# Configuration values with priority order
NETWORK_RPC_ENDPOINT = get_config_value(
    "NETWORK_RPC_ENDPOINT", 
    "network_rpc_endpoint",
    "https://api.mainnet-beta.solana.com",
    config
)

SOLANA_RPC_ENDPOINT = get_config_value(
    "SOLANA_RPC_ENDPOINT", 
    "solana_rpc_endpoint",
    "http://localhost:8799",
    config
)

SOLANA_WS_ENDPOINT = get_config_value(
    "SOLANA_WS_ENDPOINT", 
    "solana_ws_endpoint",
    "ws://localhost:8800",
    config
)

# Numeric configurations
THREAD_POOL_SIZE = get_config_value(
    "THREAD_POOL_SIZE", 
    "thread_pool_size",
    4,
    config,
    int
)

SLEEP_TIME = get_config_value(
    "SLEEP_TIME", 
    "sleep_time",
    15,
    config,
    int
)

PORT = get_config_value(
    "METRIC_PORT", 
    "metric_port",
    6660,
    config,
    int
)

RETRY = get_config_value(
    "RETRY", 
    "retry",
    10,
    config,
    int
)

LOG_LEVEL = get_config_value(
    "LOG_LEVEL", 
    "log_level",
    "INFO",
    config
)

# Log the final configuration
logger.info("Configuration values:")
logger.info(f"NETWORK_RPC_ENDPOINT: {NETWORK_RPC_ENDPOINT}")
logger.info(f"SOLANA_RPC_ENDPOINT: {SOLANA_RPC_ENDPOINT}")
logger.info(f"SOLANA_WS_ENDPOINT: {SOLANA_WS_ENDPOINT}")
logger.info(f"THREAD_POOL_SIZE: {THREAD_POOL_SIZE}")
logger.info(f"SLEEP_TIME: {SLEEP_TIME}")
logger.info(f"PORT: {PORT}")
logger.info(f"LOG_LEVEL: {LOG_LEVEL}")
logger.info(f"RETRY: {RETRY}")
