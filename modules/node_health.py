import aiohttp
from loguru import logger
from config import SOLANA_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from prometheus.metrics import (
    solana_node_health, solana_node_slots_behind,
    solana_rpc_websocket_connections, solana_rpc_account_cache_size,
    solana_rpc_program_cache_size
)

async def get_health():
    """Check the health status of the RPC node and related metrics"""
    try:
        async with aiohttp.ClientSession() as session:
            # Health check
            health_payload = {
                "jsonrpc": "2.0", "id": 1, "method": "getHealth"
            }
            async with session.post(SOLANA_RPC_ENDPOINT, json=health_payload, headers=HEADERS) as response:
                result = await response.json()

            if "result" in result and result["result"] == "ok":
                update_metric(solana_node_health, 1, labels={"status": "healthy", "cause": "none"})
                logger.info("RPC node is healthy")
            elif "error" in result:
                error_message = result["error"].get("message", "Unknown error")
                slots_behind = result["error"]["data"].get("numSlotsBehind", 0)
                update_metric(solana_node_health, 0, labels={"status": "unhealthy", "cause": "slots_behind"})
                update_metric(solana_node_slots_behind, slots_behind)
                logger.error(f"RPC node is unhealthy: {error_message}.")
            else:
                logger.error("Unexpected response format")
                update_metric(solana_node_health, 0, labels={"status": "unhealthy", "cause": "unknown"})

            # Get cache metrics
            cache_payload = {
                "jsonrpc": "2.0", "id": 1, "method": "getCacheInfo"
            }
            try:
                async with session.post(SOLANA_RPC_ENDPOINT, json=cache_payload, headers=HEADERS) as response:
                    cache_result = await response.json()
                    if "result" in cache_result:
                        account_cache = cache_result["result"].get("accountCacheSize", 0)
                        program_cache = cache_result["result"].get("programCacheSize", 0)
                        update_metric(solana_rpc_account_cache_size, account_cache)
                        update_metric(solana_rpc_program_cache_size, program_cache)
                        logger.debug(f"Cache sizes - Account: {account_cache}, Program: {program_cache}")
            except Exception as e:
                logger.debug(f"Cache info not available: {e}")
                update_metric(solana_rpc_account_cache_size, 0)
                update_metric(solana_rpc_program_cache_size, 0)

            # Get WebSocket connections
            ws_payload = {
                "jsonrpc": "2.0", "id": 1, "method": "getWebsocketInfo"
            }
            try:
                async with session.post(SOLANA_RPC_ENDPOINT, json=ws_payload, headers=HEADERS) as response:
                    ws_result = await response.json()
                    if "result" in ws_result:
                        connections = ws_result["result"].get("connections", 0)
                        update_metric(solana_rpc_websocket_connections, connections)
                        logger.debug(f"Active WebSocket connections: {connections}")
            except Exception as e:
                logger.debug(f"WebSocket info not available: {e}")
                update_metric(solana_rpc_websocket_connections, 0)

    except aiohttp.ClientError as e:
        logger.error(f"Network error occurred while fetching node health: {e}")
        update_metric(solana_node_health, 0, labels={"status": "unhealthy", "cause": "network_error"})
    except Exception as e:
        logger.error(f"Error getting node health: {e}")
        update_metric(solana_node_health, 0, labels={"status": "unhealthy", "cause": "unknown"})
