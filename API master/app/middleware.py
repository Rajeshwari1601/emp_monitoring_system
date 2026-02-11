from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("API")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Consume body to log it
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
        
        # Reset the request body so it can be read again by the endpoint
        async def receive():
            return {"type": "http.request", "body": body}
        
        request._receive = receive
        
        try:
            response = await call_next(request)
            logger.info(f"RES: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Middleware caught error: {e}")
            raise e
