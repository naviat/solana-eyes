import asyncio
from loguru import logger
from modules.node_health import get_health
from modules.slot_monitor import get_slot_info, get_block_heights
from modules.tx_monitor import get_transaction_stats, get_transaction_types
from modules.version import get_version
from modules.websocket_monitor import check_websocket_health
from modules.epoch_monitor import get_epoch_info


async def run_async_tasks():
    """Run all async monitoring tasks"""
    tasks = {
        "health": get_health(),
        "slot_info": get_slot_info(),
        "block_heights": get_block_heights(),
        "tx_stats": get_transaction_stats(),
        "tx_types": get_transaction_types(),
        "version": get_version(),
        "websocket": check_websocket_health(),
        "epoch_info": get_epoch_info()
    }

    try:
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        for task_name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Error in {task_name}: {result}")
    except Exception as e:
        logger.error(f"Error in collector: {e}")


async def collect():
    """Main collection function"""
    logger.info("Starting metrics collection")
    start_time = asyncio.get_event_loop().time()

    await run_async_tasks()

    end_time = asyncio.get_event_loop().time()
    logger.info(f"Metrics collection completed in {end_time - start_time:.2f} seconds")
