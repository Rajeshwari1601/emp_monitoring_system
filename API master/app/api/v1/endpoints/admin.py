from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.core.redis import get_redis
from app.models.user import User, Device
from app.models.data import Command, Screenshot, AppLog, BrowserLog
from app.schemas import user as user_schema, client as client_schema

router = APIRouter()

@router.get("/online-users")
def get_online_users(
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db),
    redis = Depends(get_redis)
) -> Any:
    # Scan Redis for online keys
    # Keys: online:{user_id}
    online_keys = redis.keys("online:*")
    users_data = []
    
    for key in online_keys:
        user_id = key.split(":")[1]
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Find device info?
            device = db.query(Device).filter(Device.user_id == user.id).first()
            users_data.append({
                "user_id": user.id,
                "name": user.name,
                "device_name": device.name if device else "Unknown"
            })
            
    return {"users": users_data}



@router.get("/users", response_model=List[user_schema.User])
def get_all_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@router.post("/command/send", response_model=client_schema.CommandResponse)
def send_command(
    cmd_in: client_schema.CommandCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db)
) -> Any:
    cmd = Command(
        user_id=cmd_in.user_id,
        command=cmd_in.command,
        payload=cmd_in.payload,
        status="PENDING"
    )
    db.add(cmd)
    db.commit()
    db.refresh(cmd)
    return {"success": True, "command_id": cmd.id}

@router.post("/notify")
def send_notification(
    payload: client_schema.NotifySchema,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db)
) -> Any:
    cmd_payload = {
        "title": payload.title,
        "message": payload.message
    }
    
    cmd = Command(
        user_id=payload.user_id,
        command="SEND_NOTIFICATION",
        payload=cmd_payload,
        status="PENDING"
    )
    db.add(cmd)
    db.commit()
    
    return {"success": True}

@router.get("/screenshot/{command_id}")
def get_screenshot(
    command_id: str,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db)
) -> Any:
    shot = db.query(Screenshot).filter(Screenshot.command_id == command_id).first()
    if not shot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return {"url": shot.url, "created_at": shot.created_at}

@router.get("/apps/{user_id}")
def get_user_apps(
    user_id: str,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db)
) -> Any:
    # Get latest
    log = db.query(AppLog).filter(AppLog.user_id == user_id).order_by(AppLog.created_at.desc()).first()
    if not log:
         return {"apps": []}
    return {"apps": log.apps, "created_at": log.created_at}

@router.get("/browser/{user_id}")
def get_user_browser_logs(
    user_id: str,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db)
) -> Any:
    log = db.query(BrowserLog).filter(BrowserLog.user_id == user_id).order_by(BrowserLog.created_at.desc()).first()
    if not log:
        return {"browser": "Unknown", "youtube_open": False, "details": None}
    return {
        "browser": log.browser,
        "youtube_open": log.youtube_open,
        "details": log.details,
        "created_at": log.created_at
    }

@router.get("/commands")
def get_command_history(
    user_id: str,
    current_user: User = Depends(deps.get_current_active_superuser),
    db: Session = Depends(deps.get_db)
) -> Any:
    cmds = db.query(Command).filter(Command.user_id == user_id).order_by(Command.created_at.desc()).limit(20).all()
    return [{"id": c.id, "command": c.command, "status": c.status, "created_at": c.created_at} for c in cmds]
