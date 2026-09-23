# Critical Diagnostic Logging Added to FLServer

## Summary of Changes

Added granular **thread-aware logging** to pinpoint exactly which thread hangs and at which line.

## Key Findings

### 1. `self.round_updates` Type Confirmation

**Line 125 in FLServer.__init__:**
```python
self.round_updates: Dict[int, Dict[str, Tuple[Dict, int]]] = {}
```

**Status:** Plain Python dict. NOT a multiprocessing.Manager().dict() or any thread-safe wrapper.

### 2. CRITICAL BUG FOUND: Unprotected Concurrent Access

**Location:** `get_round_status()` method - was reading `self.round_updates` **without acquiring the lock**, while `submit_update` modifies it under the lock.

**FIXED:** Now protects all reads with the same lock used for writes.

## Diagnostic Logging Added

### Critical Section: Dict Assignment

**Most detailed logging around the hang point (lines 214-225):**

```python
thread_name = threading.current_thread().name
logger.info(f"[LOCK] {client_id} thread={thread_name} BEFORE dict assignment: round_num={round_num}, weights type={type(self.round_updates[round_num])}")

logger.info(f"[LOCK] {client_id} thread={thread_name} attempting to assign weights to round_updates[{round_num}][{client_id}]")
self.round_updates[round_num][client_id] = (weights, num_samples)
logger.info(f"[LOCK] {client_id} thread={thread_name} AFTER dict assignment: successfully stored")

logger.info(
    f"[LOCK] {client_id} thread={thread_name} stored update for round {round_num} "
    f"({len(self.round_updates[round_num])}/{self.num_clients} clients)"
)
```

**This pinpoints:**
- Which thread is executing (from thread_name)
- What type `self.round_updates[round_num]` actually is (should be `<class 'dict'>`)
- Which of the 3 lines actually hangs

## Expected Successful Log Flow

```
[ROUTE] Update submission from client_0 for round 0
[ROUTE] Submitting work to worker executor
[LOCK] client_0 thread=fl_worker_0 attempting to acquire state lock for round 0
[LOCK] client_0 thread=fl_worker_0 acquired state lock
[LOCK] client_0 thread=fl_worker_0 initializing round 0 updates dict
[LOCK] client_0 thread=fl_worker_0 BEFORE dict assignment: round_num=0, weights type=<class 'dict'>
[LOCK] client_0 thread=fl_worker_0 attempting to assign weights to round_updates[0][client_0]
[LOCK] client_0 thread=fl_worker_0 AFTER dict assignment: successfully stored
[LOCK] client_0 thread=fl_worker_0 stored update for round 0 (1/5 clients)
[ROUTE] Update from client_0 accepted for round 0
```

## If Hang Occurs: What to Check

1. **Exactly which line freezes** - Look for which log appears but the next one doesn't
2. **Thread name** - Is it a worker thread (fl_worker_N) or something else?
3. **Dict type** - Is it really a plain `<class 'dict'>`?
4. **Race condition evidence** - Do `[ROUND_STATUS]` logs appear during `[LOCK]` operations?

