from fastapi import APIRouter

router = APIRouter()

@router.get("/poll")
def poll_alerts():
    """
    Poll for new alerts using long polling
    """
    return {"alerts": []}
