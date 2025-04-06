from sqlmodel import SQLModel, Field
from typing import Optional

class Resource1(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    resource_tag_id: Optional[int] = None
    name: Optional[str] = None
    pretty_name: Optional[str] = None
    service_id: Optional[int] = None
    internal_only: bool = Field(default=True)
    grants_access: bool = Field(default=True)