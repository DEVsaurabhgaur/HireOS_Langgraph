"""
scripts/healthcheck.py
Simple health check script for deployment monitoring.

Usage:
    python scripts/healthcheck.py [url]
"""

import sys
import time
import urllib.request
import json


def check_health(base_url: str = "http://localhost:8000") -> bool:
    """Hit the /api/health endpoint and verify response."""
    url = f"{base_url}/api/health"
    try:
        start = time.time()
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            elapsed = round((time.time() - start) * 1000, 1)

            if data.get("status") == "ok":
                print(f"[OK] Health check passed ({elapsed}ms)")
                print(f"     Version: {data.get('version', 'unknown')}")
                return True
            else:
                print(f"[WARN] Unexpected response: {data}")
                return False

    except Exception as e:
        print(f"[FAIL] Health check failed: {e}")
        return False


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    success = check_health(url)
    sys.exit(0 if success else 1)
