from fastapi import FastAPI
from app.api.v1.endpoints import auth, activity, alerts, screenshots, admin
from app.core.config import settings

app = FastAPI(title="Employee Monitoring System API")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(activity.router, prefix="/api/v1/activity", tags=["activity"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(screenshots.router, prefix="/api/v1/screenshots", tags=["screenshots"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Employee Monitoring System API"}
