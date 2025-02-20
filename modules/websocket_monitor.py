import asyncio
import json
import websockets
from loguru import logger
from config import SOLANA_WS_ENDPOINT
from utils.func import update_metric
from prometheus.metrics import solana_rpc_websocket_connections, solana_rpc_websocket_latency

async def check_websocket_health():
    """Check WebSocket connection health by subscribing to slots"""
    subscription_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "slotSubscribe"
    }

    try:
        start_time = asyncio.get_event_loop().time()
        async with websockets.connect(SOLANA_WS_ENDPOINT) as websocket:
            # Mark connection as successful
            update_metric(solana_rpc_websocket_connections, 1)
            logger.info(f"Successfully connected to WebSocket endpoint: {SOLANA_WS_ENDPOINT}")
            
            # Send subscription request
            await websocket.send(json.dumps(subscription_payload))
            
            # Wait for subscription confirmation
            response = await websocket.recv()
            response_data = json.loads(response)
            
            if "result" in response_data:
                end_time = asyncio.get_event_loop().time()
                latency = (end_time - start_time) * 1000  # Convert to milliseconds
                update_metric(solana_rpc_websocket_latency, latency)
                logger.info(f"WebSocket connection healthy - Latency: {latency:.2f}ms")

                # Unsubscribe
                unsubscribe_payload = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "slotUnsubscribe",
                    "params": [response_data["result"]]
                }
                await websocket.send(json.dumps(unsubscribe_payload))
                await websocket.recv()  # Wait for unsubscribe confirmation
                logger.debug("Successfully unsubscribed from slot updates")
            else:
                logger.error(f"Failed to subscribe to slots: {response_data}")
                update_metric(solana_rpc_websocket_connections, 0)

    except Exception as e:
        logger.error(f"WebSocket connection failed: {e}")
        update_metric(solana_rpc_websocket_connections, 0)
        update_metric(solana_rpc_websocket_latency, 0)