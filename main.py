#!/usr/bin/env python3
"""
Distributed Clock Synchronization Simulator

This module simulates three major clock synchronization algorithms used in
distributed systems: Cristian's Algorithm, Berkeley Algorithm, and Network
Time Protocol (NTP). It provides a comprehensive simulation environment with
configurable parameters and detailed logging.

Author: Clock Sync Simulator
Version: 2.0.0
"""

try:
    import time
    import random
    import argparse
    import logging
    import sys
    from datetime import datetime
    from typing import List, Dict, Optional
    from enum import Enum
    from pyfiglet import Figlet
except ImportError as error:
    print(error)
    print()
    print("1. (optional) Setup a virtual environment: ")
    print("  python3 -m venv ~/Python3env/ClockSync")
    print("  source ~/Python3env/ClockSync/bin/activate")
    print()
    print("2. Install requirements:")
    print("  pip3 install --upgrade pip")
    print("  pip3 install -r requirements.txt")
    print()
    sys.exit(-1)


class View:
    """
    Renders a visual banner for the simulator using ASCII art (pyfiglet).

    The banner is printed at startup to identify the tool, showing the main
    title in 'slant' font and a subtitle in 'mini' font.
    """

    def __init__(self, title: str = 'Clock Sync'):
        """
        Initialize the view with a given title.

        Args:
            title: The main title to be displayed as ASCII art.
        """
        self.title = title

    def print_view(self) -> None:
        """
        Print the ASCII art banner with title and subtitle.
        """
        font_title = Figlet(font='slant')
        print(font_title.renderText(self.title))

        font_small = Figlet(font='mini')
        print(font_small.renderText('Simulator'))

        print("-" * 50)
        print(" Distributed Clock Synchronization Simulator")
        print(" Algorithms: Cristian | Berkeley | NTP")
        print("-" * 50)
        print()


class LogLevel(Enum):
    """Enumeration for logging levels."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR


class Clock:
    """
    Represents a clock for a process/server in a distributed system.

    Each clock has a drift rate that simulates real-world clock imperfections,
    and an offset that represents the initial time difference from a reference.

    Attributes:
        name (str): Identifier for this clock
        drift (float): Clock drift rate in seconds per second
        offset (float): Initial time offset in seconds
        start_time (float): System time when clock was initialized
    """

    def __init__(self, name: str, drift: float = 0.0, offset: Optional[float] = None):
        """
        Initialize a clock with specified parameters.

        Args:
            name: Unique identifier for this clock
            drift: Drift rate (default: 0.0, perfect clock)
            offset: Initial offset in seconds (random if None)
        """
        self.name = name
        self.drift = drift
        self.offset = offset if offset is not None else random.uniform(-5, 5)
        self.start_time = time.time()

        logging.debug(f"Clock '{name}' initialized - Drift: {drift:.6f}s/s, "
                      f"Offset: {self.offset:.4f}s")

    def get_time(self) -> float:
        """
        Get the current time of this clock including drift.

        The time is calculated as:
        t = elapsed_time + offset + (elapsed_time * drift)

        Returns:
            Current clock time in seconds
        """
        elapsed = time.time() - self.start_time
        return elapsed + self.offset + (elapsed * self.drift)

    def set_time(self, new_time: float) -> None:
        """
        Set the clock to a specific time (hard adjustment).

        Args:
            new_time: The time to set the clock to
        """
        current = time.time() - self.start_time
        old_time = self.get_time()
        self.offset = new_time - current - (current * self.drift)

        logging.debug(f"Clock '{self.name}' set from {old_time:.4f}s to {new_time:.4f}s "
                      f"(adjustment: {new_time - old_time:+.4f}s)")

    def adjust_time(self, adjustment: float) -> None:
        """
        Adjust the clock by an incremental value (soft adjustment).

        Args:
            adjustment: Time adjustment in seconds (positive or negative)
        """
        old_time = self.get_time()
        self.offset += adjustment
        new_time = self.get_time()

        logging.debug(f"Clock '{self.name}' adjusted by {adjustment:+.4f}s "
                      f"({old_time:.4f}s -> {new_time:.4f}s)")


class TimeServer:
    """
    Time server for Cristian's Algorithm and NTP.

    Represents a highly accurate time source with minimal drift,
    similar to a stratum-1 NTP server connected to an atomic clock.

    Attributes:
        clock (Clock): The server's clock instance
        name (str): Server identifier
    """

    def __init__(self, name: str = "TimeServer", drift: float = 0.0001):
        """
        Initialize a time server.

        Args:
            name: Server identifier
            drift: Minimal drift rate (default: 0.0001 for high accuracy)
        """
        self.clock = Clock(name, drift)
        self.name = name

        logging.info(f"Time server '{name}' initialized with drift {drift:.6f}s/s")

    def get_time(self) -> float:
        """
        Get the server's current time.

        Returns:
            Current server time in seconds
        """
        return self.clock.get_time()


class Client:
    """
    Client node that synchronizes its clock with a time server or other nodes.

    Represents a typical distributed system node with moderate clock drift
    that needs periodic synchronization.

    Attributes:
        clock (Clock): The client's clock instance
        name (str): Client identifier
    """

    def __init__(self, name: str, drift: float = 0.01):
        """
        Initialize a client node.

        Args:
            name: Client identifier
            drift: Clock drift rate (default: 0.01)
        """
        self.clock = Clock(name, drift)
        self.name = name

        logging.info(f"Client '{name}' initialized with drift {drift:.4f}s/s")

    def get_time(self) -> float:
        """Get the client's current time."""
        return self.clock.get_time()

    def set_time(self, new_time: float) -> None:
        """Set the client's clock to a specific time."""
        self.clock.set_time(new_time)

    def adjust_time(self, adjustment: float) -> None:
        """Adjust the client's clock by an incremental value."""
        self.clock.adjust_time(adjustment)


def simulate_network_delay(min_delay: float = 0.01, max_delay: float = 0.1) -> float:
    """
    Simulate network latency with random delay.

    Args:
        min_delay: Minimum delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Random delay value in the specified range
    """
    delay = random.uniform(min_delay, max_delay)
    logging.debug(f"Network delay: {delay:.4f}s")
    return delay


# ==================== CRISTIAN'S ALGORITHM ====================

def cristian_algorithm(server: TimeServer, client: Client,
                       network_delay_range: tuple = (0.01, 0.1)) -> Dict:
    """
    Implement Cristian's Clock Synchronization Algorithm.

    This algorithm synchronizes a client's clock with a time server by:
    1. Recording the local time before sending a request (T0)
    2. Requesting the server's time
    3. Recording the local time after receiving the response (T1)
    4. Calculating RTT (Round Trip Time) = T1 - T0
    5. Estimating actual time = server_time + RTT/2
    6. Adjusting the client's clock to the estimated time

    Reference: Cristian, F. (1989). "Probabilistic clock synchronization"

    Args:
        server: Time server to synchronize with
        client: Client node to synchronize
        network_delay_range: Tuple of (min, max) network delay in seconds

    Returns:
        Dictionary containing synchronization results and statistics
    """
    logging.info(f"{'=' * 70}")
    logging.info(f"CRISTIAN'S ALGORITHM - Client: {client.name}")
    logging.info(f"{'=' * 70}")

    # T0: Record time before request
    t0 = client.get_time()
    logging.info(f"T0 (client time before request): {t0:.4f}s")

    # FIX: use time.sleep(simulate_network_delay(...)) directly, consistent
    # with the rest of the codebase (no need to store the delay value).
    # Simulate network delay (outbound)
    time.sleep(simulate_network_delay(*network_delay_range))

    # Server provides its time
    server_time = server.get_time()
    logging.info(f"Server time: {server_time:.4f}s")

    # Simulate network delay (inbound)
    time.sleep(simulate_network_delay(*network_delay_range))

    # T1: Record time after receiving response
    t1 = client.get_time()
    logging.info(f"T1 (client time after response): {t1:.4f}s")

    # Calculate Round Trip Time and estimate current time
    rtt = t1 - t0
    estimated_time = server_time + (rtt / 2)

    logging.info(f"RTT (Round Trip Time): {rtt:.4f}s")
    logging.info(f"Estimated current time: {estimated_time:.4f}s")

    # Adjust the clock
    adjustment = estimated_time - t1
    client.set_time(estimated_time)

    logging.info(f"Clock adjustment: {adjustment:+.4f}s")
    logging.info(f"Client new time: {client.get_time():.4f}s")

    # Calculate synchronization accuracy
    final_diff = abs(server.get_time() - client.get_time())
    logging.info(f"Final time difference: {final_diff:.4f}s")

    return {
        'algorithm': 'Cristian',
        'client': client.name,
        'server': server.name,
        'rtt': rtt,
        'adjustment': adjustment,
        'final_time': client.get_time(),
        'final_diff': final_diff
    }


# ==================== BERKELEY ALGORITHM ====================

def berkeley_algorithm(master: Client, slaves: List[Client],
                       network_delay_range: tuple = (0.01, 0.1)) -> Dict:
    """
    Implement the Berkeley Clock Synchronization Algorithm.

    This algorithm achieves internal clock synchronization by:
    1. Master polls all slaves for their current time
    2. Master calculates the average time across all nodes (including itself)
    3. Master computes adjustment values for each node
    4. Master sends adjustment values to all slaves
    5. All nodes (including master) apply their adjustments

    Note: This algorithm synchronizes clocks relative to each other, not to
    an absolute time reference. The goal is agreement, not accuracy.

    Reference: Gusella, R. & Zatti, S. (1989). "The accuracy of the clock
    synchronization achieved by TEMPO in Berkeley UNIX 4.3BSD"

    Args:
        master: The master node that coordinates synchronization
        slaves: List of slave nodes to synchronize
        network_delay_range: Tuple of (min, max) network delay in seconds

    Returns:
        Dictionary containing synchronization results and statistics
    """
    logging.info(f"{'=' * 70}")
    logging.info(f"BERKELEY ALGORITHM - Master: {master.name}")
    logging.info(f"{'=' * 70}")

    # Master records its own time
    master_time = master.get_time()
    logging.info(f"Master time: {master_time:.4f}s")

    # Collect times from all slaves
    times = [master_time]
    logging.info(f"Polling slave nodes:")

    for slave in slaves:
        # Simulate network delay for time request
        time.sleep(simulate_network_delay(*network_delay_range))

        slave_time = slave.get_time()
        times.append(slave_time)
        diff = slave_time - master_time

        logging.info(f"  {slave.name}: {slave_time:.4f}s "
                     f"(difference: {diff:+.4f}s)")

    # Calculate average time across all nodes
    avg_time = sum(times) / len(times)
    logging.info(f"Calculated average time: {avg_time:.4f}s")

    # Calculate and distribute adjustments
    logging.info(f"Distributing clock adjustments:")
    adjustments = {}

    # Adjust master's clock
    master_adj = avg_time - master_time
    master.adjust_time(master_adj)
    adjustments[master.name] = master_adj
    logging.info(f"  {master.name}: {master_adj:+.4f}s -> {master.get_time():.4f}s")

    # Adjust slaves' clocks
    for i, slave in enumerate(slaves):
        # Simulate network delay for sending adjustment
        time.sleep(simulate_network_delay(*network_delay_range))

        slave_adj = avg_time - times[i + 1]
        slave.adjust_time(slave_adj)
        adjustments[slave.name] = slave_adj
        logging.info(f"  {slave.name}: {slave_adj:+.4f}s -> {slave.get_time():.4f}s")

    # Calculate synchronization quality
    all_nodes = [master] + slaves
    final_times = [node.get_time() for node in all_nodes]
    time_variance = max(final_times) - min(final_times)

    logging.info(f"Time variance after sync: {time_variance:.4f}s")

    return {
        'algorithm': 'Berkeley',
        'master': master.name,
        'num_slaves': len(slaves),
        'avg_time': avg_time,
        'adjustments': adjustments,
        'time_variance': time_variance
    }


# ==================== NETWORK TIME PROTOCOL (NTP) ====================

def ntp_algorithm(server: TimeServer, client: Client,
                  network_delay_range: tuple = (0.01, 0.1)) -> Dict:
    """
    Implement a simplified version of the Network Time Protocol (NTP).

    NTP uses four timestamps to calculate both network delay and clock offset:
    - T1: Client sends request (client time)
    - T2: Server receives request (server time)
    - T3: Server sends reply (server time)
    - T4: Client receives reply (client time)

    Calculations:
    - Network delay: δ = ((T4-T1) - (T3-T2)) / 2
    - Clock offset: θ = ((T2-T1) + (T3-T4)) / 2

    The offset represents how much the client clock differs from the server,
    and the delay represents the round-trip network latency.

    Simplification note: T3 is captured immediately after T2, so (T3-T2) ≈ 0.
    This assumes negligible server processing time, which collapses the delay
    formula to δ ≈ (T4-T1)/2 — equivalent to Cristian's RTT/2. In a real NTP
    implementation, the gap between T2 and T3 accounts for actual server
    processing time and is measured independently.

    Reference: Mills, D. L. (1991). "Internet time synchronization: the
    Network Time Protocol"

    Args:
        server: NTP time server
        client: Client node to synchronize
        network_delay_range: Tuple of (min, max) network delay in seconds

    Returns:
        Dictionary containing synchronization results and statistics
    """
    logging.info(f"{'=' * 70}")
    logging.info(f"NETWORK TIME PROTOCOL (NTP) - Client: {client.name}")
    logging.info(f"{'=' * 70}")

    # T1: Client sends request
    t1 = client.get_time()
    logging.info(f"T1 (client sends request): {t1:.4f}s")

    # Simulate outbound network delay
    time.sleep(simulate_network_delay(*network_delay_range))

    # T2: Server receives request
    t2 = server.get_time()
    logging.info(f"T2 (server receives request): {t2:.4f}s")

    # T3: Server sends reply.
    # Simplification: server processing time is assumed to be zero, so T3 is
    # captured immediately after T2 without any intermediate sleep. This means
    # (T3-T2) ≈ 0 and its contribution to the delay formula is negligible.
    t3 = server.get_time()
    logging.info(f"T3 (server sends reply): {t3:.4f}s")

    # Simulate inbound network delay
    time.sleep(simulate_network_delay(*network_delay_range))

    # T4: Client receives reply
    t4 = client.get_time()
    logging.info(f"T4 (client receives reply): {t4:.4f}s")

    # NTP calculations
    # Network delay: δ = ((T4-T1) - (T3-T2)) / 2
    delay = ((t4 - t1) - (t3 - t2)) / 2

    # Clock offset: θ = ((T2-T1) + (T3-T4)) / 2
    offset = ((t2 - t1) + (t3 - t4)) / 2

    logging.info(f"NTP Calculations:")
    logging.info(f"  Network delay (δ): {delay:.4f}s")
    logging.info(f"  Clock offset (θ): {offset:.4f}s")

    # Adjust the client's clock
    client.adjust_time(offset)

    logging.info(f"Clock adjustment applied: {offset:+.4f}s")
    logging.info(f"Client new time: {client.get_time():.4f}s")
    logging.info(f"Server current time: {server.get_time():.4f}s")

    # Calculate synchronization accuracy
    final_diff = abs(client.get_time() - server.get_time())
    logging.info(f"Final time difference: {final_diff:.4f}s")

    return {
        'algorithm': 'NTP',
        'client': client.name,
        'server': server.name,
        'delay': delay,
        'offset': offset,
        'final_diff': final_diff,
        'final_time': client.get_time()
    }


# ==================== COMMAND LINE INTERFACE ====================

def setup_logging(level: str, log_file: Optional[str] = None) -> None:
    """
    Configure logging system with specified level and optional file output.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging output
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )


def run_cristian(args) -> None:
    """Execute Cristian's algorithm with command-line arguments."""
    server = TimeServer("TimeServer", drift=args.server_drift)
    client = Client("Client1", drift=args.client_drift)

    logging.info(f"[Before Synchronization]")
    logging.info(f"Server: {server.get_time():.4f}s")
    logging.info(f"Client: {client.get_time():.4f}s")
    logging.info(f"Difference: {abs(server.get_time() - client.get_time()):.4f}s")

    result = cristian_algorithm(server, client,
                                (args.min_delay, args.max_delay))

    logging.info(f"[After Synchronization]")
    logging.info(f"Final difference: {result['final_diff']:.4f}s")


def run_berkeley(args) -> None:
    """Execute Berkeley algorithm with command-line arguments."""
    master = Client("Master", drift=args.master_drift)
    slaves = [
        Client(f"Slave{i + 1}", drift=random.uniform(0.015, 0.025))
        for i in range(args.num_slaves)
    ]

    logging.info(f"[Before Synchronization]")
    logging.info(f"Master: {master.get_time():.4f}s")
    for slave in slaves:
        logging.info(f"{slave.name}: {slave.get_time():.4f}s")

    result = berkeley_algorithm(master, slaves,
                                (args.min_delay, args.max_delay))

    logging.info(f"[After Synchronization]")
    logging.info(f"Time variance: {result['time_variance']:.4f}s")


def run_ntp(args) -> None:
    """Execute NTP algorithm with command-line arguments."""
    server = TimeServer("NTP-Server", drift=args.server_drift)
    client = Client("NTP-Client", drift=args.client_drift)

    logging.info(f"[Before Synchronization]")
    logging.info(f"Server: {server.get_time():.4f}s")
    logging.info(f"Client: {client.get_time():.4f}s")
    logging.info(f"Difference: {abs(server.get_time() - client.get_time()):.4f}s")

    result = ntp_algorithm(server, client,
                           (args.min_delay, args.max_delay))


def run_all(args) -> None:
    """Execute all synchronization algorithms sequentially."""
    logging.info(f"{'#' * 70}")
    logging.info(f"# EXECUTING ALL SYNCHRONIZATION ALGORITHMS")
    logging.info(f"{'#' * 70}\n")

    # Cristian's Algorithm
    run_cristian(args)
    time.sleep(0.5)

    # Berkeley Algorithm
    run_berkeley(args)
    time.sleep(0.5)

    # NTP
    run_ntp(args)


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure argument parser for command-line interface.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description='Distributed Clock Synchronization Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s cristian --client-drift 0.05 --log-level DEBUG
  %(prog)s berkeley --num-slaves 5 --max-delay 0.2
  %(prog)s ntp --server-drift 0.0001 --min-delay 0.02
  %(prog)s all --log-file simulation.log
        """
    )

    # Create subparsers for different algorithms
    subparsers = parser.add_subparsers(dest='algorithm', help='Algorithm to simulate')
    subparsers.required = True

    # Common arguments for all algorithms
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    parent_parser.add_argument(
        '--log-file',
        type=str,
        help='Write logs to specified file'
    )
    parent_parser.add_argument(
        '--min-delay',
        type=float,
        default=0.01,
        help='Minimum network delay in seconds (default: 0.01)'
    )
    parent_parser.add_argument(
        '--max-delay',
        type=float,
        default=0.1,
        help='Maximum network delay in seconds (default: 0.1)'
    )
    parent_parser.add_argument(
        '--server-drift',
        type=float,
        default=0.0001,
        help='Server clock drift rate (default: 0.0001)'
    )
    parent_parser.add_argument(
        '--client-drift',
        type=float,
        default=0.02,
        help='Client clock drift rate (default: 0.02)'
    )

    # Cristian's Algorithm
    parser_cristian = subparsers.add_parser(
        'cristian',
        parents=[parent_parser],
        help="Simulate Cristian's Clock Synchronization Algorithm"
    )
    parser_cristian.set_defaults(func=run_cristian)

    # Berkeley Algorithm
    parser_berkeley = subparsers.add_parser(
        'berkeley',
        parents=[parent_parser],
        help='Simulate Berkeley Clock Synchronization Algorithm'
    )
    parser_berkeley.add_argument(
        '--num-slaves',
        type=int,
        default=3,
        help='Number of slave nodes (default: 3)'
    )
    parser_berkeley.add_argument(
        '--master-drift',
        type=float,
        default=0.015,
        help='Master clock drift rate (default: 0.015)'
    )
    parser_berkeley.set_defaults(func=run_berkeley)

    # NTP
    parser_ntp = subparsers.add_parser(
        'ntp',
        parents=[parent_parser],
        help='Simulate Network Time Protocol (NTP)'
    )
    parser_ntp.set_defaults(func=run_ntp)

    # All algorithms
    parser_all = subparsers.add_parser(
        'all',
        parents=[parent_parser],
        help='Run all synchronization algorithms'
    )
    parser_all.add_argument(
        '--num-slaves',
        type=int,
        default=3,
        help='Number of slave nodes for Berkeley (default: 3)'
    )
    parser_all.add_argument(
        '--master-drift',
        type=float,
        default=0.015,
        help='Master clock drift rate for Berkeley (default: 0.015)'
    )
    parser_all.set_defaults(func=run_all)

    return parser


def main() -> None:
    """Main entry point for the clock synchronization simulator."""
    View().print_view()

    parser = create_parser()
    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level, args.log_file)

    # Execute the selected algorithm
    try:
        args.func(args)
    except KeyboardInterrupt:
        logging.info("\nSimulation interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Simulation error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
