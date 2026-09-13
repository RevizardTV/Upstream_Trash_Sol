import logging
import time
from logging.handlers import RotatingFileHandler
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure Log Formatter
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
formatter = logging.Formatter(LOG_FORMAT)

# Rotating File Handler for General System Logs
general_file_handler = RotatingFileHandler("app.log", maxBytes=5_000_000, backupCount=3)
general_file_handler.setFormatter(formatter)
general_file_handler.setLevel(logging.INFO)

# Rotating File Handler for Security & Login Audits
security_file_handler = RotatingFileHandler("security.log", maxBytes=5_000_000, backupCount=3)
security_file_handler.setFormatter(formatter)
security_file_handler.setLevel(logging.INFO)

# Console Output Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.INFO)

# Logger Instances
logger = logging.getLogger("EcoRecycle.System")
logger.setLevel(logging.INFO)
logger.addHandler(general_file_handler)
logger.addHandler(console_handler)

auth_logger = logging.getLogger("EcoRecycle.Auth")
auth_logger.setLevel(logging.INFO)
auth_logger.addHandler(security_file_handler)
auth_logger.addHandler(console_handler)


# Performance Tracking Middleware
class PerformanceLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            
            # Log endpoints taking longer than 200ms as warnings
            if process_time > 200:
                logger.warning(
                    f"SLOW ENDPOINT: {request.method} {request.url.path} "
                    f"completed in {process_time:.2f}ms | Status: {response.status_code}"
                )
            else:
                logger.info(
                    f"PERF: {request.method} {request.url.path} "
                    f"took {process_time:.2f}ms | Status: {response.status_code}"
                )
            return response
            
        except Exception as exc:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"UNCAUGHT EXCEPTION: {request.method} {request.url.path} "
                f"failed after {process_time:.2f}ms | Error: {str(exc)}",
                exc_info=True
            )
            raise exc


# Audit Helper Functions
def log_auth_event(event_type: str, email: str, status: str, ip: str, detail: str = ""):
    """Logs authentication actions like OTP requests, user logins, and staff logins."""
    message = f"EVENT: {event_type} | EMAIL: {email} | STATUS: {status} | IP: {ip}"
    if detail:
        message += f" | DETAIL: {detail}"
    
    if status.lower() in ["success", "verified"]:
        auth_logger.info(message)
    else:
        auth_logger.warning(message)


def log_recycling_action(action_type: str, user_id: int, weight: float, status: str, detail: str = ""):
    """Logs waste recycling submissions and staff decisions."""
    message = f"ACTION: {action_type} | USER_ID: {user_id} | WEIGHT: {weight}kg | STATUS: {status}"
    if detail:
        message += f" | DETAIL: {detail}"
    logger.info(message)