import asyncio, sys
import signal
from prometheus_client import start_http_server
import time
from loguru import logger
from config import SLEEP_TIME, PORT, LOG_LEVEL
from exporter.collector import collect


async def graceful_shutdown(loop, sig=None):
    """Handles graceful shutdown on receiving a signal"""
    if sig:
        logger.info(f"Received exit signal {sig.name}...")

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")
    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


def setup_signals(loop):
    """Setup signal handling for graceful shutdown"""
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(graceful_shutdown(loop, s)))


async def run_exporter():
    """Main function to run the Prometheus exporter"""
    logger.info(f"Starting Prometheus metrics server on localhost:{PORT}/metrics")
    start_http_server(PORT)

    while True:
        start_time = time.time()
        logger.info("Starting collection of metrics")
        try:
            await collect()
            logger.info(f"Metrics collected successfully in {time.time() - start_time:.2f} seconds")
        except Exception as e:
            logger.error(f"Error during metrics collection: {e}")

        logger.info(f"Sleeping for {SLEEP_TIME} seconds")
        await asyncio.sleep(SLEEP_TIME)


def main():
    """Main entry point for the exporter"""
    logger.remove()
    logger.add("logs/monitor.log",
               level=LOG_LEVEL,
               format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
               rotation="00:00",
               retention="6 days",
               compression=None,
               backtrace=True,
               diagnose=True,
               enqueue=True)
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        level=LOG_LEVEL,
        colorize=True
    )
    
    loop = asyncio.get_event_loop()
    setup_signals(loop)
    try:
        loop.run_until_complete(run_exporter())
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        logger.info("Shutting down RPC monitor")
        loop.close()
