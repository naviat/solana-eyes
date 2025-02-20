import aiohttp
from loguru import logger
from config import SOLANA_RPC_ENDPOINT, NETWORK_RPC_ENDPOINT, HEADERS, RETRY
from utils.func import update_metric
from prometheus.metrics import (
    solana_current_slot, solana_net_current_slot, solana_slot_diff,
    solana_rpc_highest_processed_slot, solana_block_height,
    solana_network_block_height, solana_block_height_diff
)

async def get_slot_info():
    """Get slot information from both RPC nodes"""
    payload = [
        {"jsonrpc": "2.0", "id": 1, "method": "getSlot", "params": [{"commitment": "confirmed"}]},
        {"jsonrpc": "2.0", "id": 2, "method": "getHighestProcessedSlot"}
    ]

    try:
        # Get slots from your RPC node
        async with aiohttp.ClientSession() as session:
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                rpc_result = await response.json()
            
            # Get slot from reference network
            async with session.post(NETWORK_RPC_ENDPOINT, json=payload[0], headers=HEADERS) as response:
                network_result = await response.json()

        # Process RPC node results
        if isinstance(rpc_result, list) and len(rpc_result) >= 2:
            current_slot = rpc_result[0].get('result')
            highest_processed = rpc_result[1].get('result')
            
            if current_slot is not None:
                update_metric(solana_current_slot, current_slot)
            if highest_processed is not None:
                update_metric(solana_rpc_highest_processed_slot, highest_processed)
        
        # Process network results
        if "result" in network_result:
            network_slot = network_result["result"]
            update_metric(solana_net_current_slot, network_slot)
            
            # Calculate slot difference
            if current_slot is not None and network_slot is not None:
                slot_diff = network_slot - current_slot
                update_metric(solana_slot_diff, slot_diff)
                logger.debug(f"Slot difference: {slot_diff}")

    except Exception as e:
        logger.error(f"Error getting slot information: {e}")

async def get_block_heights():
    """Get block heights from both RPC nodes"""
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "getBlockHeight"
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Get block height from your RPC node
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                rpc_result = await response.json()
            
            # Get block height from reference network
            async with session.post(NETWORK_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                network_result = await response.json()

        rpc_height = rpc_result.get('result')
        network_height = network_result.get('result')

        if rpc_height is not None:
            update_metric(solana_block_height, rpc_height)
        if network_height is not None:
            update_metric(solana_network_block_height, network_height)

        if rpc_height is not None and network_height is not None:
            height_diff = network_height - rpc_height
            update_metric(solana_block_height_diff, height_diff)
            logger.debug(f"Block height difference: {height_diff}")

    except Exception as e:
        logger.error(f"Error getting block heights: {e}")
