#!/usr/bin/env python3
"""
Manual test script: Fire 5 concurrent /register_client requests to verify server handles them without blocking.
Run this in a separate terminal while the server is running.
"""

import requests
import concurrent.futures
import time
import sys

SERVER_URL = "http://localhost:8000"

def register_client(client_idx: int) -> dict:
    """Register a single client."""
    client_id = f"client_{client_idx}"
    payload = {
        "client_id": client_id,
        "num_samples": 100 * (client_idx + 1),
    }
    
    print(f"[{time.strftime('%H:%M:%S')}] Sending registration for {client_id}...", flush=True)
    start = time.time()
    
    try:
        response = requests.post(
            f"{SERVER_URL}/register_client",
            json=payload,
            timeout=5,
        )
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"[{time.strftime('%H:%M:%S')}] ✓ {client_id} registered in {elapsed:.2f}s", flush=True)
            return {"client_id": client_id, "status": "success", "elapsed": elapsed}
        else:
            print(f"[{time.strftime('%H:%M:%S')}] ✗ {client_id} failed: {response.status_code}", flush=True)
            return {"client_id": client_id, "status": "failed", "elapsed": elapsed}
    except requests.exceptions.Timeout:
        elapsed = time.time() - start
        print(f"[{time.strftime('%H:%M:%S')}] ✗ {client_id} TIMEOUT after {elapsed:.2f}s", flush=True)
        return {"client_id": client_id, "status": "timeout", "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"[{time.strftime('%H:%M:%S')}] ✗ {client_id} error: {e} ({elapsed:.2f}s)", flush=True)
        return {"client_id": client_id, "status": "error", "elapsed": elapsed}


def test_concurrent_registrations():
    """Test 5 concurrent /register_client requests."""
    print("=" * 80)
    print("Testing concurrent /register_client requests")
    print("=" * 80)
    
    # First verify server is alive
    print("\nChecking server health...")
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=2)
        if response.status_code == 200:
            print(f"✓ Server is alive: {response.json()}")
        else:
            print(f"✗ Server returned {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Server unreachable: {e}")
        sys.exit(1)
    
    # Fire 5 concurrent registrations
    print(f"\n[{time.strftime('%H:%M:%S')}] Firing 5 concurrent registrations...")
    start_total = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(register_client, i) for i in range(5)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    total_elapsed = time.time() - start_total
    
    # Print summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    for result in results:
        status_symbol = "✓" if result["status"] == "success" else "✗"
        print(f"{status_symbol} {result['client_id']}: {result['status']} ({result['elapsed']:.2f}s)")
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nTotal: {success_count}/5 successful in {total_elapsed:.2f}s")
    
    if success_count == 5:
        print("\n✓ All registrations succeeded! Server is handling concurrent requests correctly.")
        return True
    else:
        print(f"\n✗ Only {success_count}/5 succeeded. Check server logs for errors.")
        return False


if __name__ == "__main__":
    success = test_concurrent_registrations()
    sys.exit(0 if success else 1)
