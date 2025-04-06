from fastapi import APIRouter, HTTPException, Query as QueryParam, Body
from typing import List, Optional
from datetime import datetime

from schemas import JoinLogsRequest, JoinedLogResults
from logs_service import join_logs_query

router = APIRouter()

@router.post("/join-query", response_model=JoinedLogResults)
async def join_logs_data(request: JoinLogsRequest = Body(...)):
    """
    Run the same query against multiple log groups and join the results by a common field.
    """
    try:
        results, start_time, end_time = await join_logs_query(
            services=request.services,
            log_groups=request.log_groups,
            query_string=request.query_string,
            join_field=request.join_field,
            start_time=request.start_time,
            end_time=request.end_time
        )
        
        return JoinedLogResults(
            start_time=start_time,
            end_time=end_time,
            services=request.services,
            join_field=request.join_field,
            results=results,
            count=len(results)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error joining log data: {str(e)}")

@router.get("/join-query", response_model=JoinedLogResults)
async def join_logs_data_get(
    services: List[str] = QueryParam(..., description="List of service names"),
    log_groups: List[str] = QueryParam(..., description="List of log group names corresponding to services"),
    query_string: str = QueryParam(..., description="CloudWatch Logs Insights query to run against each log group"),
    join_field: str = QueryParam(..., description="Field to use for joining results across services"),
    start_time: Optional[datetime] = QueryParam(None, description="Start time for query (ISO format)"),
    end_time: Optional[datetime] = QueryParam(None, description="End time for query (ISO format)")
):
    """
    Run the same query against multiple log groups and join the results by a common field using GET.
    """
    try:
        if len(services) != len(log_groups):
            raise HTTPException(
                status_code=400, 
                detail="Number of services must match number of log groups"
            )
        
        results, start_time, end_time = await join_logs_query(
            services=services,
            log_groups=log_groups,
            query_string=query_string,
            join_field=join_field,
            start_time=start_time,
            end_time=end_time
        )
        
        return JoinedLogResults(
            start_time=start_time,
            end_time=end_time,
            services=services,
            join_field=join_field,
            results=results,
            count=len(results)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error joining log data: {str(e)}")