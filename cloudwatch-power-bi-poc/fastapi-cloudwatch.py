# main.py
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

import boto3
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="CloudWatch Logs Query API", 
              description="API for querying and joining AWS CloudWatch logs from multiple services")

# Add CORS middleware to allow frontend to communicate with API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for the web interface)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize CloudWatch Logs client
logs_client = boto3.client('logs')

# Define models
class LogGroup(BaseModel):
    name: str
    arn: str

class LogStream(BaseModel):
    name: str
    lastEventTimestamp: Optional[int] = None
    creationTime: Optional[int] = None

class LogEvent(BaseModel):
    timestamp: int
    message: str
    logStreamName: str

class LogQueryResult(BaseModel):
    service: str
    logGroupName: str
    results: List[Dict[str, Any]]

class JoinedLogResults(BaseModel):
    startTime: datetime
    endTime: datetime
    services: List[str]
    results: List[Dict[str, Any]]

@app.get("/", include_in_schema=False)
async def root():
    """Redirect to docs"""
    return {"message": "Welcome to CloudWatch Logs Query API. Visit /docs for API documentation."}

@app.get("/api/log-groups", response_model=List[LogGroup])
async def get_log_groups(prefix: Optional[str] = None):
    """Get all log groups, optionally filtered by prefix"""
    try:
        params = {}
        if prefix:
            params["logGroupNamePrefix"] = prefix
        
        response = logs_client.describe_log_groups(**params)
        log_groups = [
            LogGroup(name=lg["logGroupName"], arn=lg["arn"]) 
            for lg in response.get("logGroups", [])
        ]
        return log_groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching log groups: {str(e)}")

@app.get("/api/log-streams/{log_group_name}", response_model=List[LogStream])
async def get_log_streams(
    log_group_name: str, 
    prefix: Optional[str] = None,
    limit: int = 50
):
    """Get log streams for a specific log group"""
    try:
        params = {
            "logGroupName": log_group_name,
            "limit": limit,
            "descending": True,
            "orderBy": "LastEventTime"
        }
        if prefix:
            params["logStreamNamePrefix"] = prefix
            
        response = logs_client.describe_log_streams(**params)
        log_streams = [
            LogStream(
                name=ls["logStreamName"],
                lastEventTimestamp=ls.get("lastEventTimestamp"),
                creationTime=ls.get("creationTime")
            ) 
            for ls in response.get("logStreams", [])
        ]
        return log_streams
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching log streams: {str(e)}")

@app.get("/api/logs/{log_group_name}", response_model=List[LogEvent])
async def get_logs(
    log_group_name: str,
    log_stream_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    filter_pattern: str = "",
    limit: int = 1000
):
    """Get logs from a specific log group and optionally a specific log stream"""
    try:
        # Default to last 24 hours if not specified
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Convert datetime to milliseconds timestamp
        start_timestamp = int(start_time.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        
        params = {
            "logGroupName": log_group_name,
            "startTime": start_timestamp,
            "endTime": end_timestamp,
            "limit": limit,
        }
        
        if log_stream_name:
            params["logStreamNames"] = [log_stream_name]
        
        if filter_pattern:
            params["filterPattern"] = filter_pattern
            
        response = logs_client.filter_log_events(**params)
        log_events = [
            LogEvent(
                timestamp=event["timestamp"],
                message=event["message"],
                logStreamName=event["logStreamName"]
            ) 
            for event in response.get("events", [])
        ]
        return log_events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching logs: {str(e)}")

@app.get("/api/query", response_model=LogQueryResult)
async def query_logs(
    log_group_name: str,
    service_name: str,
    query_string: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000
):
    """Run a CloudWatch Logs Insights query against a log group"""
    try:
        # Default to last 24 hours if not specified
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Convert datetime to seconds timestamp (Logs Insights uses seconds)
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())
        
        # Start the query
        start_query_response = logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_timestamp,
            endTime=end_timestamp,
            queryString=query_string,
            limit=limit
        )
        
        query_id = start_query_response['queryId']
        
        # Poll for results
        response = None
        while response is None or response['status'] == 'Running':
            response = logs_client.get_query_results(
                queryId=query_id
            )
            if response['status'] == 'Running':
                # Wait a bit before checking again
                import time
                time.sleep(1)
        
        # Format results
        results = []
        for result in response['results']:
            result_dict = {}
            for field in result:
                result_dict[field['field']] = field['value']
            results.append(result_dict)
        
        return LogQueryResult(
            service=service_name,
            logGroupName=log_group_name,
            results=results
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying logs: {str(e)}")

@app.get("/api/join-query", response_model=JoinedLogResults)
async def join_logs_query(
    services: List[str] = Query(..., description="List of service names"),
    log_groups: List[str] = Query(..., description="List of log group names corresponding to services"),
    query_string: str = Query(..., description="CloudWatch Logs Insights query to run against each log group"),
    join_field: str = Query(..., description="Field to use for joining results across services"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
):
    """Run the same query against multiple log groups and join the results"""
    try:
        if len(services) != len(log_groups):
            raise HTTPException(
                status_code=400, 
                detail="Number of services must match number of log groups"
            )
        
        # Default to last 24 hours if not specified
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=24)
        
        # Query each service's logs
        query_results = []
        for service, log_group in zip(services, log_groups):
            result = await query_logs(
                log_group_name=log_group,
                service_name=service,
                query_string=query_string,
                start_time=start_time,
                end_time=end_time
            )
            query_results.append(result)
        
        # Join results based on the join field
        joined_data = {}
        for service_result in query_results:
            service = service_result.service
            for result in service_result.results:
                if join_field in result:
                    join_value = result[join_field]
                    
                    if join_value not in joined_data:
                        joined_data[join_value] = {
                            "join_value": join_value,
                            "services": {}
                        }
                    
                    # Add service-specific data
                    joined_data[join_value]["services"][service] = result
        
        # Convert to list of results
        final_results = list(joined_data.values())
        
        return JoinedLogResults(
            startTime=start_time,
            endTime=end_time,
            services=services,
            results=final_results
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error joining log data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)