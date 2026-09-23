# Thread Pool Starvation Fix: FastAPI/Starlette Threading Model

## Problem Diagnosed

**Symptom:** When client_0 and client_1 submitted nearly simultaneously:
- client_0, client_3, client_4 succeeded
- client_1 submitted successfully but its request handler thread **never printed any [LOCK] logging**
- The 10-second lock timeout **never fired**
- Subsequent requests also hung with no logging
- Simple GET endpoints (/global_model) still responded

**Root Cause:** Thread pool starvation, NOT a lock deadlock.

## Why This Happened

FastAPI/Starlette uses two distinct thread pools:

1. **Request Handler Thread Pool** (via anyio)
   - Handles HTTP request routing and deserialization
   - Runs sync `def` route handlers in worker threads
   - Default limit: ~40 threads
   - **CRITICAL: If a thread blocks indefinitely, the slot is lost forever**

2. **Background Aggregation Thread** (via `threading.Thread`)
   - Runs in a separate, unmanaged thread
   - Does NOT consume request handler pool slots
   - Can block indefinitely without starving request handlers

## The Hang Sequence

When client_1's request handler thread gets stuck before reaching [LOCK] logging:
- The thread never returns to FastAPI's request handler pool
- That pool slot is permanently consumed
- New requests queue waiting for free slots
- They never even start executing (no [LOCK] logging)
- Lock timeout never fires because requests never reach that code

## Solution: Dedicated Worker Executor

Create a **separate, explicit ThreadPoolExecutor** that is completely independent from FastAPI's request handler pool.

### Architecture

```
HTTP Request (FastAPI/Starlette)
    ↓
Route Handler (brief, fast)
    ├─ Log: "[ROUTE] Update submission from client_X"
    ├─ Submit work to WORKER_EXECUTOR (non-blocking)
    └─ Wait with timeout for result
        ↓
WORKER_EXECUTOR Thread Pool (10 dedicated threads)
    ├─ Worker 1: Running server.submit_update()
    ├─ Worker 2: Free
    └─ Worker N: Running aggregation
        ↓
    Lock-protected state updates
    (with all lock timeouts)
        ↓
Response returned to FastAPI route handler
    └─ Route handler returns immediately
    └─ Frees FastAPI request handler slot
```

### Key Differences

**Before:**
- Route handler thread = request handler thread (permanent assignment until completion)
- If handler hangs → slot consumed forever
- Limited to ~40 concurrent handlers

**After:**
- Route handler thread (fast, just submits work) → returns immediately
- Worker executor thread (heavy lifting, can run in parallel)
- Route handler frees request handler slot immediately
- 10 dedicated workers for heavy work
