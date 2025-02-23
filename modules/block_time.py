import aiohttp
import time
from loguru import logger
from config import SOLANA_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from metrics.metrics import solana_block_time, solana_block_time_diff

async def get_block_time():
    """Get current block time and calculate time difference"""
    try:
        # First get current slot
        slot_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSlot",
            "params": [{"commitment": "finalized"}]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(SOLANA_RPC_ENDPOINT, json=slot_payload, headers=HEADERS) as response:
                slot_result = await response.json()
                
            if "result" not in slot_result:
                logger.error("Failed to get current slot")
                return

            current_slot = slot_result["result"]

            # Get block time for the slot
            block_time_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlockTime",
                "params": [current_slot]
            }

            async with session.post(SOLANA_RPC_ENDPOINT, json=block_time_payload, headers=HEADERS) as response:
                result = await response.json()

            if "result" in result:
                block_time = result["result"]
                current_time = int(time.time())
                time_diff = current_time - block_time

                # Update metrics
                update_metric(solana_block_time, block_time)
                update_metric(solana_block_time_diff, time_diff)

                logger.info(f"Block time - Slot: {current_slot}, Time diff: {time_diff}s")
            else:
                logger.error("Failed to get block time")

    except Exception as e:
        logger.error(f"Error getting block time: {e}")
        # Reset metrics on error
        update_metric(solana_block_time, 0)
        update_metric(solana_block_time_diff, 0)
