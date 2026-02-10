from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.core.redis import get_redis
from app.models.data import Command, Screenshot, AppLog, BrowserLog
from app.schemas import client as client_schema
from app.models.user import User
import json
import base64
import os
import uuid
import logging

# Setup logger
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/heartbeat", response_model=client_schema.HeartbeatResponse)
def heartbeat(
    *,
    status_in: client_schema.HeartbeatRequest,
    current_user: User = Depends(deps.get_current_user),
    redis = Depends(get_redis)
) -> Any:
    # Update Redis
    # PRD: online:{user_id} -> timestamp (TTL 30s)
    redis.setex(f"online:{current_user.id}", 30, "online")
    return {"success": True}

@router.get("/commands", response_model=List[client_schema.CommandSchema])
def get_commands(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    # Get PENDING commands
    commands = db.query(Command).filter(
        Command.user_id == current_user.id,
        Command.status == "PENDING"
    ).all()
    return commands

@router.post("/command/ack", response_model=dict)
def ack_command(
    ack_in: client_schema.CommandAck,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    cmd = db.query(Command).filter(Command.id == ack_in.command_id).first()
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")
    
    cmd.status = ack_in.status
    db.commit()
    return {"success": True}

@router.post("/screenshot/upload", response_model=client_schema.ScreenshotResponse)
def upload_screenshot(
    screenshot_in: client_schema.ScreenshotUpload,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    file_name = f"{uuid.uuid4()}.png"
    file_path = f"static/screenshots/{file_name}"
    
    real_url = ""
    try:
        if screenshot_in.image_base64:
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(screenshot_in.image_base64))
            # Construct URL - strictly ideally this should come from config
            real_url = f"http://localhost:8000/static/screenshots/{file_name}"
        else:
             logger.warning("No image_base64 provided in upload")
             real_url = "https://placehold.co/600x400?text=No+Image"
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        real_url = "https://placehold.co/600x400?text=Error+Saving"
    
    shot = Screenshot(
        user_id=current_user.id,
        command_id=screenshot_in.command_id,
        url=real_url,
        file_path=file_path
    )
    db.add(shot)
    db.commit()
    
    return {"success": True, "screenshot_url": real_url}

@router.post("/apps/upload", response_model=dict)
def upload_apps(
    apps_in: client_schema.AppLogUpload,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    log = AppLog(
        user_id=current_user.id,
        command_id=apps_in.command_id,
        apps=[app.dict() for app in apps_in.apps]
    )
    db.add(log)
    db.commit()
    return {"success": True}

@router.post("/browser/upload", response_model=dict)
def upload_browser(
    browser_in: client_schema.BrowserLogUpload,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Any:
    log = BrowserLog(
        user_id=current_user.id,
        command_id=browser_in.command_id,
        browser=browser_in.browser,
        youtube_open=browser_in.youtube_open,
        details=browser_in.details
    )
    db.add(log)
    db.commit()
    return {"success": True}
