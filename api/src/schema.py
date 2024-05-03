from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    user_ids: Optional[List[str]]
    template_name: str
    version: int
    send_immediately: bool
    send_time: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


class Template_schema(BaseModel):
    version: int
    name: str
    text: str
