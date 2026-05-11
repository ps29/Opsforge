from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ReportCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    owner: str = Field(min_length=2, max_length=80)
    data: dict[str, Any] = Field(default_factory=dict)
    force_fail: bool = False


class ReportAccepted(BaseModel):
    id: str
    status: str


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    payload: dict[str, Any]
    input_summary: str
    output: dict[str, Any] | None
    attempts: int
    failure_reason: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
