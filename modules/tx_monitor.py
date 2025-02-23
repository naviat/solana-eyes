import aiohttp
from loguru import logger
from config import SOLANA_RPC_ENDPOINT, HEADERS
from utils.func import update_metric
from metrics.metrics import (
    solana_tx_count, solana_tx_success_rate, solana_tx_error_rate,
    solana_rpc_processed_tx_count, solana_rpc_tx_by_type,
    solana_rpc_tx_latency, solana_confirmed_transactions_total
)

async def get_transaction_stats():
    """Get transaction statistics from the RPC node"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getRecentPerformanceSamples",
        "params": [10]  # Get last 10 samples
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
            non_vote_tx = latest_sample.get("numNonVoteTransactions", 0)
            sample_period = latest_sample.get("samplePeriodSecs", 60)
            
            # Calculate TPS (Transactions Per Second)
            tps = tx_count / sample_period if sample_period > 0 else 0
            non_vote_tps = non_vote_tx / sample_period if sample_period > 0 else 0
            
            update_metric(solana_tx_count, tx_count)
            update_metric(solana_rpc_processed_tx_count, non_vote_tx)
            update_metric(solana_rpc_tx_latency, tps, labels={"type": "total_tps"})
            update_metric(solana_rpc_tx_latency, non_vote_tps, labels={"type": "non_vote_tps"})
                
            logger.info(f"Transaction stats - Total: {tx_count}, Non-vote: {non_vote_tx}, TPS: {tps:.2f}, Non-vote TPS: {non_vote_tps:.2f}")

    except Exception as e:
        logger.error(f"Error getting transaction stats: {e}")
        # Set metrics to 0 when there's an error
        update_metric(solana_tx_count, 0)
        update_metric(solana_rpc_processed_tx_count, 0)
        update_metric(solana_rpc_tx_latency, 0, labels={"type": "total_tps"})
        update_metric(solana_rpc_tx_latency, 0, labels={"type": "non_vote_tps"})

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
            tx_types = {
                "success": 0,
                "error": 0,
                "memo": 0
            }
            
            total_tx = len(result["result"])
            
            for tx in result["result"]:
                if tx.get("err"):
                    tx_types["error"] += 1
                elif tx.get("memo"):
                    tx_types["memo"] += 1
                else:
                    tx_types["success"] += 1

            # Update metrics for each transaction type
            for tx_type, count in tx_types.items():
                update_metric(solana_rpc_tx_by_type, count, labels={"tx_type": tx_type})

            # Calculate success/error rates
            if total_tx > 0:
                success_rate = (tx_types["success"] / total_tx) * 100
                error_rate = (tx_types["error"] / total_tx) * 100
                
                update_metric(solana_tx_success_rate, success_rate)
                update_metric(solana_tx_error_rate, error_rate)
                
                logger.info(f"Transaction types - Distribution: {tx_types}, Success: {success_rate:.2f}%, Error: {error_rate:.2f}%")

    except Exception as e:
        logger.error(f"Error getting transaction types: {e}")
        # Set metric to 0 for common transaction types when there's an error
        for tx_type in ["success", "error", "memo"]:
            update_metric(solana_rpc_tx_by_type, 0, labels={"tx_type": tx_type})
        update_metric(solana_tx_success_rate, 0)
        update_metric(solana_tx_error_rate, 0)

async def get_confirmed_transactions_total():
    """Get total confirmed transactions"""
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTransactionCount",
        "params": [{"commitment": "finalized"}]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                result = await response.json()

        if "result" in result:
            total_tx = result["result"]
            update_metric(solana_confirmed_transactions_total, total_tx)
            logger.info(f"Total confirmed transactions: {total_tx:,.0f}")

    except Exception as e:
        logger.error(f"Error getting total transactions: {e}")
        update_metric(solana_confirmed_transactions_total, 0)
