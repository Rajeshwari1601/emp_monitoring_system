from typing import Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, status, Depends
from jose import jwt, JWTError
from app.core.config import settings
from app.core.redis import get_async_redis
from app.api.deps import get_db
from app.models.user import User
from sqlalchemy.orm import Session
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps user_id -> WebSocket (The client streamer)
        self.active_streams: Dict[str, WebSocket] = {}
        # Maps target_user_id -> List[WebSocket] (Admins watching this user)
        self.admin_viewers: Dict[str, List[WebSocket]] = {}

    async def connect_streamer(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        # Close existing connection if any (1-to-1 mapping enforcement)
        if user_id in self.active_streams:
            try:
                await self.active_streams[user_id].close(code=status.WS_1000_NORMAL_CLOSURE)
            except:
                pass
        self.active_streams[user_id] = websocket
        logger.info(f"Streamer connected: {user_id}")

    def disconnect_streamer(self, user_id: str):
        if user_id in self.active_streams:
            del self.active_streams[user_id]
        logger.info(f"Streamer disconnected: {user_id}")
        
    async def connect_admin(self, websocket: WebSocket, target_user_id: str):
        if target_user_id not in self.admin_viewers:
            self.admin_viewers[target_user_id] = []
        self.admin_viewers[target_user_id].append(websocket)
        logger.info(f"Admin connected to watch: {target_user_id}")

    def disconnect_admin(self, websocket: WebSocket, target_user_id: str):
        if target_user_id in self.admin_viewers:
            if websocket in self.admin_viewers[target_user_id]:
                self.admin_viewers[target_user_id].remove(websocket)
        logger.info(f"Admin disconnected from watching: {target_user_id}")

manager = ConnectionManager()

def get_user_from_token(token: str, db: Session) -> Optional[User]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            return None
        return db.query(User).filter(User.id == user_id).first()
    except JWTError:
        return None

@router.websocket("/live")
async def websocket_stream_endpoint(
    websocket: WebSocket, 
    token: str = Query(...)
):
    """
    Client Streamer Endpoint.
    URL: ws://HOST/api/v1/ws/live?token=XYZ
    """
    logger.info("New Streamer connection attempt to /live")
    db = next(get_db())
    try:
        user = get_user_from_token(token, db)
    finally:
        db.close()
    
    if not user:
        logger.warning(f"Streamer token invalid or expired. Closing connection.")
        await websocket.accept()
        await websocket.close(code=4001) 
        return

    user_id = user.id
    logger.info(f"Streamer token valid for user {user_id}. Accepting...")
    await manager.connect_streamer(websocket, user_id)
    
    redis = get_async_redis()
    channel = f"live_stream:{user_id}"
    
    try:
        while True:
            data = await websocket.receive_bytes()
            # Publish to Redis channel for this user
            count = await redis.publish(channel, data)
            # logger.debug(f"Published {len(data)} bytes to {channel}. Subscribers: {count}")
    except WebSocketDisconnect:
        manager.disconnect_streamer(user_id)
    except Exception as e:
        logger.error(f"Stream connection error for {user_id}: {e}")
        manager.disconnect_streamer(user_id)

@router.websocket("/admin/{target_user_id}")
async def websocket_admin_endpoint(
    websocket: WebSocket, 
    target_user_id: str,
    token: Optional[str] = Query(None)
):
    """
    Admin Viewer Endpoint.
    URL: ws://HOST/api/v1/ws/admin/{user_id}?token=JWT
    """
    logger.info(f"ENTERING admin websocket endpoint for user: {target_user_id}. Token: {token[:10] if token else 'None'}...")
    
    if not token:
        logger.warning(f"No token provided for admin socket to {target_user_id}")
        await websocket.accept() # Accept then close to provide specific code
        await websocket.close(code=4001)
        return

    db = next(get_db())
    try:
        admin_user = get_user_from_token(token, db)
    finally:
        db.close()
    
    if not admin_user or not admin_user.is_superuser:
        logger.warning(f"Unauthorized admin access attempt to user {target_user_id}")
        await websocket.accept()
        await websocket.close(code=4001)
        return

    logger.info(f"Admin {admin_user.id} authorized to watch {target_user_id}. Accepting connection...")
    await manager.connect_admin(websocket, target_user_id)
    await websocket.accept()
    logger.info(f"WebSocket accepted for admin watching {target_user_id}")
    
    redis = get_async_redis()
    pubsub = redis.pubsub()
    try:
        logger.info(f"Subscribing to Redis channel: live_stream:{target_user_id}")
        await pubsub.subscribe(f"live_stream:{target_user_id}")
        logger.info(f"Successfully subscribed to live_stream:{target_user_id}")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to subscribe to Redis for {target_user_id}: {e}")
        # We don't close the socket, but the admin will see no data.
    
    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    await websocket.send_bytes(message['data'])
        except Exception as e:
            logger.debug(f"Redis listener for admin watching {target_user_id} stopped: {e}")

    # Start the redis listener in the background
    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            # Keep connection alive and wait for client to close/disconnect
            # Admin client doesn't need to send anything, but we need to wait
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info(f"Admin disconnected from watching: {target_user_id}")
    except Exception as e:
        logger.error(f"Admin connection error for {target_user_id}: {e}")
    finally:
        listener_task.cancel()
        await pubsub.unsubscribe(f"live_stream:{target_user_id}")
        await pubsub.close()
        manager.disconnect_admin(websocket, target_user_id)
