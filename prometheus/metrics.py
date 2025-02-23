from prometheus_client import Gauge

# Node health metrics
solana_node_health = Gauge('solana_node_health', 'Health status of the Solana RPC node', ['status', 'cause'])
solana_node_slots_behind = Gauge('solana_node_slots_behind', 'Number of slots the Solana RPC node is behind')
solana_node_version = Gauge('solana_node_version', 'Node version of solana RPC', ['version'])

# Block and slot metrics
solana_block_height = Gauge('solana_block_height', 'Current Block Height of your RPC node')
solana_network_block_height = Gauge('solana_network_block_height', 'Current Block Height of reference network')
solana_block_height_diff = Gauge('solana_block_height_diff', 'Block Height difference between your RPC and network')

solana_current_slot = Gauge('solana_current_slot', 'Current RPC node slot height')
solana_net_current_slot = Gauge('solana_net_current_slot', 'Current network slot height')
solana_slot_diff = Gauge('solana_slot_diff', 'Slot difference between your RPC and network')

# Shred metrics
solana_max_shred_insert_slot = Gauge('solana_max_shred_insert_slot', 'Max slot seen from after shred insert')
solana_max_retransmit_slot = Gauge('solana_max_retransmit_slot', 'Max slot seen from retransmit stage')
solana_net_max_shred_insert_slot = Gauge('solana_net_max_shred_insert_slot', 'Max NETWORK slot seen from after shred insert')
solana_net_max_retransmit_slot = Gauge('solana_net_max_retransmit_slot', 'Max NETWORK slot seen from retransmit stage')

# RPC performance metrics
solana_rpc_highest_processed_slot = Gauge('solana_rpc_highest_processed_slot', 'Highest slot processed by the RPC node')
solana_rpc_requests = Gauge('solana_rpc_requests', 'Total RPC requests', ['method'])
solana_rpc_errors = Gauge('solana_rpc_errors', 'Total RPC errors', ['method'])
solana_rpc_latency = Gauge('solana_rpc_latency', 'RPC request latency in seconds', ['method'])

# WebSocket metrics
solana_rpc_websocket_connections = Gauge('solana_rpc_websocket_connections', 'WebSocket connection status (1=connected, 0=disconnected)')
solana_rpc_websocket_latency = Gauge('solana_rpc_websocket_latency', 'WebSocket connection latency in milliseconds')

# Transaction metrics
solana_tx_count = Gauge('solana_tx_count', 'Total transaction count')
solana_tx_success_rate = Gauge('solana_tx_success_rate', 'Transaction success rate')
solana_tx_error_rate = Gauge('solana_tx_error_rate', 'Transaction error rate')
solana_rpc_processed_tx_count = Gauge('solana_rpc_processed_tx_count', 'Number of transactions processed')
solana_rpc_tx_by_type = Gauge('solana_rpc_tx_by_type', 'Transaction count by type', ['tx_type'])
solana_rpc_tx_latency = Gauge('solana_rpc_tx_latency', 'Transactions per second', ['type'])

# Epoch metrics
solana_network_epoch = Gauge('solana_network_epoch', 'Current epoch of network')
solana_slot_in_epoch = Gauge('solana_slot_in_epoch', 'Current slot in epoch')
solana_slot_index = Gauge('solana_slot_index', 'Current slot index')
