import aiohttp
from loguru import logger
from config import HEADERS, SOLANA_RPC_ENDPOINT, PORT
from utils.func import update_metric
from prometheus.metrics import solana_node_version

PROMETHEUS_METRICS_URL = f"http://localhost:{PORT}/metrics"

async def get_version():
    """Get the version of the Solana RPC node"""
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getVersion"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(SOLANA_RPC_ENDPOINT, json=payload, headers=HEADERS) as response:
                result = await response.json()

        if "result" in result:
            current_version = result['result'].get('solana-core')
            if current_version:
                # Get previous versions to update their status to 0
                async with aiohttp.ClientSession() as session:
                    async with session.get(PROMETHEUS_METRICS_URL) as response:
                        metrics = await response.text()
                
                all_versions = [
                    line.split('{')[1].split('}')[0].split('=')[1].replace('"', '')
                    for line in metrics.splitlines()
                    if line.startswith(f'{solana_node_version._name}') and '1.0' in line
                ]

                # Set old versions to 0
                for version in all_versions:
                    if version != current_version:
                        update_metric(solana_node_version, 0, labels={"version": version})

                # Set current version to 1
                update_metric(solana_node_version, 1, labels={"version": current_version})
                logger.info(f"RPC node version: {current_version}")
        else:
            logger.error("No version information in response")

    except Exception as e:
        logger.error(f"Error getting RPC node version: {e}")
