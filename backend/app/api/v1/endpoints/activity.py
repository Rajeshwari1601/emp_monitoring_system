from fastapi import APIRouter

router = APIRouter()

@router.post("/log")
def log_activity():
    """
    Receive employee activity logs
    """
    return {"status": "logged"}
