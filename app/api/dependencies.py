"""API dependencies and utilities"""
from fastapi import Depends, HTTPException, status, Header, Query
from typing import Optional
from app.utils.logger import logger

async def verify_api_key(
    x_api_key: Optional[str] = Header(None)
) -> str:
    """Verify API key"""
    # In production, validate against actual API keys
    if x_api_key is None:
        logger.warning("Missing API key")
        # raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key required")
    return x_api_key or "default"

async def get_pagination(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
) -> dict:
    """Get pagination parameters"""
    return {"skip": skip, "limit": limit}

def verify_admin(api_key: str = Depends(verify_api_key)) -> str:
    """Verify admin access"""
    # In production, check if key has admin permissions
    return api_key
