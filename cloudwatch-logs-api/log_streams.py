from fastapi import APIRouter, HTTPException, Path, Query
from typing import Optional, List

from schemas import LogStream, LogStreamList
from logs_service import get_log_streams

router = APIRouter()

@router.get("/log-streams/{log_group_name}", response_model=List[LogStream])
async def list_log_streams(
    log_group_name: str = Path(..., description="Log group name"),
    prefix: Optional[str] = Query(None, description="Log stream name prefix filter"),
    limit: int = Query(50, description="Maximum number of log streams to return", gt=0, le=100)
):
    """
    Get log streams for a specific log group.
    """
    try:
        log_streams = await get_log_streams(
            log_group_name=log_group_name, 
            prefix=prefix, 
            limit=limit
        )
        return log_streams
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching log streams: {str(e)}")