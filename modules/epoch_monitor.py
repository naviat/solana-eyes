import aiohttp
from loguru import logger
from config import SOLANA_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from prometheus.metrics import (
    solana_network_epoch,
    solana_slot_in_epoch,
    solana_slot_index,
    solana_rpc_highest_processed_slot
)

async def get_epoch_info():
    """Get detailed epoch information"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getEpochInfo",
        "params": [{"commitment": "finalized"}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                result = await response.json()

            if "result" in result:
                epoch_info = result["result"]
                
                # Update epoch metrics
                current_epoch = epoch_info.get("epoch", 0)
                slot_index = epoch_info.get("slotIndex", 0)
                slots_in_epoch = epoch_info.get("slotsInEpoch", 0)
                
                update_metric(solana_network_epoch, current_epoch)
                update_metric(solana_slot_in_epoch, slots_in_epoch)
                update_metric(solana_slot_index, slot_index)
                
                logger.info(f"Epoch info - Current: {current_epoch}, Slot Index: {slot_index}, Slots in Epoch: {slots_in_epoch}")

            # Get highest processed slot
            highest_slot_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getHighestSnapshotSlot"
            }

            async with session.post(SOLANA_RPC_ENDPOINT, json=highest_slot_payload, headers=HEADERS) as response:
                result = await response.json()

            if "result" in result:
                highest_slot = result["result"].get("full", 0)
                update_metric(solana_rpc_highest_processed_slot, highest_slot)
                logger.info(f"Highest processed slot: {highest_slot}")

    except Exception as e:
        logger.error(f"Error getting epoch information: {e}")