"""
WebSocket Connection Manager for real-time updates
"""
from fastapi import WebSocket
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, case_id: str):
        """
        Accept a new WebSocket connection for a case
        """
        await websocket.accept()
        
        if case_id not in self.active_connections:
            self.active_connections[case_id] = []
        
        self.active_connections[case_id].append(websocket)
        logger.info(f"WebSocket connected for case {case_id}. Total connections: {len(self.active_connections[case_id])}")
    
    def disconnect(self, websocket: WebSocket, case_id: str):
        """
        Remove a WebSocket connection
        """
        if case_id in self.active_connections:
            if websocket in self.active_connections[case_id]:
                self.active_connections[case_id].remove(websocket)
                logger.info(f"WebSocket disconnected for case {case_id}. Remaining: {len(self.active_connections[case_id])}")
            
            # Clean up empty case entries
            if not self.active_connections[case_id]:
                del self.active_connections[case_id]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """
        Send a message to a specific WebSocket connection
        """
        await websocket.send_text(message)
    
    async def broadcast_to_case(self, case_id: str, message: dict):
        """
        Broadcast a message to all connections for a specific case
        """
        if case_id in self.active_connections:
            disconnected = []
            
            for connection in self.active_connections[case_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected sockets
            for connection in disconnected:
                self.disconnect(connection, case_id)
    
    async def broadcast_all(self, message: dict):
        """
        Broadcast a message to all active connections
        """
        for case_id in list(self.active_connections.keys()):
            await self.broadcast_to_case(case_id, message)
    
    def get_connection_count(self, case_id: str = None) -> int:
        """
        Get the number of active connections
        """
        if case_id:
            return len(self.active_connections.get(case_id, []))
        else:
            return sum(len(conns) for conns in self.active_connections.values())
