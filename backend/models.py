from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.orm import relationship
from backend.database import Base
from backend.config import get_settings
import uuid
from datetime import datetime


# Cross-dialect UUID support
class GUID(TypeDecorator):
    """Platform-independent GUID type that uses CHAR(36) on SQLite and UUID on PostgreSQL."""
    
    impl = CHAR(36)
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        settings = get_settings()
        if settings.DATABASE_TYPE == "postgres":
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))
    
    def process_bind_param(self, value, dialect):
        settings = get_settings()
        if value is None:
            return value
        if settings.DATABASE_TYPE == "postgres":
            return value
        return str(value) if not isinstance(value, str) else value
    
    def process_result_value(self, value, dialect):
        settings = get_settings()
        if value is None:
            return value
        if settings.DATABASE_TYPE == "postgres":
            return value
        return uuid.UUID(value) if isinstance(value, str) else value


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="user")


class Project(Base):
    """Project model."""

    __tablename__ = "projects"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    repository_url = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="projects")
    bug_reports = relationship("BugReport", back_populates="project")


class BugReport(Base):
    """Bug report model."""

    __tablename__ = "bug_reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    project_id = Column(GUID(), ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), nullable=True)
    cve_id = Column(String(50), nullable=True, index=True)
    affected_file = Column(String(1024), nullable=False)
    affected_line = Column(Integer, nullable=True)
    source = Column(String(50), default="manual", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="bug_reports")
    code_snapshots = relationship("CodeSnapshot", back_populates="bug_report")
    analysis_results = relationship("AnalysisResult", back_populates="bug_report")


class CodeSnapshot(Base):
    """Code snapshot model."""

    __tablename__ = "code_snapshots"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    bug_report_id = Column(GUID(), ForeignKey("bug_reports.id"), nullable=False, index=True)
    repo_url = Column(String(1024), nullable=False)
    commit_hash = Column(String(255), nullable=True)
    snapshot_data = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bug_report = relationship("BugReport", back_populates="code_snapshots")


class AnalysisResult(Base):
    """Analysis result model."""

    __tablename__ = "analysis_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    bug_report_id = Column(GUID(), ForeignKey("bug_reports.id"), nullable=False, index=True)
    root_cause = Column(Text, nullable=True)
    exploit_payload = Column(Text, nullable=True)
    suggested_patch = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bug_report = relationship("BugReport", back_populates="analysis_results")
