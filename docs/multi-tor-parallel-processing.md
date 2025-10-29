## Multi-Tor Parallel Processing

### The Fundamental Problem (Discovered)

**A single Tor daemon can only maintain ONE circuit at a time.**

This means:
- Multiple `requests.Session` objects connecting to the same Tor daemon **all use the same exit IP**
- Keeping sessions open does NOT give you different IPs
- The old working approach: rotate circuit → close session → open new session → get new circuit

### The Solution: Multiple Tor Daemons

To achieve true parallel processing with unique exit IPs, you need **multiple Tor daemon instances**.

**Architecture:**
```
Worker 1 → Tor Daemon #1 (port 9050) → Unique Exit IP #1
Worker 2 → Tor Daemon #2 (port 9052) → Unique Exit IP #2
Worker 3 → Tor Daemon #3 (port 9054) → Unique Exit IP #3
Worker 4 → Tor Daemon #4 (port 9056) → Unique Exit IP #4
Worker 5 → Tor Daemon #5 (port 9058) → Unique Exit IP #5
```

Each Tor daemon:
- Runs independently in its own Docker container
- Maintains its own circuit
- Has its own SOCKS port (9050, 9052, 9054, 9056, 9058)
- Has its own control port (9051, 9053, 9055, 9057, 9059)
- Uses its own data volume (independent state)

### Setup

#### 1. Start Multiple Tor Instances

**Option A: Using the setup script (recommended)**
```bash
./scripts/tor-parallel-setup.sh
# Follow the interactive menu to start 5 Tor instances
```

**Option B: Using docker-compose directly**
```bash
# Start 5 Tor instances
docker-compose -f docker-compose.yml -f docker-compose.parallel.yml up -d

# Verify they're running
docker ps | grep tor-proxy

# Test connectivity
curl -x socks5://127.0.0.1:9050 https://api.ipify.org  # Instance 1
curl -x socks5://127.0.0.1:9052 https://api.ipify.org  # Instance 2
curl -x socks5://127.0.0.1:9054 https://api.ipify.org  # Instance 3
curl -x socks5://127.0.0.1:9056 https://api.ipify.org  # Instance 4
curl -x socks5://127.0.0.1:9058 https://api.ipify.org  # Instance 5
```

#### 2. Run Parallel Processing

```bash
# The CLI auto-detects available Tor instances
uv run yt-study-buddy --parallel --workers 5 --file urls.txt
```

**Output:**
```
Detecting available Tor instances for parallel processing...
  ✓ Detected: Tor#1 (SOCKS:9050, Control:9051)
  ✓ Detected: Tor#2 (SOCKS:9052, Control:9053)
  ✓ Detected: Tor#3 (SOCKS:9054, Control:9055)
  ✓ Detected: Tor#4 (SOCKS:9056, Control:9057)
  ✓ Detected: Tor#5 (SOCKS:9058, Control:9059)
  Total detected: 5 instance(s)
✓ Detected 5 Tor instances for parallel processing
```

### How It Works

#### 1. Auto-Detection
The `TorPoolManager` probes ports 9050, 9052, 9054, 9056, 9058 (SOCKS ports) to detect available Tor instances.

#### 2. Worker Assignment
Workers are assigned to Tor instances using round-robin:
- Worker 0 → Tor instance 1 (9050)
- Worker 1 → Tor instance 2 (9052)
- Worker 2 → Tor instance 3 (9054)
- Worker 3 → Tor instance 4 (9056)
- Worker 4 → Tor instance 5 (9058)
- Worker 5 → Tor instance 1 (9050) ← wraps around
- ...

#### 3. Circuit Independence
Each worker connects to its assigned Tor daemon:
- `TorTranscriptFetcher(tor_host='127.0.0.1', tor_port=9052, tor_control_port=9053)`
- Each daemon maintains its own circuit
- Workers can rotate circuits independently
- No coordination locks needed

### Performance Comparison

#### Single Tor Instance (Sequential-ish)
```
9 videos, 3 workers, 1 Tor instance:
- Workers share same Tor circuit
- All see same exit IP
- YouTube may rate limit
- Effective speedup: ~1.5x (limited by shared circuit)
```

#### Multiple Tor Instances (True Parallel)
```
9 videos, 3 workers, 3 Tor instances:
- Each worker has dedicated Tor circuit
- Workers get different exit IPs
- No YouTube rate limiting
- Effective speedup: ~3x (full parallelism)
```

### Resource Usage

Each Tor instance:
- **RAM**: ~50-100MB per instance
- **CPU**: Minimal when idle, moderate during rotation
- **Disk**: ~50MB per data volume

5 instances total:
- **RAM**: ~250-500MB
- **CPU**: Negligible impact
- **Disk**: ~250MB

### Fallback Behavior

If only 1 Tor instance is detected, the CLI shows a warning:

```
⚠️  Only 1 Tor instance detected. For true parallel processing:
     docker-compose -f docker-compose.yml -f docker-compose.parallel.yml up -d
  With 1 instance, 3 workers will share circuits (slower)
```

The system still works, but workers share the same circuit (reduced performance).

### Configuration Files

#### docker-compose.yml (Base)
Contains single Tor instance (tor-proxy):
- SOCKS port: 9050
- Control port: 9051

#### docker-compose.parallel.yml (Extension)
Adds 4 more Tor instances:
- tor-proxy-2: ports 9052, 9053
- tor-proxy-3: ports 9054, 9055
- tor-proxy-4: ports 9056, 9057
- tor-proxy-5: ports 9058, 9059

Uses Docker Compose's override feature to extend base configuration.

### Code Architecture

#### TorPoolManager (`tor_pool_manager.py`)
- Auto-detects available Tor instances
- Assigns workers to instances (round-robin)
- Simple, no coordination locks needed

#### CLI Integration (`cli.py`)
```python
# Auto-detect Tor instances
self.tor_pool = TorPoolManager.auto_detect()

# Assign worker to Tor instance
tor_instance = self.tor_pool.get_tor_for_worker(worker_id)

# Create fetcher for assigned instance
tor_fetcher = TorTranscriptFetcher(
    tor_host=tor_instance.host,
    tor_port=tor_instance.socks_port,
    tor_control_port=tor_instance.control_port
)
```

### Troubleshooting

#### "Only 1 Tor instance detected"
**Cause**: docker-compose.parallel.yml not started
**Fix**: `docker-compose -f docker-compose.yml -f docker-compose.parallel.yml up -d`

#### "No Tor instances detected"
**Cause**: No Tor containers running
**Fix**: `docker-compose up -d tor-proxy`

#### Verify Tor instances are running
```bash
docker ps | grep tor-proxy

# Should show:
# ytstudybuddy-tor-proxy
# ytstudybuddy-tor-proxy-2
# ytstudybuddy-tor-proxy-3
# ytstudybuddy-tor-proxy-4
# ytstudybuddy-tor-proxy-5
```

#### Test individual instances
```bash
# Test each SOCKS port
for port in 9050 9052 9054 9056 9058; do
  ip=$(curl -s -x socks5://127.0.0.1:$port https://api.ipify.org)
  echo "Port $port: $ip"
done

# Should show 5 different IPs (usually)
```

### Benefits of This Approach

✅ **True parallel processing** - Each worker has dedicated circuit
✅ **No coordination locks** - Workers operate independently
✅ **Natural load balancing** - Round-robin assignment
✅ **Simple architecture** - No complex IP queues or pre-allocation
✅ **Works with standard Tor** - No special Tor configuration needed
✅ **Auto-detection** - Automatically finds available instances
✅ **Graceful fallback** - Works with 1 instance (shows warning)
✅ **Docker Compose native** - Uses standard Docker features

### Why the Old "Queue" Approach Failed

**The flawed assumption:**
- Multiple `requests.Session` objects can maintain different Tor circuits to the same daemon

**The reality:**
- A single Tor daemon has ONE active circuit
- All connections to that daemon share the circuit
- Closing and reopening the session is the only way to use a new circuit

**The working solution:**
- Multiple Tor daemons = Multiple circuits
- Each worker connects to a different daemon
- Natural parallelism without complex coordination

### Migration from Old Approach

**Old (broken):**
```python
# TorIPQueue tried to pre-allocate IPs with multiple sessions
queue = TorIPQueue(client, target_size=9)
queue.start()  # All sessions got same IP!
```

**New (working):**
```python
# TorPoolManager assigns workers to Tor daemons
pool = TorPoolManager.auto_detect()
tor = pool.get_tor_for_worker(worker_id)
fetcher = TorTranscriptFetcher(tor_port=tor.socks_port)
```

### Future Enhancements

Possible improvements:
- Dynamic scaling: Add/remove Tor instances based on load
- Health monitoring: Detect and skip unhealthy Tor instances
- Kubernetes support: Use K8s StatefulSets for Tor daemons
- Circuit metrics: Track rotation counts, success rates per instance

### Summary

**The key insight**: You cannot have multiple unique circuits to a single Tor daemon simultaneously. Multiple sessions to the same daemon share the same circuit/exit IP.

**The solution**: Run multiple Tor daemon instances (one per worker) using Docker Compose. Each daemon maintains its own independent circuit.

This approach provides true parallel processing with unique exit IPs, solving the original problem correctly.
