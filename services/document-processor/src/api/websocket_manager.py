"""
WebSocket manager for real-time job updates.

Provides:
- WebSocket connection management
- Real-time job progress broadcasting
- Client subscription handling
"""

import asyncio
import json
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
import redis

from ..jobs import JobManager, JobStatus
from ..api.schemas import WebSocketMessage


class ConnectionManager:
    """
    Manage WebSocket connections for job updates.

    Features:
    - Multiple clients per job
    - Automatic cleanup on disconnect
    - Broadcast to all subscribers
    """

    def __init__(self):
        """Initialize connection manager."""
        # Map of job_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Map of WebSocket -> job_id for cleanup
        self.connection_jobs: Dict[WebSocket, str] = {}

    async def connect(self, websocket: WebSocket, job_id: str):
        """
        Accept WebSocket connection and subscribe to job.

        Args:
            websocket: WebSocket connection
            job_id: Job to subscribe to
        """
        await websocket.accept()

        # Add to job subscribers
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()

        self.active_connections[job_id].add(websocket)
        self.connection_jobs[websocket] = job_id

    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket connection
        """
        # Get job_id
        job_id = self.connection_jobs.get(websocket)

        if job_id:
            # Remove from job subscribers
            if job_id in self.active_connections:
                self.active_connections[job_id].discard(websocket)

                # Clean up empty job sets
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

            # Remove from connection map
            del self.connection_jobs[websocket]

    async def send_message(
        self,
        job_id: str,
        message: WebSocketMessage
    ):
        """
        Send message to all subscribers of a job.

        Args:
            job_id: Job ID
            message: Message to send
        """
        if job_id not in self.active_connections:
            return

        # Convert message to JSON
        message_json = json.dumps({
            "type": message.type,
            "job_id": message.job_id,
            "data": message.data,
            "timestamp": message.timestamp.isoformat(),
        })

        # Send to all subscribers
        disconnected = []
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_text(message_json)
            except Exception:
                # Mark for removal
                disconnected.append(websocket)

        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)

    async def broadcast_status(
        self,
        job_id: str,
        status: str,
        data: Optional[Dict] = None
    ):
        """
        Broadcast job status update.

        Args:
            job_id: Job ID
            status: Job status
            data: Additional data
        """
        message = WebSocketMessage(
            type="status",
            job_id=job_id,
            data={
                "status": status,
                **(data or {})
            }
        )

        await self.send_message(job_id, message)

    async def broadcast_progress(
        self,
        job_id: str,
        current: int,
        total: int,
        message: str
    ):
        """
        Broadcast job progress update.

        Args:
            job_id: Job ID
            current: Current step
            total: Total steps
            message: Progress message
        """
        msg = WebSocketMessage(
            type="progress",
            job_id=job_id,
            data={
                "current": current,
                "total": total,
                "percentage": (current / total) * 100 if total > 0 else 0,
                "message": message,
            }
        )

        await self.send_message(job_id, msg)

    async def broadcast_result(
        self,
        job_id: str,
        result: Dict
    ):
        """
        Broadcast job result.

        Args:
            job_id: Job ID
            result: Job result
        """
        message = WebSocketMessage(
            type="result",
            job_id=job_id,
            data=result
        )

        await self.send_message(job_id, message)

    async def broadcast_error(
        self,
        job_id: str,
        error: str
    ):
        """
        Broadcast job error.

        Args:
            job_id: Job ID
            error: Error message
        """
        message = WebSocketMessage(
            type="error",
            job_id=job_id,
            data={"error": error}
        )

        await self.send_message(job_id, message)


# Global connection manager
connection_manager = ConnectionManager()


class JobMonitor:
    """
    Monitor job progress and broadcast updates via WebSocket.

    Features:
    - Poll job status from Redis
    - Detect status changes
    - Broadcast updates to subscribers
    """

    def __init__(
        self,
        job_manager: JobManager,
        connection_manager: ConnectionManager,
        poll_interval: float = 1.0,
    ):
        """
        Initialize job monitor.

        Args:
            job_manager: JobManager instance
            connection_manager: ConnectionManager instance
            poll_interval: Polling interval in seconds
        """
        self.job_manager = job_manager
        self.connection_manager = connection_manager
        self.poll_interval = poll_interval

        # Track last known status
        self.last_status: Dict[str, JobStatus] = {}

        # Monitoring task
        self.monitor_task: Optional[asyncio.Task] = None

    async def start_monitoring(self, job_id: str):
        """
        Start monitoring a job.

        Args:
            job_id: Job to monitor
        """
        # Create monitoring task
        task = asyncio.create_task(self._monitor_job(job_id))
        self.monitor_task = task

    async def _monitor_job(self, job_id: str):
        """
        Monitor job and broadcast updates.

        Args:
            job_id: Job to monitor
        """
        try:
            while True:
                # Get current status
                try:
                    job_result = self.job_manager.get_job_status(job_id)
                except Exception:
                    # Job not found or error
                    await asyncio.sleep(self.poll_interval)
                    continue

                # Check for status change
                last_status = self.last_status.get(job_id)

                if last_status != job_result.status:
                    # Status changed, broadcast update
                    await self.connection_manager.broadcast_status(
                        job_id=job_id,
                        status=job_result.status.value,
                        data={
                            "progress": job_result.progress * 100,
                        }
                    )

                    # Update last status
                    self.last_status[job_id] = job_result.status

                    # If completed or failed, broadcast result/error
                    if job_result.status == JobStatus.SUCCESS:
                        if job_result.result:
                            await self.connection_manager.broadcast_result(
                                job_id=job_id,
                                result=job_result.result
                            )

                    elif job_result.status == JobStatus.FAILURE:
                        if job_result.error:
                            await self.connection_manager.broadcast_error(
                                job_id=job_id,
                                error=job_result.error
                            )

                    # Stop monitoring if terminal state
                    if job_result.status in [JobStatus.SUCCESS, JobStatus.FAILURE, JobStatus.REVOKED]:
                        break

                # Wait before next poll
                await asyncio.sleep(self.poll_interval)

        except asyncio.CancelledError:
            # Task cancelled, stop monitoring
            pass

        except Exception as e:
            # Error in monitoring, broadcast error
            await self.connection_manager.broadcast_error(
                job_id=job_id,
                error=f"Monitoring error: {str(e)}"
            )

    def stop_monitoring(self):
        """Stop monitoring."""
        if self.monitor_task:
            self.monitor_task.cancel()
            self.monitor_task = None
