import yaml

HEADERS = {'Content-Type': 'application/json'}

with open("config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)

NETWORK_RPC_ENDPOINT = config.get("network_rpc_endpoint", "https://api.testnet.solana.com")
SOLANA_RPC_ENDPOINT = config.get("solana_rpc_endpoint", "http://localhost:8899")
SOLANA_WS_ENDPOINT = config.get("solana_ws_endpoint", "ws://localhost:8900")

THREAD_POOL_SIZE = config.get("thread_pool_size", 4)
SLEEP_TIME = config.get("sleep_time", 45)
PORT = config.get("metric_port", 9090)
LOG_LEVEL = config.get("log_level", "INFO")
RETRY = config.get("retry", 5)
