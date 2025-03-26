"""
Common type definitions using Pydantic models
"""

from pydantic import BaseModel
from typing import Optional
from enum import Enum


class PortfolioCompany(BaseModel):
    """A company in the EQT portfolio"""

    name: str
    sector: str
    fund: str
    country: str
    entry_year: str
    link: str
    website: Optional[str] = None

    def dict(self):
        """Convert model to a dictionary, compatible with both Pydantic v1 and v2"""
        try:
            # Try Pydantic v2 method
            return self.model_dump()
        except AttributeError:
            # Fallback to Pydantic v1 method
            return super().dict()


class JobStatus(str, Enum):
    """Status of an asynchronous job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobProgress(BaseModel):
    """Progress information for an asynchronous job"""
    
    job_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    message: Optional[str] = None  # Status message to display
    result: Optional[str] = None  # Final result when completed
    error: Optional[str] = None  # Error message if failed