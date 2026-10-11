"""WebSocket support for real-time Q&A generation and status updates"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Set, Optional
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        # {job_id: {user_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}
        # {job_id: connection_count}
        self.job_subscriptions: Dict[str, int] = {}

    async def connect(self, job_id: str, user_id: str, websocket: WebSocket):
        """Register new connection"""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = {}
        
        self.active_connections[job_id][user_id] = websocket
        self.job_subscriptions[job_id] = self.job_subscriptions.get(job_id, 0) + 1
        
        logger.info(f"WebSocket connected: job={job_id}, user={user_id}")

    def disconnect(self, job_id: str, user_id: str):
        """Unregister connection"""
        if job_id in self.active_connections:
            self.active_connections[job_id].pop(user_id, None)
            
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
            
            self.job_subscriptions[job_id] = self.job_subscriptions.get(job_id, 1) - 1
            if self.job_subscriptions[job_id] <= 0:
                del self.job_subscriptions[job_id]
        
        logger.info(f"WebSocket disconnected: job={job_id}, user={user_id}")

    async def broadcast_progress(
        self,
        job_id: str,
        message_type: str,
        data: Dict,
        user_id: Optional[str] = None,
    ):
        """Broadcast progress update to all connected clients"""
        if job_id not in self.active_connections:
            return

        message = {
            "type": message_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
        }

        disconnected_users = []
        
        for connected_user_id, websocket in self.active_connections[job_id].items():
            # Only send to specific user if specified
            if user_id and connected_user_id != user_id:
                continue
            
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                disconnected_users.append(connected_user_id)
        
        # Clean up disconnected users
        for user_id in disconnected_users:
            self.disconnect(job_id, user_id)

    async def broadcast_job_update(
        self,
        job_id: str,
        status: str,
        progress: int = 0,
        message: str = "",
        **extra_data,
    ):
        """Broadcast job status update"""
        data = {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message,
            **extra_data,
        }
        await self.broadcast_progress(job_id, "job_update", data)

    async def broadcast_question_generated(
        self,
        job_id: str,
        question_number: int,
        question: str,
        answer: str,
        confidence: float,
        difficulty: str,
    ):
        """Broadcast Q&A pair as it's generated"""
        data = {
            "job_id": job_id,
            "question_number": question_number,
            "question": question,
            "answer": answer,
            "confidence": confidence,
            "difficulty": difficulty,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_progress(job_id, "question_generated", data)

    async def send_error(self, job_id: str, error_message: str, user_id: Optional[str] = None):
        """Send error message"""
        data = {
            "job_id": job_id,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_progress(job_id, "error", data, user_id)

    def get_active_connections_count(self, job_id: str) -> int:
        """Get number of active connections for job"""
        return len(self.active_connections.get(job_id, {}))

    def get_total_connections(self) -> int:
        """Get total active connections"""
        total = 0
        for users in self.active_connections.values():
            total += len(users)
        return total


# Global connection manager
connection_manager = ConnectionManager()


async def get_connection_manager() -> ConnectionManager:
    """Get connection manager instance"""
    return connection_manager
