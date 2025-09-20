#!/usr/bin/env python3
"""
LM Studio Connection Pool System
Task A1.5.1: Connection Pool Architecture

Persistent connection pool system for LM Studio with:
- 2-3 active connections maintained
- Connection health monitoring with heartbeat checks
- Automatic reconnection on failures with exponential backoff
- Connection reuse and lifecycle management
- Request queuing when all connections are busy
- Graceful degradation when LM Studio is unavailable
- Integration with SecurityEthicsFoundation

Optimizes performance by eliminating connection overhead and providing resilient communication.
"""

import asyncio
import aiohttp
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
from queue import Queue, Empty
import concurrent.futures
import statistics

try:
    from security_ethics_foundation import SecurityEthicsFoundation, EthicalBoundary
except ImportError:
    print("Warning: SecurityEthicsFoundation not available - running in standalone mode")


class ConnectionState(Enum):
    """Connection state enumeration"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


class RequestPriority(Enum):
    """Request priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    connection_id: str
    created_at: datetime
    last_used: datetime
    requests_handled: int
    average_response_time: float
    current_latency: float
    failures: int
    consecutive_failures: int
    total_uptime: float
    health_score: float


@dataclass
class PooledConnection:
    """Pooled connection wrapper"""
    connection_id: str
    session: aiohttp.ClientSession
    state: ConnectionState
    created_at: datetime
    last_used: datetime
    last_health_check: datetime
    health_failures: int
    is_busy: bool
    current_request_id: Optional[str]
    metrics: ConnectionMetrics


@dataclass
class QueuedRequest:
    """Queued request structure"""
    request_id: str
    url: str
    method: str
    data: Optional[Dict[str, Any]]
    headers: Optional[Dict[str, str]]
    priority: RequestPriority
    timeout: float
    queued_at: datetime
    max_retries: int
    callback: Optional[Callable]
    context: Dict[str, Any]


@dataclass
class RequestResult:
    """Request execution result"""
    request_id: str
    success: bool
    response_data: Optional[Dict[str, Any]]
    status_code: Optional[int]
    error_message: Optional[str]
    execution_time: float
    connection_id: Optional[str]
    retries_used: int


class LMStudioConnectionPool:
    """
    High-performance connection pool for LM Studio with health monitoring,
    automatic failover, and request queuing
    """

    def __init__(self,
                 lm_studio_host: str = "localhost",
                 lm_studio_port: int = 1234,
                 pool_size: int = 3,
                 max_queue_size: int = 100,
                 request_timeout: float = 30.0,
                 health_check_interval: float = 5.0,
                 connection_timeout: float = 10.0,
                 security_foundation: Optional[SecurityEthicsFoundation] = None):

        # Connection configuration
        self.lm_studio_host = lm_studio_host
        self.lm_studio_port = lm_studio_port
        self.base_url = f"http://{lm_studio_host}:{lm_studio_port}"
        self.pool_size = pool_size
        self.max_queue_size = max_queue_size
        self.request_timeout = request_timeout
        self.health_check_interval = health_check_interval
        self.connection_timeout = connection_timeout

        # Security integration
        self.security_foundation = security_foundation

        # Connection pool
        self.connections: Dict[str, PooledConnection] = {}
        self.connection_lock = threading.RLock()

        # Request queue
        self.request_queue = Queue(maxsize=max_queue_size)
        self.pending_requests: Dict[str, QueuedRequest] = {}

        # Health monitoring
        self.is_running = False
        self.health_monitor_thread = None
        self.request_processor_thread = None

        # Performance tracking
        self.pool_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "queue_overflows": 0,
            "average_queue_time": 0.0,
            "average_response_time": 0.0,
            "lm_studio_available": False,
            "last_availability_check": None
        }

        # Response time tracking
        self.response_times = []
        self.max_response_time_samples = 100

        # Event loop for async operations
        self.loop = None
        self.loop_thread = None

        # Retry configuration
        self.retry_config = {
            "initial_delay": 1.0,
            "max_delay": 30.0,
            "exponential_base": 2.0,
            "max_retries": 3
        }

        self.logger = logging.getLogger("lm_studio_pool")
        self.logger.info(f"LM Studio Connection Pool initialized for {self.base_url}")

    def start(self) -> bool:
        """Start the connection pool"""
        if self.is_running:
            self.logger.warning("Connection pool already running")
            return True

        try:
            self.is_running = True

            # Start event loop in separate thread
            self._start_event_loop()

            # Initialize connections
            self._initialize_connection_pool()

            # Start monitoring threads
            self._start_health_monitor()
            self._start_request_processor()

            self.logger.info("LM Studio Connection Pool started successfully")

            # Log security event if security foundation available
            if self.security_foundation:
                self._log_security_event("connection_pool_started", "INFO",
                                        "LM Studio connection pool started")

            return True

        except Exception as e:
            self.logger.error(f"Failed to start connection pool: {e}")
            self.is_running = False
            return False

    def stop(self) -> None:
        """Stop the connection pool gracefully"""
        if not self.is_running:
            return

        self.logger.info("Stopping LM Studio Connection Pool...")
        self.is_running = False

        try:
            # Close all connections
            self._close_all_connections()

            # Stop threads
            if self.health_monitor_thread:
                self.health_monitor_thread.join(timeout=5.0)

            if self.request_processor_thread:
                self.request_processor_thread.join(timeout=5.0)

            # Stop event loop
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)

            if self.loop_thread:
                self.loop_thread.join(timeout=5.0)

            # Log security event
            if self.security_foundation:
                self._log_security_event("connection_pool_stopped", "INFO",
                                        "LM Studio connection pool stopped")

            self.logger.info("LM Studio Connection Pool stopped")

        except Exception as e:
            self.logger.error(f"Error stopping connection pool: {e}")

    def _start_event_loop(self):
        """Start asyncio event loop in separate thread"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        self.loop_thread = threading.Thread(target=run_loop, daemon=True, name="LMStudioEventLoop")
        self.loop_thread.start()

        # Wait for loop to be ready
        while self.loop is None:
            time.sleep(0.1)

    def _initialize_connection_pool(self):
        """Initialize the connection pool with configured number of connections"""
        self.logger.info(f"Initializing {self.pool_size} connections to LM Studio")

        for i in range(self.pool_size):
            connection_id = f"lm_conn_{i}_{uuid.uuid4().hex[:8]}"

            try:
                # Create connection asynchronously
                future = asyncio.run_coroutine_threadsafe(
                    self._create_connection(connection_id), self.loop
                )

                connection = future.result(timeout=self.connection_timeout)

                if connection:
                    with self.connection_lock:
                        self.connections[connection_id] = connection
                    self.logger.info(f"Connection {connection_id} initialized successfully")
                else:
                    self.logger.warning(f"Failed to initialize connection {connection_id}")

            except Exception as e:
                self.logger.error(f"Error initializing connection {connection_id}: {e}")

        active_connections = len([c for c in self.connections.values() if c.state == ConnectionState.HEALTHY])
        self.logger.info(f"Connection pool initialized with {active_connections}/{self.pool_size} healthy connections")

    async def _create_connection(self, connection_id: str) -> Optional[PooledConnection]:
        """Create a new pooled connection"""
        try:
            # Create aiohttp session with optimized settings
            connector = aiohttp.TCPConnector(
                limit=1,  # One connection per session
                limit_per_host=1,
                keepalive_timeout=300,  # 5 minutes
                enable_cleanup_closed=True
            )

            timeout = aiohttp.ClientTimeout(
                total=self.connection_timeout,
                connect=self.connection_timeout / 2
            )

            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "Penny-AI-Assistant/1.0"}
            )

            # Test connection health
            health_ok = await self._test_connection_health(session)

            now = datetime.now()
            state = ConnectionState.HEALTHY if health_ok else ConnectionState.UNHEALTHY

            # Create metrics
            metrics = ConnectionMetrics(
                connection_id=connection_id,
                created_at=now,
                last_used=now,
                requests_handled=0,
                average_response_time=0.0,
                current_latency=0.0,
                failures=0,
                consecutive_failures=0 if health_ok else 1,
                total_uptime=0.0,
                health_score=1.0 if health_ok else 0.0
            )

            # Create pooled connection
            connection = PooledConnection(
                connection_id=connection_id,
                session=session,
                state=state,
                created_at=now,
                last_used=now,
                last_health_check=now,
                health_failures=0 if health_ok else 1,
                is_busy=False,
                current_request_id=None,
                metrics=metrics
            )

            return connection

        except Exception as e:
            self.logger.error(f"Failed to create connection {connection_id}: {e}")
            return None

    async def _test_connection_health(self, session: aiohttp.ClientSession) -> bool:
        """Test connection health with LM Studio"""
        try:
            # Try to get LM Studio health/models endpoint
            health_endpoints = [
                f"{self.base_url}/v1/models",
                f"{self.base_url}/health",
                f"{self.base_url}/v1/health",
                f"{self.base_url}/"
            ]

            for endpoint in health_endpoints:
                try:
                    async with session.get(endpoint, timeout=aiohttp.ClientTimeout(total=5.0)) as response:
                        if response.status in [200, 404]:  # 404 is OK if endpoint doesn't exist
                            self.pool_metrics["lm_studio_available"] = True
                            self.pool_metrics["last_availability_check"] = datetime.now()
                            return True
                except:
                    continue

            self.pool_metrics["lm_studio_available"] = False
            return False

        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            self.pool_metrics["lm_studio_available"] = False
            return False

    def _start_health_monitor(self):
        """Start health monitoring thread"""
        def health_monitor():
            while self.is_running:
                try:
                    self._perform_health_checks()
                    time.sleep(self.health_check_interval)
                except Exception as e:
                    self.logger.error(f"Health monitor error: {e}")
                    time.sleep(self.health_check_interval)

        self.health_monitor_thread = threading.Thread(
            target=health_monitor, daemon=True, name="LMStudioHealthMonitor"
        )
        self.health_monitor_thread.start()

    def _start_request_processor(self):
        """Start request processing thread"""
        def request_processor():
            while self.is_running:
                try:
                    self._process_queued_requests()
                    time.sleep(0.1)  # Small delay to prevent busy waiting
                except Exception as e:
                    self.logger.error(f"Request processor error: {e}")
                    time.sleep(1.0)

        self.request_processor_thread = threading.Thread(
            target=request_processor, daemon=True, name="LMStudioRequestProcessor"
        )
        self.request_processor_thread.start()

    def _perform_health_checks(self):
        """Perform health checks on all connections"""
        with self.connection_lock:
            connections_to_check = list(self.connections.values())

        for connection in connections_to_check:
            if not self.is_running:
                break

            try:
                # Skip busy connections
                if connection.is_busy:
                    continue

                # Check if health check is due
                time_since_check = (datetime.now() - connection.last_health_check).total_seconds()
                if time_since_check < self.health_check_interval:
                    continue

                # Perform health check asynchronously
                future = asyncio.run_coroutine_threadsafe(
                    self._check_connection_health(connection), self.loop
                )

                # Don't block too long on health checks
                future.result(timeout=5.0)

            except Exception as e:
                self.logger.error(f"Health check failed for {connection.connection_id}: {e}")
                self._mark_connection_unhealthy(connection)

    async def _check_connection_health(self, connection: PooledConnection):
        """Check health of a specific connection"""
        try:
            start_time = time.time()
            health_ok = await self._test_connection_health(connection.session)
            latency = (time.time() - start_time) * 1000  # Convert to ms

            connection.last_health_check = datetime.now()
            connection.metrics.current_latency = latency

            if health_ok:
                connection.state = ConnectionState.HEALTHY
                connection.health_failures = 0
                connection.metrics.consecutive_failures = 0
                connection.metrics.health_score = min(1.0, connection.metrics.health_score + 0.1)
            else:
                self._mark_connection_unhealthy(connection)

        except Exception as e:
            self.logger.warning(f"Health check error for {connection.connection_id}: {e}")
            self._mark_connection_unhealthy(connection)

    def _mark_connection_unhealthy(self, connection: PooledConnection):
        """Mark connection as unhealthy and schedule reconnection if needed"""
        connection.state = ConnectionState.UNHEALTHY
        connection.health_failures += 1
        connection.metrics.failures += 1
        connection.metrics.consecutive_failures += 1
        connection.metrics.health_score = max(0.0, connection.metrics.health_score - 0.2)

        # If too many failures, attempt reconnection
        if connection.health_failures >= 3:
            self.logger.warning(f"Connection {connection.connection_id} marked for reconnection")
            self._schedule_reconnection(connection)

    def _schedule_reconnection(self, connection: PooledConnection):
        """Schedule connection reconnection with exponential backoff"""
        def reconnect():
            try:
                delay = min(
                    self.retry_config["initial_delay"] *
                    (self.retry_config["exponential_base"] ** (connection.health_failures - 1)),
                    self.retry_config["max_delay"]
                )

                time.sleep(delay)

                if not self.is_running:
                    return

                # Attempt reconnection
                future = asyncio.run_coroutine_threadsafe(
                    self._reconnect_connection(connection), self.loop
                )

                future.result(timeout=self.connection_timeout)

            except Exception as e:
                self.logger.error(f"Reconnection failed for {connection.connection_id}: {e}")

        reconnect_thread = threading.Thread(
            target=reconnect, daemon=True,
            name=f"LMStudioReconnect-{connection.connection_id}"
        )
        reconnect_thread.start()

    async def _reconnect_connection(self, connection: PooledConnection):
        """Reconnect a failed connection"""
        try:
            connection.state = ConnectionState.RECONNECTING

            # Close old session
            if connection.session and not connection.session.closed:
                await connection.session.close()

            # Create new connection
            new_connection = await self._create_connection(connection.connection_id)

            if new_connection:
                # Update existing connection object
                connection.session = new_connection.session
                connection.state = new_connection.state
                connection.health_failures = 0
                connection.last_health_check = datetime.now()

                self.logger.info(f"Successfully reconnected {connection.connection_id}")

                # Log security event
                if self.security_foundation:
                    self._log_security_event("connection_reconnected", "INFO",
                                            f"Connection {connection.connection_id} reconnected")
            else:
                connection.state = ConnectionState.FAILED

        except Exception as e:
            self.logger.error(f"Reconnection error for {connection.connection_id}: {e}")
            connection.state = ConnectionState.FAILED

    def _process_queued_requests(self):
        """Process requests from the queue"""
        try:
            # Get request from queue (non-blocking)
            try:
                queued_request = self.request_queue.get_nowait()
            except Empty:
                return

            # Check if request has timed out
            if self._is_request_expired(queued_request):
                self.logger.warning(f"Request {queued_request.request_id} expired in queue")
                self._complete_request(queued_request.request_id, RequestResult(
                    request_id=queued_request.request_id,
                    success=False,
                    response_data=None,
                    status_code=None,
                    error_message="Request expired in queue",
                    execution_time=0.0,
                    connection_id=None,
                    retries_used=0
                ))
                return

            # Find available connection
            connection = self._get_available_connection()
            if not connection:
                # No connections available, requeue the request
                if self.request_queue.qsize() < self.max_queue_size:
                    self.request_queue.put(queued_request)
                else:
                    self.logger.error(f"Queue overflow, dropping request {queued_request.request_id}")
                    self.pool_metrics["queue_overflows"] += 1
                return

            # Execute request
            self._execute_request_async(queued_request, connection)

        except Exception as e:
            self.logger.error(f"Error processing queued requests: {e}")

    def _get_available_connection(self) -> Optional[PooledConnection]:
        """Get an available healthy connection"""
        with self.connection_lock:
            # Find healthy, non-busy connections
            available = [
                conn for conn in self.connections.values()
                if conn.state == ConnectionState.HEALTHY and not conn.is_busy
            ]

            if available:
                # Sort by health score and last used time
                available.sort(key=lambda c: (c.metrics.health_score, -c.last_used.timestamp()), reverse=True)
                return available[0]

            return None

    def _execute_request_async(self, queued_request: QueuedRequest, connection: PooledConnection):
        """Execute request asynchronously"""
        def execute():
            try:
                # Mark connection as busy
                connection.is_busy = True
                connection.current_request_id = queued_request.request_id

                # Execute request
                future = asyncio.run_coroutine_threadsafe(
                    self._execute_request(queued_request, connection), self.loop
                )

                result = future.result(timeout=queued_request.timeout)

                # Complete request
                self._complete_request(queued_request.request_id, result)

            except Exception as e:
                self.logger.error(f"Request execution error: {e}")

                # Handle retry logic
                if queued_request.max_retries > 0:
                    queued_request.max_retries -= 1
                    self.logger.info(f"Retrying request {queued_request.request_id} ({queued_request.max_retries} retries left)")

                    if self.request_queue.qsize() < self.max_queue_size:
                        self.request_queue.put(queued_request)
                    else:
                        self._complete_request(queued_request.request_id, RequestResult(
                            request_id=queued_request.request_id,
                            success=False,
                            response_data=None,
                            status_code=None,
                            error_message="Queue overflow on retry",
                            execution_time=0.0,
                            connection_id=connection.connection_id,
                            retries_used=0
                        ))
                else:
                    self._complete_request(queued_request.request_id, RequestResult(
                        request_id=queued_request.request_id,
                        success=False,
                        response_data=None,
                        status_code=None,
                        error_message=str(e),
                        execution_time=0.0,
                        connection_id=connection.connection_id,
                        retries_used=0
                    ))

            finally:
                # Mark connection as not busy
                connection.is_busy = False
                connection.current_request_id = None
                connection.last_used = datetime.now()

        # Execute in separate thread to avoid blocking
        executor_thread = threading.Thread(target=execute, daemon=True)
        executor_thread.start()

    async def _execute_request(self, queued_request: QueuedRequest, connection: PooledConnection) -> RequestResult:
        """Execute HTTP request using the connection"""
        start_time = time.time()

        try:
            # Prepare request
            kwargs = {
                'timeout': aiohttp.ClientTimeout(total=queued_request.timeout)
            }

            if queued_request.data:
                kwargs['json'] = queued_request.data

            if queued_request.headers:
                kwargs['headers'] = queued_request.headers

            # Execute request
            async with connection.session.request(
                queued_request.method,
                queued_request.url,
                **kwargs
            ) as response:

                execution_time = (time.time() - start_time) * 1000  # Convert to ms

                # Read response
                try:
                    response_data = await response.json()
                except:
                    response_data = {"text": await response.text()}

                # Update metrics
                connection.metrics.requests_handled += 1
                connection.metrics.last_used = datetime.now()

                # Track response time
                self.response_times.append(execution_time)
                if len(self.response_times) > self.max_response_time_samples:
                    self.response_times.pop(0)

                # Update average response time
                if self.response_times:
                    self.pool_metrics["average_response_time"] = statistics.mean(self.response_times)

                # Update connection metrics
                if connection.metrics.requests_handled == 1:
                    connection.metrics.average_response_time = execution_time
                else:
                    # Running average
                    connection.metrics.average_response_time = (
                        (connection.metrics.average_response_time * (connection.metrics.requests_handled - 1) + execution_time) /
                        connection.metrics.requests_handled
                    )

                success = response.status < 400

                if success:
                    self.pool_metrics["successful_requests"] += 1
                else:
                    self.pool_metrics["failed_requests"] += 1
                    connection.metrics.failures += 1

                self.pool_metrics["total_requests"] += 1

                return RequestResult(
                    request_id=queued_request.request_id,
                    success=success,
                    response_data=response_data,
                    status_code=response.status,
                    error_message=None if success else f"HTTP {response.status}",
                    execution_time=execution_time,
                    connection_id=connection.connection_id,
                    retries_used=0
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000

            # Update failure metrics
            connection.metrics.failures += 1
            self.pool_metrics["failed_requests"] += 1
            self.pool_metrics["total_requests"] += 1

            return RequestResult(
                request_id=queued_request.request_id,
                success=False,
                response_data=None,
                status_code=None,
                error_message=str(e),
                execution_time=execution_time,
                connection_id=connection.connection_id,
                retries_used=0
            )

    def _complete_request(self, request_id: str, result: RequestResult):
        """Complete a request and notify callback if provided"""
        if request_id in self.pending_requests:
            queued_request = self.pending_requests.pop(request_id)

            # Calculate queue time
            queue_time = (datetime.now() - queued_request.queued_at).total_seconds() * 1000

            # Update average queue time
            if self.pool_metrics["total_requests"] > 0:
                total_queue_time = self.pool_metrics["average_queue_time"] * (self.pool_metrics["total_requests"] - 1)
                self.pool_metrics["average_queue_time"] = (total_queue_time + queue_time) / self.pool_metrics["total_requests"]

            # Call callback if provided
            if queued_request.callback:
                try:
                    queued_request.callback(result)
                except Exception as e:
                    self.logger.error(f"Callback error for request {request_id}: {e}")

    def _is_request_expired(self, queued_request: QueuedRequest) -> bool:
        """Check if a queued request has expired"""
        queue_time = (datetime.now() - queued_request.queued_at).total_seconds()
        return queue_time > queued_request.timeout

    def _close_all_connections(self):
        """Close all connections gracefully"""
        with self.connection_lock:
            for connection in self.connections.values():
                try:
                    if connection.session and not connection.session.closed:
                        # Close session asynchronously
                        future = asyncio.run_coroutine_threadsafe(
                            connection.session.close(), self.loop
                        )
                        future.result(timeout=5.0)
                except Exception as e:
                    self.logger.error(f"Error closing connection {connection.connection_id}: {e}")

            self.connections.clear()

    def _log_security_event(self, event_type: str, severity: str, description: str):
        """Log security event if security foundation is available"""
        if self.security_foundation:
            try:
                # This would integrate with the SecurityEthicsFoundation logging
                # For now, just log normally
                self.logger.info(f"Security Event [{event_type}] {severity}: {description}")
            except Exception as e:
                self.logger.error(f"Failed to log security event: {e}")

    # Public API methods

    def submit_request(self,
                      url: str,
                      method: str = "POST",
                      data: Optional[Dict[str, Any]] = None,
                      headers: Optional[Dict[str, str]] = None,
                      priority: RequestPriority = RequestPriority.NORMAL,
                      timeout: float = None,
                      max_retries: int = None,
                      callback: Optional[Callable] = None,
                      context: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a request to the pool queue
        Returns: request_id for tracking
        """
        if not self.is_running:
            raise RuntimeError("Connection pool is not running")

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Use defaults if not specified
        if timeout is None:
            timeout = self.request_timeout
        if max_retries is None:
            max_retries = self.retry_config["max_retries"]

        # Create queued request
        queued_request = QueuedRequest(
            request_id=request_id,
            url=url,
            method=method.upper(),
            data=data,
            headers=headers,
            priority=priority,
            timeout=timeout,
            queued_at=datetime.now(),
            max_retries=max_retries,
            callback=callback,
            context=context or {}
        )

        # Check queue capacity
        if self.request_queue.qsize() >= self.max_queue_size:
            self.pool_metrics["queue_overflows"] += 1
            raise RuntimeError("Request queue is full")

        # Add to pending requests and queue
        self.pending_requests[request_id] = queued_request
        self.request_queue.put(queued_request)

        return request_id

    def get_pool_status(self) -> Dict[str, Any]:
        """Get current pool status and metrics"""
        with self.connection_lock:
            connection_stats = {}
            for conn_id, conn in self.connections.items():
                connection_stats[conn_id] = {
                    "state": conn.state.value,
                    "is_busy": conn.is_busy,
                    "health_score": conn.metrics.health_score,
                    "requests_handled": conn.metrics.requests_handled,
                    "average_response_time": conn.metrics.average_response_time,
                    "failures": conn.metrics.failures
                }

        return {
            "is_running": self.is_running,
            "pool_size": len(self.connections),
            "healthy_connections": len([c for c in self.connections.values() if c.state == ConnectionState.HEALTHY]),
            "busy_connections": len([c for c in self.connections.values() if c.is_busy]),
            "queue_size": self.request_queue.qsize(),
            "pending_requests": len(self.pending_requests),
            "pool_metrics": self.pool_metrics.copy(),
            "connection_details": connection_stats,
            "lm_studio_base_url": self.base_url
        }

    def wait_for_lm_studio(self, timeout: float = 60.0, check_interval: float = 5.0) -> bool:
        """
        Wait for LM Studio to become available
        Returns: True if LM Studio is available, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            if self.pool_metrics["lm_studio_available"]:
                return True

            time.sleep(check_interval)

        return False


def test_lm_studio_connection_pool():
    """Test the LM Studio connection pool"""
    print("Testing LM Studio Connection Pool...")

    # Create connection pool
    pool = LMStudioConnectionPool(
        lm_studio_host="localhost",
        lm_studio_port=1234,
        pool_size=2,
        max_queue_size=50
    )

    try:
        # Start pool
        print("Starting connection pool...")
        if not pool.start():
            print("❌ Failed to start connection pool")
            return

        # Wait a moment for initialization
        time.sleep(2)

        # Check status
        status = pool.get_pool_status()
        print(f"Pool status: {status['healthy_connections']}/{status['pool_size']} healthy connections")
        print(f"LM Studio available: {status['pool_metrics']['lm_studio_available']}")

        # Test request submission (will fail if LM Studio not running, but that's OK for testing)
        def request_callback(result: RequestResult):
            print(f"Request {result.request_id} completed: success={result.success}")

        print("Submitting test request...")
        request_id = pool.submit_request(
            url=f"{pool.base_url}/v1/chat/completions",
            method="POST",
            data={
                "model": "test",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50
            },
            callback=request_callback
        )

        print(f"Request submitted with ID: {request_id}")

        # Wait for request processing
        time.sleep(3)

        # Final status
        final_status = pool.get_pool_status()
        print(f"Final metrics: {final_status['pool_metrics']['total_requests']} total requests")

        print("✅ Connection pool test completed")

    finally:
        # Stop pool
        print("Stopping connection pool...")
        pool.stop()


if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    test_lm_studio_connection_pool()