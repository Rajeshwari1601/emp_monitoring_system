from fastapi import APIRouter

router = APIRouter()

@router.get("/dashboard/stats")
def get_stats():
    """
    Get statistics for the admin dashboard
    """
    return {"online_users": 0, "active_alerts": 0}
