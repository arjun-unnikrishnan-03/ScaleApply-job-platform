#!/bin/sh
# wait_for_qdrant.sh
# DevOps startup script to wait for Qdrant availability.

set -e

# Load defaults if not configured
QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
MAX_ATTEMPTS=30
SLEEP_SECS=2

echo "[DIAGNOSTICS] Checking Qdrant connection at http://${QDRANT_HOST}:${QDRANT_PORT}/"

# Use Python standard library to check HTTP endpoint, as curl/nc might not be installed.
python3 -c "
import sys
import time
import urllib.request

host = '${QDRANT_HOST}'
port = ${QDRANT_PORT}
url = f'http://{host}:{port}/'

for attempt in range(1, ${MAX_ATTEMPTS} + 1):
    try:
        # Pinging Qdrant root
        urllib.request.urlopen(url, timeout=3)
        print(f'[DIAGNOSTICS] Attempt {attempt}/{MAX_ATTEMPTS}: Connected to Qdrant!')
        sys.exit(0)
    except Exception as e:
        print(f'[DIAGNOSTICS] Attempt {attempt}/{MAX_ATTEMPTS}: Qdrant not ready ({e}). Retrying in ${SLEEP_SECS}s...')
        time.sleep(${SLEEP_SECS})

print('[DIAGNOSTICS] Error: Qdrant was not ready after ${MAX_ATTEMPTS} attempts.', file=sys.stderr)
sys.exit(1)
"
