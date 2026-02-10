from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        body = await request.body()
        log_body = "Binary/Large Body"
        try:
             if len(body) < 1000:
                log_body = body.decode()
             else:
                log_body = f"Truncated Body ({len(body)} bytes)"
        except:
             pass
             
        logger.info(f"REQ: {request.method} {request.url} | BODY: {log_body}")
        
        response = await call_next(request)
        
        logger.info(f"RES: {response.status_code}")
        return response
