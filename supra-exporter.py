"""
Supra Mainnet Validator Prometheus Exporter by Silk Nodes

Exports:
- supra_validator_block_height: current block height of local node
- supra_public_block_height: current block height from public RPC
- supra_validator_health: 1 if local node is within 10 blocks of public RPC, 0 otherwise
"""

import subprocess
import time
import re
import requests
from prometheus_client import start_http_server, Gauge, CollectorRegistry

# ------------------------------
# Configuration
# ------------------------------
EXPORTER_PORT = 8889
PUBLIC_BLOCK_URL = "https://rpc-mainnet.supra.com/rpc/v1/block"
LOG_FILE = "supra_configs_mainnet/supra_node_logs/supra.log" # Replace with your path
POLL_INTERVAL = 10  # seconds for public RPC polling
BLOCK_HEIGHT_REGEX = re.compile(r"Block height:\s*\((\d+)\)")

# ------------------------------
# Prometheus setup
# ------------------------------
registry = CollectorRegistry()
validator_block_height_gauge = Gauge(
    "supra_validator_block_height",
    "Local validator block height",
    registry=registry
)
public_block_height_gauge = Gauge(
    "supra_public_block_height",
    "Public RPC block height",
    registry=registry
)
validator_health_gauge = Gauge(
    "supra_validator_health",
    "1 if local validator is within 10 blocks of public RPC, 0 otherwise",
    registry=registry
)

# ------------------------------
# Functions
# ------------------------------
def follow_log_file(filepath):
    """Yield new lines from a log file using tail -F"""
    proc = subprocess.Popen(
        ["tail", "-F", filepath],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    for line in proc.stdout:
        yield line.strip()

def get_public_block_height():
    """Fetch block height from public block endpoint."""
    try:
        response = requests.get(PUBLIC_BLOCK_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        return int(data.get("height", 0))
    except Exception as e:
        print(f"Error fetching public block height: {e}")
        return 0

# ------------------------------
# Main loop
# ------------------------------
def main():
    print(f"Starting Supra Exporter on port {EXPORTER_PORT}")
    start_http_server(EXPORTER_PORT, registry=registry)

    last_local_height = 0
    last_public_poll = 0
    public_height = 0

    # Follow the log file continuously
    for line in follow_log_file(LOG_FILE):
        # Update local validator height
        match = BLOCK_HEIGHT_REGEX.search(line)
        if match:
            last_local_height = int(match.group(1))
            validator_block_height_gauge.set(last_local_height)

        # Poll public RPC every POLL_INTERVAL seconds
        now = time.time()
        if now - last_public_poll >= POLL_INTERVAL:
            public_height = get_public_block_height()
            public_block_height_gauge.set(public_height)

            # Update health metric
            if public_height > 0:
                health = 1 if last_local_height >= public_height - 10 else 0
                validator_health_gauge.set(health)
            else:
                validator_health_gauge.set(0)

            # Print metrics for console visibility
            print(f"[Metrics] Local: {last_local_height} | Public: {public_height} | Health: {health}")
            last_public_poll = now

# ------------------------------
# Entry point
# ------------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Exporter stopped by user.")
