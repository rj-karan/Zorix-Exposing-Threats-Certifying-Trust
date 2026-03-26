from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ===== User Schemas =====
class UserCreate(BaseModel):
    """User creation schema."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """User login schema."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema."""

    id: UUID
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Project Schemas =====
class ProjectCreate(BaseModel):
    """Project creation schema."""

    name: str = Field(..., min_length=1, max_length=255)
    repository_url: str = Field(..., min_length=1)


class ProjectResponse(BaseModel):
    """Project response schema."""

    id: UUID
    name: str
    repository_url: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Bug Report Schemas =====
class BugReportCreate(BaseModel):
    """Bug report creation schema."""

    project_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    severity: Optional[str] = None
    cve_id: Optional[str] = None
    affected_file: str = Field(..., min_length=1)
    affected_line: Optional[int] = None
    source: str = "manual"


class BugReportResponse(BaseModel):
    """Bug report response schema."""

    id: UUID
    project_id: UUID
    title: str
    description: str
    severity: Optional[str]
    cve_id: Optional[str]
    affected_file: str
    affected_line: Optional[int]
    source: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Code Snapshot Schemas =====
class CodeSnapshotResponse(BaseModel):
    """Code snapshot response schema."""

    id: UUID
    bug_report_id: UUID
    repo_url: str
    commit_hash: Optional[str]
    snapshot_data: str
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Analysis Result Schemas =====
class AnalysisResultCreate(BaseModel):
    """Analysis result creation schema."""

    root_cause: Optional[str] = None
    exploit_payload: Optional[str] = None
    suggested_patch: Optional[str] = None
    confidence_score: float = 0.0


class AnalysisResultResponse(BaseModel):
    """Analysis result response schema."""

    id: UUID
    bug_report_id: UUID
    root_cause: Optional[str]
    exploit_payload: Optional[str]
    suggested_patch: Optional[str]
    confidence_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ===== Auth Schemas =====
class TokenResponse(BaseModel):
    """Token response schema."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
