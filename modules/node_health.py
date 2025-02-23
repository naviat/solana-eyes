# modules/node_health.py
import aiohttp
import time
from loguru import logger
from config import SOLANA_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from prometheus.metrics import (
    solana_node_health, solana_node_slots_behind,
    solana_rpc_requests, solana_rpc_errors, solana_rpc_latency
)

async def get_health():
    """Check the health status of the RPC node and collect performance metrics"""
    try:
        async with aiohttp.ClientSession() as session:
            # Health check
            start_time = time.time()
            health_payload = {
                "jsonrpc": "2.0", "id": 1, "method": "getHealth"
            }
            
            async with session.post(SOLANA_RPC_ENDPOINT, json=health_payload, headers=HEADERS) as response:
                result = await response.json()
                end_time = time.time()
                
                # Update latency metric
                latency = end_time - start_time
                update_metric(solana_rpc_latency, latency, labels={"method": "getHealth"})
                update_metric(solana_rpc_requests, 1, labels={"method": "getHealth"})

            if "result" in result and result["result"] == "ok":
                update_metric(solana_node_health, 1, labels={"status": "healthy", "cause": "none"})
                logger.info("RPC node is healthy")
                last_slots_behind = solana_node_slots_behind._value.get()
                if last_slots_behind:
                    logger.info(f"RPC node is healthy. Last recorded slots behind when unhealthy: {last_slots_behind}")
            elif "error" in result:
                error_message = result["error"].get("message", "Unknown error")
                slots_behind = result["error"]["data"].get("numSlotsBehind", 0)
                update_metric(solana_node_health, 0, labels={"status": "unhealthy", "cause": "slots_behind"})
                update_metric(solana_node_slots_behind, slots_behind)
                update_metric(solana_rpc_errors, 1, labels={"method": "getHealth"})
                # Enhanced logging for unhealthy state with slots behind
                logger.error(
                    "RPC node is unhealthy\n"
                    f"Error message: {error_message}\n"
                    f"Current slots behind: {slots_behind}\n"
                    f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                logger.error("Unexpected response format")
                update_metric(solana_node_health, 0, labels={"status": "unhealthy", "cause": "unknown"})

    except aiohttp.ClientError as e:
        logger.error(f"Network error occurred while fetching node health: {e}")
        update_metric(solana_node_health, 0, labels={"status": "unhealthy", "cause": "network_error"})
    except Exception as e:
        logger.error(f"Error getting node health: {e}")
        update_metric(solana_node_health, 0, labels={"status": "unhealthy", "cause": "unknown"})
