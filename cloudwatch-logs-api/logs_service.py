import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from aws_client import logs_client, get_aioboto3_client
from config import settings
from schemas import LogGroup, LogStream, LogEvent, LogQueryResult

logger = logging.getLogger(__name__)

async def get_log_groups(prefix: Optional[str] = None, limit: int = 50) -> List[LogGroup]:
    """
    Get CloudWatch log groups, optionally filtered by prefix
    """
    try:
        params = {"limit": limit}
        if prefix:
            params["logGroupNamePrefix"] = prefix
        
        async with await get_aioboto3_client('logs') as logs:
            response = await logs.describe_log_groups(**params)
        
        log_groups = [
            LogGroup(
                name=lg["logGroupName"],
                arn=lg["arn"],
                creation_time=lg.get("creationTime"),
                retention_in_days=lg.get("retentionInDays"),
                metric_filter_count=lg.get("metricFilterCount")
            ) 
            for lg in response.get("logGroups", [])
        ]
        
        return log_groups
    except Exception as e:
        logger.error(f"Error fetching log groups: {str(e)}")
        raise

async def get_log_streams(log_group_name: str, prefix: Optional[str] = None, limit: int = 50) -> List[LogStream]:
    """
    Get log streams for a specific log group
    """
    try:
        params = {
            "logGroupName": log_group_name,
            "limit": limit,
            "descending": True,
            "orderBy": "LastEventTime"
        }
        
        if prefix:
            params["logStreamNamePrefix"] = prefix
        
        async with await get_aioboto3_client('logs') as logs:
            response = await logs.describe_log_streams(**params)
        
        log_streams = [
            LogStream(
                name=ls["logStreamName"],
                log_group_name=log_group_name,
                creation_time=ls.get("creationTime"),
                first_event_timestamp=ls.get("firstEventTimestamp"),
                last_event_timestamp=ls.get("lastEventTimestamp"),
                last_ingestion_time=ls.get("lastIngestionTime")
            ) 
            for ls in response.get("logStreams", [])
        ]
        
        return log_streams
    except Exception as e:
        logger.error(f"Error fetching log streams for {log_group_name}: {str(e)}")
        raise

async def get_log_events(
    log_group_name: str,
    log_stream_name: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    filter_pattern: str = "",
    limit: int = 1000
) -> List[LogEvent]:
    """
    Get logs from a specific log group and optionally a specific log stream
    """
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
            "limit": min(limit, settings.MAX_LOGS_RESULTS),
        }
        
        if log_stream_name:
            params["logStreamNames"] = [log_stream_name]
        
        if filter_pattern:
            params["filterPattern"] = filter_pattern
            
        async with await get_aioboto3_client('logs') as logs:
            response = await logs.filter_log_events(**params)
        
        log_events = [
            LogEvent(
                timestamp=event["timestamp"],
                message=event["message"],
                ingestion_time=event.get("ingestionTime"),
                log_stream_name=event["logStreamName"]
            ) 
            for event in response.get("events", [])
        ]
        
        return log_events
    except Exception as e:
        logger.error(f"Error fetching logs for {log_group_name}: {str(e)}")
        raise

async def query_logs(
    log_group_name: str,
    service_name: str,
    query_string: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 1000
) -> LogQueryResult:
    """
    Run a CloudWatch Logs Insights query against a log group
    """
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
        async with await get_aioboto3_client('logs') as logs:
            start_query_response = await logs.start_query(
                logGroupName=log_group_name,
                startTime=start_timestamp,
                endTime=end_timestamp,
                queryString=query_string,
                limit=min(limit, settings.MAX_LOGS_RESULTS)
            )
            
            query_id = start_query_response['queryId']
            
            # Poll for results with timeout
            max_time = time.time() + settings.MAX_QUERY_DURATION_SECONDS
            
            while time.time() < max_time:
                query_response = await logs.get_query_results(queryId=query_id)
                
                if query_response['status'] in ['Complete', 'Failed', 'Cancelled', 'Timeout']:
                    break
                
                # Wait before checking again
                await asyncio.sleep(1)
            
            # Process results
            results = []
            for result in query_response['results']:
                result_dict = {}
                for field in result:
                    result_dict[field['field']] = field['value']
                results.append(result_dict)
            
            # Get statistics if available
            statistics = query_response.get('statistics', None)
            
            return LogQueryResult(
                service=service_name,
                log_group_name=log_group_name,
                query_id=query_id,
                results=results,
                status=query_response['status']
            )
    except Exception as e:
        logger.error(f"Error querying logs for {log_group_name}: {str(e)}")
        raise

async def join_logs_query(
    services: List[str],
    log_groups: List[str],
    query_string: str,
    join_field: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> Tuple[List[Dict[str, Any]], datetime, datetime]:
    """
    Run the same query against multiple log groups and join the results
    """
    if len(services) != len(log_groups):
        raise ValueError("Number of services must match number of log groups")
    
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
    
    return final_results, start_time, end_time