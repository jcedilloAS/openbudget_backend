"""Request utilities for extracting information from FastAPI requests."""

from fastapi import Request
from typing import Optional


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Checks X-Forwarded-For header first (for proxies/load balancers),
    then falls back to direct client host.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Client IP address as string, or "unknown" if cannot be determined
    """
    # Check for forwarded IP (behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header (some proxies use this)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fallback to direct client host
    if request.client:
        return request.client.host
    
    return "unknown"


def get_user_agent(request: Request) -> Optional[str]:
    """
    Extract User-Agent from request headers.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        User-Agent string or None
    """
    return request.headers.get("User-Agent")
