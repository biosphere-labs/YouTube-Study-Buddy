# Simplified Tor Parallel Processing Architecture

## Overview

**Single facade pattern**: `TorExitNodeManager` is the ONLY class that workers interact with for Tor connections.

## The Problem We Discovered

**A single Tor daemon maintains ONE circuit at a time.**

Multiple `requests.Session` objects connecting to the same Tor daemon all share the same exit IP. Keeping sessions open does NOT give you different IPs.

## The Solution

**Multiple Tor daemon instances** - one per worker.

```
Worker 0 → Tor Daemon #1 (port 9050) → Unique Exit IP
Worker 1 → Tor Daemon #2 (port 9052) → Unique Exit IP
Worker 2 → Tor Daemon #3 (port 9054) → Unique Exit IP
```

## Architecture

```
┌─────────────────────────────────────────┐
│      TorExitNodeManager (Facade)        │
│  - Auto-detects Tor instances           │
│  - Assigns workers to instances          │
│  - Tracks exit IPs in daily JSON         │
└─────────────────┬───────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
    ┌────▼────┐       ┌───▼─────┐
    │ Tor #1  │       │ Tor #2  │  ...
    │ :9050   │       │ :9052   │
    └─────────┘       └─────────┘
```

### Single Facade Class

**`TorExitNodeManager`** (`tor_exit_manager.py`):

```python
# Initialize (auto-detects Tor instances)
manager = TorExitNodeManager()

# Worker gets configured fetcher
fetcher = manager.get_fetcher_for_worker(worker_id=0)

# Use fetcher normally
transcript = fetcher.fetch_transcript(video_id)
```

That's it. One class, one method call.

### What It Does

1. **Auto-detects Tor instances** by probing ports 9050, 9052, 9054, 9056, 9058
2. **Assigns workers to instances** using round-robin (worker_id % num_instances)
3. **Returns TorTranscriptFetcher** configured for assigned instance
4. **Tracks exit IPs** in `data/daily_exit_tracking.json` (via daily_exit_tracker)

### CLI Integration

```python
# In cli.py - initialize manager
self.tor_manager = TorExitNodeManager()

# In process_single_url - get fetcher for worker
tor_fetcher = self.tor_manager.get_fetcher_for_worker(worker_id)
processor.provider.tor_fetcher = tor_fetcher
```

Clean and simple. No complex coordination, no locks, no queues.

## Setup

### Start Multiple Tor Instances

```bash
# Start 5 Tor instances
docker-compose -f docker-compose.yml -f docker-compose.parallel.yml up -d

# Or use helper script
./scripts/tor-parallel-setup.sh
```

### Run Parallel Processing

```bash
uv run yt-study-buddy --parallel --workers 5 --file urls.txt
```

Output:
```
Initializing Tor exit node manager...
  ✓ Detected Tor #1 on port 9050
  ✓ Detected Tor #2 on port 9052
  ✓ Detected Tor #3 on port 9053
  ✓ Detected Tor #4 on port 9056
  ✓ Detected Tor #5 on port 9058
✓ Detected 5 Tor instances - true parallel processing enabled
```

## Files

### Core Files (Keep)
- `src/yt_study_buddy/tor_exit_manager.py` - **Single facade class**
- `src/yt_study_buddy/tor_transcript_fetcher.py` - Low-level Tor fetcher
- `src/yt_study_buddy/daily_exit_tracker.py` - Tracks IPs in JSON
- `src/yt_study_buddy/cli.py` - CLI integration
- `docker-compose.yml` - Single Tor instance (base)
- `docker-compose.parallel.yml` - Multiple Tor instances (extension)

### Removed Files (Broken/Complex)
- ~~`tor_ip_queue.py`~~ - Based on flawed assumption (multiple sessions = unique IPs)
- ~~`rotating_tor_client.py`~~ - Unnecessary complexity
- ~~`tor_pool_manager.py`~~ - Replaced by simpler TorExitNodeManager

## Exit IP Tracking

Daily tracking is integrated into `TorExitNodeManager`:

```python
stats = manager.get_stats()

# Returns:
{
    'tor_instances': 5,
    'multi_instance': True,
    'daily_tracking': {
        'date': '2025-10-28',
        'total_attempts': 42,
        'unique_ips_used': 15,
        'successful_fetches': 38,
        'failed_fetches': 4
    }
}
```

Tracking file: `data/daily_exit_tracking.json`

## How Workers Get Assigned

Round-robin assignment:
```python
instance_idx = worker_id % num_instances

# Example with 5 instances:
Worker 0 → Tor #1 (9050)
Worker 1 → Tor #2 (9052)
Worker 2 → Tor #3 (9054)
Worker 3 → Tor #4 (9056)
Worker 4 → Tor #5 (9058)
Worker 5 → Tor #1 (9050)  ← wraps around
```

## Benefits

✅ **Single facade** - One class to rule them all
✅ **Auto-detection** - Finds available Tor instances automatically
✅ **Simple assignment** - Round-robin, no coordination needed
✅ **Integrated tracking** - Daily exit IPs tracked automatically
✅ **Graceful fallback** - Works with 1 instance (shows warning)
✅ **No broken code** - Removed all non-functional implementations

## Troubleshooting

**Only 1 Tor detected?**
```bash
docker-compose -f docker-compose.yml -f docker-compose.parallel.yml up -d
```

**No Tor detected?**
```bash
docker-compose up -d tor-proxy
```

**Verify instances:**
```bash
docker ps | grep tor-proxy
```

**Test each instance:**
```bash
for port in 9050 9052 9054 9056 9058; do
  ip=$(curl -s -x socks5://127.0.0.1:$port https://api.ipify.org)
  echo "Port $port: $ip"
done
```

## Summary

**One facade class (`TorExitNodeManager`) provides everything workers need:**
- Auto-detects Tor instances
- Assigns workers to instances
- Returns configured fetchers
- Tracks exit IPs

**Simple. Clean. Works.**

No complex queues, no broken assumptions, no coordination locks. Just multiple Tor daemons and simple round-robin assignment.
