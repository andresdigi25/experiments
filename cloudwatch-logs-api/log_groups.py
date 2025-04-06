from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from schemas import LogGroup, LogGroupList
from logs_service import get_log_groups

router = APIRouter()

@router.get("/log-groups", response_model=List[LogGroup])
async def list_log_groups(
    prefix: Optional[str] = Query(None, description="Log group name prefix filter"),
    limit: int = Query(50, description="Maximum number of log groups to return", gt=0, le=100)
):
    """
    Get all CloudWatch log groups, optionally filtered by prefix.
    """
    try:
        log_groups = await get_log_groups(prefix=prefix, limit=limit)
        return log_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching log groups: {str(e)}")