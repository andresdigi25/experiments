from fastapi import APIRouter, HTTPException, Path, Query, Body
from typing import Optional, List
from datetime import datetime

from schemas import LogEvent, LogEventList, LogsQueryRequest, LogQueryResult
from logs_service import get_log_events, query_logs

router = APIRouter()

@router.get("/logs/{log_group_name}", response_model=List[LogEvent])
async def list_logs(
    log_group_name: str = Path(..., description="Log group name"),
    log_stream_name: Optional[str] = Query(None, description="Log stream name, if omitted retrieves from all streams"),
    start_time: Optional[datetime] = Query(None, description="Start time for log events (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time for log events (ISO format)"),
    filter_pattern: str = Query("", description="CloudWatch Logs filter pattern"),
    limit: int = Query(1000, description="Maximum number of log events to return", gt=0, le=10000)
):
    """
    Get logs from a specific log group and optionally a specific log stream.
    """
    try:
        log_events = await get_log_events(
            log_group_name=log_group_name,
            log_stream_name=log_stream_name,
            start_time=start_time,
            end_time=end_time,
            filter_pattern=filter_pattern,
            limit=limit
        )
        return log_events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@router.post("/query", response_model=LogQueryResult)
async def query_log_data(request: LogsQueryRequest = Body(...)):
    """
    Run a CloudWatch Logs Insights query against a log group.
    """
    try:
        result = await query_logs(
            log_group_name=request.log_group_name,
            service_name=request.service_name or request.log_group_name.split('/')[-1],
            query_string=request.query_string,
            start_time=request.start_time,
            end_time=request.end_time,
            limit=request.limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying logs: {str(e)}")

@router.get("/query", response_model=LogQueryResult)
async def query_log_data_get(
    log_group_name: str = Query(..., description="Log group name"),
    service_name: Optional[str] = Query(None, description="Service name, defaults to last part of log group name"),
    query_string: str = Query(..., description="CloudWatch Logs Insights query"),
    start_time: Optional[datetime] = Query(None, description="Start time for query (ISO format)"),
    end_time: Optional[datetime] = Query(None, description="End time for query (ISO format)"),
    limit: int = Query(1000, description="Maximum number of results to return", gt=0, le=10000)
):
    """
    Run a CloudWatch Logs Insights query against a log group using GET.
    """
    try:
        result = await query_logs(
            log_group_name=log_group_name,
            service_name=service_name or log_group_name.split('/')[-1],
            query_string=query_string,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying logs: {str(e)}")