"""Rate limiting configuration."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Use client IP for rate limiting
limiter = Limiter(key_func=get_remote_address)

# Rate limit settings from config
RATE_LIMIT_REQUESTS_PER_MINUTE = settings.rate_limit_requests_per_minute
RATE_LIMIT_WS_CONNECTIONS_PER_IP = settings.rate_limit_ws_connections_per_ip
