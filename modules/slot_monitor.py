# modules/slot_monitor.py
import aiohttp, time
from loguru import logger
from config import SOLANA_RPC_ENDPOINT, NETWORK_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from metrics.metrics import (
    solana_current_slot, solana_net_current_slot, solana_slot_diff,
    solana_block_height, solana_network_block_height, solana_block_height_diff,
    solana_max_shred_insert_slot, solana_max_retransmit_slot,
    solana_net_max_shred_insert_slot, solana_net_max_retransmit_slot,
    solana_rpc_requests, solana_rpc_errors, solana_rpc_latency
)

async def get_shred_slots(session, endpoint, is_network=False):
    """Get shred insert and retransmit slots for the specified endpoint"""
    payloads = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getMaxShredInsertSlot"
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "getMaxRetransmitSlot"
        }
    ]

    try:
        results = []
        for payload in payloads:
            start_time = time.time()
            async with session.post(endpoint, json=payload, headers=HEADERS) as response:
                result = await response.json()
                end_time = time.time()
                
                # Update latency and request metrics
                latency = end_time - start_time
                method = payload["method"]
                update_metric(solana_rpc_latency, latency, labels={"method": method})
                update_metric(solana_rpc_requests, 1, labels={"method": method})
                
                if "error" in result:
                    update_metric(solana_rpc_errors, 1, labels={"method": method})
                results.append(result)
        # Process shred insert slot
        if "result" in results[0]:
            shred_insert_slot = results[0]["result"]
            if is_network:
                update_metric(solana_net_max_shred_insert_slot, shred_insert_slot)
                logger.debug(f"Network max shred insert slot: {shred_insert_slot}")
            else:
                update_metric(solana_max_shred_insert_slot, shred_insert_slot)
                logger.debug(f"Local max shred insert slot: {shred_insert_slot}")

        # Process retransmit slot
        if "result" in results[1]:
            retransmit_slot = results[1]["result"]
            if is_network:
                update_metric(solana_net_max_retransmit_slot, retransmit_slot)
                logger.debug(f"Network max retransmit slot: {retransmit_slot}")
            else:
                update_metric(solana_max_retransmit_slot, retransmit_slot)
                logger.debug(f"Local max retransmit slot: {retransmit_slot}")

    except Exception as e:
        logger.error(f"Error getting shred slots from {'network' if is_network else 'local'} endpoint: {e}")

async def get_slot_info():
    """Get slot information from both RPC nodes"""
    payload = {
        "jsonrpc": "2.0", 
        "id": 1, 
        "method": "getSlot",
        "params": [{"commitment": "finalized"}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Get slots from both endpoints
            start_time = time.time()
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                rpc_result = await response.json()
                end_time = time.time()
                # Update latency and request metrics
                latency = end_time - start_time
                update_metric(solana_rpc_latency, latency, labels={"method": "getSlot"})
                update_metric(solana_rpc_requests, 1, labels={"method": "getSlot"})
                
                current_slot = rpc_result.get('result')
                logger.debug(f"Local RPC slot: {current_slot}")
                if current_slot is not None:
                    update_metric(solana_current_slot, current_slot)

            async with session.post(NETWORK_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                network_result = await response.json()
                network_slot = network_result.get('result')
                logger.debug(f"Network RPC slot: {network_slot}")
                if network_slot is not None:
                    update_metric(solana_net_current_slot, network_slot)

            # Calculate and log slot difference
            if current_slot is not None and network_slot is not None:
                slot_diff = current_slot - network_slot
                update_metric(solana_slot_diff, slot_diff)
                if abs(slot_diff) > 100:
                    logger.warning(f"Large slot difference detected: {slot_diff} slots")
                    logger.warning(f"Local slot: {current_slot}, Network slot: {network_slot}")
                else:
                    logger.info(f"Slot difference: {slot_diff}")

            # Get shred slots for both endpoints
            await get_shred_slots(session, SOLANA_RPC_ENDPOINT, False)
            await get_shred_slots(session, NETWORK_RPC_ENDPOINT, True)

    except Exception as e:
        logger.error(f"Error getting slot information: {e}")

async def get_block_heights():
    """Get block heights from both RPC nodes"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getBlockHeight",
        "params": [{"commitment": "finalized"}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            # Get block heights from both endpoints
            start_time = time.time()
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                rpc_result = await response.json()
                end_time = time.time()
                # Update latency and request metrics
                latency = end_time - start_time
                update_metric(solana_rpc_latency, latency, labels={"method": "getBlockHeight"})
                update_metric(solana_rpc_requests, 1, labels={"method": "getBlockHeight"})
                
                rpc_height = rpc_result.get('result')
                logger.debug(f"Local RPC block height: {rpc_height}")
                if rpc_height is not None:
                    update_metric(solana_block_height, rpc_height)

            async with session.post(NETWORK_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                network_result = await response.json()
                network_height = network_result.get('result')
                logger.debug(f"Network block height: {network_height}")
                if network_height is not None:
                    update_metric(solana_network_block_height, network_height)

            # Calculate and log block height difference
            if rpc_height is not None and network_height is not None:
                height_diff = rpc_height - network_height
                update_metric(solana_block_height_diff, height_diff)
                if abs(height_diff) > 100:
                    logger.warning(f"Large block height difference detected: {height_diff} blocks")
                    logger.warning(f"Local height: {rpc_height}, Network height: {network_height}")
                else:
                    logger.info(f"Block height difference: {height_diff}")

    except Exception as e:
        logger.error(f"Error getting block heights: {e}")
