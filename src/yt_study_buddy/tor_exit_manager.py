"""
Single facade for managing Tor exit nodes across multiple Tor daemon instances.

This is the ONLY class workers interact with to get Tor connections.
Handles multi-instance detection, worker assignment, and exit IP tracking.
"""
import socket
from typing import Optional
from dataclasses import dataclass
from loguru import logger

from .tor_transcript_fetcher import TorTranscriptFetcher
from .daily_exit_tracker import get_daily_tracker


@dataclass
class TorInstance:
    """Configuration for a single Tor daemon instance."""
    instance_id: int
    socks_port: int
    control_port: int
    host: str = '127.0.0.1'


class TorExitNodeManager:
    """
    Single facade for managing Tor exit nodes.

    ARCHITECTURE:
    =============
    - Detects available Tor daemon instances (9050, 9052, 9054, 9056, 9058)
    - Assigns workers to instances (round-robin)
    - Provides TorTranscriptFetcher configured for assigned instance
    - Tracks exit IP usage in daily_exit_tracking.json

    USAGE:
    ======
    ```python
    # Initialize (auto-detects Tor instances)
    manager = TorExitNodeManager()

    # Worker gets a fetcher
    fetcher = manager.get_fetcher_for_worker(worker_id=0)

    # Use fetcher normally - it's configured for the right Tor instance
    transcript = fetcher.fetch_transcript(video_id)
    ```

    MULTI-TOR SETUP:
    ================
    Start multiple Tor instances:
        docker-compose -f docker-compose.yml -f docker-compose.parallel.yml up -d

    Each instance provides independent circuit:
        Worker 0 → Tor #1 (port 9050) → Exit IP #1
        Worker 1 → Tor #2 (port 9052) → Exit IP #2
        Worker 2 → Tor #3 (port 9054) → Exit IP #3

    This is the ONLY way to get truly unique IPs in parallel.
    A single Tor daemon = ONE circuit shared by all workers.
    """

    def __init__(
        self,
        base_socks_port: int = 9050,
        base_control_port: int = 9051,
        port_increment: int = 2,
        max_instances: int = 10,
        probe_timeout: float = 1.0
    ):
        """
        Initialize manager and auto-detect Tor instances.

        Args:
            base_socks_port: First SOCKS port to probe (default: 9050)
            base_control_port: First control port (default: 9051)
            port_increment: Port gap between instances (default: 2)
            max_instances: Max instances to probe (default: 10)
            probe_timeout: Timeout per port probe (default: 1.0s)
        """
        self.instances = self._detect_instances(
            base_socks_port,
            base_control_port,
            port_increment,
            max_instances,
            probe_timeout
        )

        # Daily exit tracking
        self.daily_tracker = get_daily_tracker()

        logger.info(f"TorExitNodeManager initialized with {len(self.instances)} instance(s)")
        for instance in self.instances:
            logger.info(f"  Tor #{instance.instance_id}: "
                       f"SOCKS {instance.socks_port}, Control {instance.control_port}")

    def _detect_instances(
        self,
        base_socks_port: int,
        base_control_port: int,
        port_increment: int,
        max_instances: int,
        timeout: float
    ) -> list[TorInstance]:
        """
        Auto-detect available Tor instances by probing SOCKS ports.

        Returns:
            List of detected TorInstance objects
        """
        logger.info("Detecting Tor instances...")

        detected = []

        for i in range(max_instances):
            instance_id = i + 1
            socks_port = base_socks_port + (i * port_increment)
            control_port = base_control_port + (i * port_increment)

            if self._is_port_open('127.0.0.1', socks_port, timeout):
                instance = TorInstance(instance_id, socks_port, control_port)
                detected.append(instance)
                logger.success(f"  ✓ Detected Tor #{instance_id} on port {socks_port}")
            else:
                # Stop after first missing instance
                break

        if not detected:
            logger.warning("  No Tor instances detected, using default (localhost:9050)")
            detected = [TorInstance(1, 9050, 9051)]

        return detected

    @staticmethod
    def _is_port_open(host: str, port: int, timeout: float) -> bool:
        """Check if a port is open and accepting connections."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def get_fetcher_for_worker(
        self,
        worker_id: int,
        tor_control_password: Optional[str] = None
    ) -> TorTranscriptFetcher:
        """
        Get a TorTranscriptFetcher configured for this worker.

        Workers are assigned to Tor instances using round-robin.
        The fetcher is pre-configured to connect to the assigned instance.

        Args:
            worker_id: Worker ID (0-based)
            tor_control_password: Optional Tor control password

        Returns:
            TorTranscriptFetcher configured for assigned Tor instance
        """
        # Assign worker to instance (round-robin)
        instance_idx = worker_id % len(self.instances)
        instance = self.instances[instance_idx]

        logger.debug(f"  Worker {worker_id} assigned to Tor #{instance.instance_id} "
                    f"(SOCKS {instance.socks_port})")

        # Create fetcher configured for this instance
        fetcher = TorTranscriptFetcher(
            tor_host=instance.host,
            tor_port=instance.socks_port,
            tor_control_port=instance.control_port,
            tor_control_password=tor_control_password
        )

        return fetcher

    def get_instance_count(self) -> int:
        """Get number of detected Tor instances."""
        return len(self.instances)

    def is_multi_instance(self) -> bool:
        """Check if multiple Tor instances are available."""
        return len(self.instances) > 1

    def get_stats(self) -> dict:
        """Get statistics about Tor instances and exit tracking."""
        tracker_stats = self.daily_tracker.get_stats()

        return {
            'tor_instances': len(self.instances),
            'multi_instance': self.is_multi_instance(),
            'instances': [
                {
                    'id': inst.instance_id,
                    'socks_port': inst.socks_port,
                    'control_port': inst.control_port
                }
                for inst in self.instances
            ],
            'daily_tracking': {
                'date': tracker_stats.get('date'),
                'total_attempts': tracker_stats.get('total_attempts', 0),
                'unique_ips_used': tracker_stats.get('unique_ips', 0),
                'successful_fetches': tracker_stats.get('successful', 0),
                'failed_fetches': tracker_stats.get('failed', 0)
            }
        }


# Example usage
if __name__ == "__main__":
    # Initialize manager (auto-detects Tor instances)
    manager = TorExitNodeManager()

    # Show stats
    stats = manager.get_stats()
    print(f"\nTor instances: {stats['tor_instances']}")
    print(f"Multi-instance mode: {stats['multi_instance']}")

    print("\nInstances:")
    for inst in stats['instances']:
        print(f"  Tor #{inst['id']}: SOCKS {inst['socks_port']}, Control {inst['control_port']}")

    print("\nDaily tracking:")
    tracking = stats['daily_tracking']
    print(f"  Date: {tracking['date']}")
    print(f"  Total attempts: {tracking['total_attempts']}")
    print(f"  Unique IPs used: {tracking['unique_ips_used']}")
    print(f"  Successful: {tracking['successful_fetches']}")
    print(f"  Failed: {tracking['failed_fetches']}")

    # Simulate worker assignment
    print("\nWorker assignments (10 workers):")
    for worker_id in range(10):
        instance_idx = worker_id % len(manager.instances)
        instance = manager.instances[instance_idx]
        print(f"  Worker {worker_id} → Tor #{instance.instance_id} (port {instance.socks_port})")
