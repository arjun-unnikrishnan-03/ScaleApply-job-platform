#!/bin/sh
# startup.sh
# Production startup script for ScaleApply AI Platform.

set -e

echo "========================================================================"
echo "  ScaleApply AI Platform - Production Startup & Diagnostics"
echo "========================================================================"

# 1. Environment Validation and Diagnostics
echo "[DIAGNOSTICS] Python version: $(python3 --version)"
echo "[DIAGNOSTICS] Current working directory: $(pwd)"

# Convert LOG_LEVEL to lowercase for uvicorn
UVICORN_LOG_LEVEL=$(echo "${LOG_LEVEL:-info}" | tr '[:upper:]' '[:lower:]')

echo "[DIAGNOSTICS] Configuration Summary:"
echo "  - LLM Provider:      ${LLM_PROVIDER:-gemini}"
echo "  - Gemini Model:      ${GEMINI_MODEL:-gemini-1.5-flash}"
echo "  - Qdrant Database:   http://${QDRANT_HOST:-localhost}:${QDRANT_PORT:-6333} (Collection: ${QDRANT_COLLECTION:-knowledge_base})"
echo "  - Redis Cache:       ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
echo "  - Log Level:         ${LOG_LEVEL:-INFO} (Uvicorn: ${UVICORN_LOG_LEVEL})"

# Validate API keys (warn but do not fail immediately, as health endpoint handles missing keys)
API_KEY="${GEMINI_API_KEY:-$LLM_API_KEY}"
if [ -z "$API_KEY" ]; then
    echo "========================================================================"
    echo "  [WARNING] GEMINI_API_KEY / LLM_API_KEY is not set!"
    echo "  The service will start, but requests to agents requiring Gemini LLM"
    echo "  will fail and readiness checks (/ready) will report 'degraded'."
    echo "========================================================================"
else
    # Mask API key for logs
    MASKED_KEY="$(echo "$API_KEY" | cut -c 1-6)...$(echo "$API_KEY" | cut -c $((${#API_KEY}-4))-${#API_KEY})"
    echo "[DIAGNOSTICS] Gemini API Key: Configured ($MASKED_KEY)"
fi

# 2. Wait for dependencies
SCRIPT_DIR="$(dirname "$0")"
if [ -f "$SCRIPT_DIR/wait_for_qdrant.sh" ]; then
    echo "[DIAGNOSTICS] Invoking Qdrant readiness check..."
    sh "$SCRIPT_DIR/wait_for_qdrant.sh"
else
    echo "[DIAGNOSTICS] Warning: wait_for_qdrant.sh not found in $SCRIPT_DIR, skipping network check."
fi

# 3. Start FastAPI application
echo "[DIAGNOSTICS] Launching FastAPI application via Uvicorn..."
exec uvicorn api.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers "${UVICORN_WORKERS:-2}" \
    --log-level "$UVICORN_LOG_LEVEL"
