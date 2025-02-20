import aiohttp
from loguru import logger
from config import SOLANA_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from prometheus.metrics import (
    solana_tx_count, solana_tx_success_rate, solana_tx_error_rate,
    solana_rpc_processed_tx_count, solana_rpc_tx_by_type,
    solana_rpc_tx_latency
)

async def get_transaction_stats():
    """Get transaction statistics from the RPC node"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getRecentPerformanceSamples",
        "params": [5]  # Get last 5 samples
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                result = await response.json()

        if "result" in result and result["result"]:
            samples = result["result"]
            latest_sample = samples[0]

            # Process transaction counts
            tx_count = latest_sample.get("numTransactions", 0)
            tx_errors = latest_sample.get("numTransactionErrors", 0)
            
            update_metric(solana_tx_count, tx_count)
            update_metric(solana_rpc_processed_tx_count, tx_count)

            if tx_count > 0:
                success_rate = ((tx_count - tx_errors) / tx_count) * 100
                error_rate = (tx_errors / tx_count) * 100
                update_metric(solana_tx_success_rate, success_rate)
                update_metric(solana_tx_error_rate, error_rate)
                logger.info(f"Processed {tx_count} transactions, Success rate: {success_rate:.2f}%, Error rate: {error_rate:.2f}%")
            else:
                logger.debug("No transactions processed in the latest sample")

            # Calculate average latency from samples
            latencies = [sample.get("averageTransactionLatencyMs", 0) for sample in samples]
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                update_metric(solana_rpc_tx_latency, avg_latency, labels={"percentile": "50"})
                
                # Calculate 90th percentile
                sorted_latencies = sorted(latencies)
                p90_index = int(len(sorted_latencies) * 0.9)
                p90_latency = sorted_latencies[p90_index]
                update_metric(solana_rpc_tx_latency, p90_latency, labels={"percentile": "90"})
                logger.debug(f"Transaction latency - Avg: {avg_latency:.2f}ms, P90: {p90_latency:.2f}ms")

    except Exception as e:
        logger.error(f"Error getting transaction stats: {e}")
        # Set metrics to 0 when there's an error
        update_metric(solana_tx_count, 0)
        update_metric(solana_rpc_processed_tx_count, 0)
        update_metric(solana_tx_success_rate, 0)
        update_metric(solana_tx_error_rate, 0)
        update_metric(solana_rpc_tx_latency, 0, labels={"percentile": "50"})
        update_metric(solana_rpc_tx_latency, 0, labels={"percentile": "90"})

async def get_transaction_types():
    """Get transaction type distribution from recent transactions"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getSignaturesForAddress",
        "params": [
            "11111111111111111111111111111111",  # System program
            {"limit": 100}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                result = await response.json()

        if "result" in result and isinstance(result["result"], list):
            tx_types = {}
            for tx in result["result"]:
                tx_status = "success"
                if tx.get("err"):
                    tx_status = "error"
                elif tx.get("memo"):
                    tx_status = "memo"
                
                tx_types[tx_status] = tx_types.get(tx_status, 0) + 1

            # Update metrics for each transaction type
            for tx_type, count in tx_types.items():
                update_metric(solana_rpc_tx_by_type, count, labels={"tx_type": tx_type})
                
            if tx_types:
                logger.info(f"Transaction type distribution: {tx_types}")
            else:
                logger.debug("No transactions found in the recent history")
        else:
            logger.warning("Unexpected response format for transaction types")

    except Exception as e:
        logger.error(f"Error getting transaction types: {e}")
        # Set metric to 0 for common transaction types when there's an error
        for tx_type in ["success", "error", "memo"]:
            update_metric(solana_rpc_tx_by_type, 0, labels={"tx_type": tx_type})
