"""
Task Pydantic schemas
Request and response models for Task API endpoints
Reference: https://fastapi.tiangolo.com/tutorial/body/
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TaskBase(BaseModel):
    """
    Base schema with common Task fields
    Used as base for create and update schemas
    """
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    completed: bool = Field(default=False, description="Whether the task is completed")


class TaskCreate(TaskBase):
    """
    Schema for creating a new task
    Inherits from TaskBase
    """
    pass


class TaskUpdate(BaseModel):
    """
    Schema for updating a task
    All fields are optional for partial updates
    Reference: https://fastapi.tiangolo.com/tutorial/body-updates/
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    completed: Optional[bool] = Field(None, description="Whether the task is completed")


class TaskResponse(TaskBase):
    """
    Schema for task response
    Includes all fields from TaskBase plus database-generated fields
    """
    id: int = Field(..., description="Task ID")
    created_at: datetime = Field(..., description="Timestamp when task was created")
    updated_at: datetime = Field(..., description="Timestamp when task was last updated")
    
    class Config:
        """
        Pydantic configuration
        Reference: https://docs.pydantic.dev/latest/concepts/config/
        """
        from_attributes = True  # Allow creation from ORM objects (SQLAlchemy models)
        json_encoders = {
            datetime: lambda v: v.isoformat()  # Convert datetime to ISO format in JSON
        }

