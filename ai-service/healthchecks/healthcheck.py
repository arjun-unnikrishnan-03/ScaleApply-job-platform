#!/usr/bin/env python3
"""
Self-contained container healthcheck script using only the Python standard library.
Queries FastAPI liveness (/health) and readiness (/ready) endpoints.
"""

import json
import sys
import urllib.error
import urllib.request


def check_endpoint(url: str, expected_status: str, expected_code: int = 200) -> bool:
    try:
        req = urllib.request.Request(url)
        # Use a reasonable timeout
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != expected_code:
                print(f"[{url}] Failed: HTTP status {response.status}", file=sys.stderr)
                return False
            
            data = json.loads(response.read().decode("utf-8"))
            status_val = data.get("status")
            if status_val != expected_status:
                print(f"[{url}] Failed: status was '{status_val}', expected '{expected_status}'", file=sys.stderr)
                print(f"Response: {data}", file=sys.stderr)
                return False
            
            return True
    except urllib.error.HTTPError as e:
        print(f"[{url}] HTTP Error {e.code}: {e.read().decode('utf-8', errors='replace')}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"[{url}] URL Error: {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[{url}] Unhandled exception during check: {e}", file=sys.stderr)
        return False


def main() -> None:
    # 1. Liveness check: must return 200 and status="healthy"
    liveness_ok = check_endpoint("http://localhost:8000/health", "healthy")
    if not liveness_ok:
        sys.exit(1)

    # 2. Readiness check: must return 200 and status="ready" (checks Qdrant/LLM setup)
    readiness_ok = check_endpoint("http://localhost:8000/ready", "ready")
    if not readiness_ok:
        sys.exit(1)

    print("All healthchecks passed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
