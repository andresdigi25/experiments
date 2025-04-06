from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Log Group Models
class LogGroup(BaseModel):
    name: str
    arn: str
    creation_time: Optional[int] = None
    retention_in_days: Optional[int] = None
    metric_filter_count: Optional[int] = None
    
class LogGroupList(BaseModel):
    log_groups: List[LogGroup]
    next_token: Optional[str] = None

# Log Stream Models
class LogStream(BaseModel):
    name: str
    log_group_name: Optional[str] = None
    creation_time: Optional[int] = None
    first_event_timestamp: Optional[int] = None
    last_event_timestamp: Optional[int] = None
    last_ingestion_time: Optional[int] = None
    
class LogStreamList(BaseModel):
    log_streams: List[LogStream]
    next_token: Optional[str] = None

# Log Event Models
class LogEvent(BaseModel):
    timestamp: int
    message: str
    ingestion_time: Optional[int] = None
    log_stream_name: str

class LogEventList(BaseModel):
    log_events: List[LogEvent]
    next_token: Optional[str] = None

# Query Models
class LogsQueryRequest(BaseModel):
    log_group_name: str
    service_name: Optional[str] = None
    query_string: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = 1000

class QueryResultField(BaseModel):
    field: str
    value: str

class QueryResult(BaseModel):
    results: List[Dict[str, str]]
    statistics: Optional[Dict[str, Any]] = None
    status: str

class LogQueryResult(BaseModel):
    service: str
    log_group_name: str
    query_id: Optional[str] = None
    results: List[Dict[str, str]]
    status: str

# Join Models
class JoinLogsRequest(BaseModel):
    services: List[str] = Field(..., description="List of service names")
    log_groups: List[str] = Field(..., description="List of log group names corresponding to services")
    query_string: str = Field(..., description="CloudWatch Logs Insights query to run against each log group")
    join_field: str = Field(..., description="Field to use for joining results across services")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
class JoinedLogResults(BaseModel):
    start_time: datetime
    end_time: datetime
    services: List[str]
    join_field: str
    results: List[Dict[str, Any]]
    count: int