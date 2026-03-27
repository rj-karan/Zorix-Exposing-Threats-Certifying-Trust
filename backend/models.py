from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Float, Boolean, JSON
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


# =====================================================
# MASTER ANALYSIS TABLE — tracks entire pipeline run
# =====================================================

class Analysis(Base):
    """Master analysis table — one row per pipeline run."""

    __tablename__ = "analyses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    repo_url = Column(String(1024), nullable=False)
    bug_description = Column(Text, nullable=False, default="")
    status = Column(String(50), nullable=False, default="pending")
    current_stage = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    pipeline_runs = relationship("PipelineRun", back_populates="analysis", cascade="all, delete-orphan")
    log_entries = relationship("LogEntry", back_populates="analysis", cascade="all, delete-orphan")


class PipelineRun(Base):
    """Tracks each pipeline stage execution."""

    __tablename__ = "pipeline_runs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(GUID(), ForeignKey("analyses.id"), nullable=False, index=True)
    stage_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    analysis = relationship("Analysis", back_populates="pipeline_runs")


class LogEntry(Base):
    """Structured log entries for pipeline observability."""

    __tablename__ = "log_entries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(GUID(), ForeignKey("analyses.id"), nullable=True, index=True)
    stage = Column(String(100), nullable=True)
    level = Column(String(20), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    extra = Column(Text, nullable=True)  # JSON string for extra data

    analysis = relationship("Analysis", back_populates="log_entries")


class AppSetting(Base):
    """Persistent application settings (key-value store)."""

    __tablename__ = "app_settings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# =====================================================
# EXISTING MODELS — UNCHANGED
# =====================================================

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
    analysis_id = Column(GUID(), ForeignKey("analyses.id"), nullable=True, index=True)
    root_cause = Column(Text, nullable=True)
    exploit_payload = Column(Text, nullable=True)
    suggested_patch = Column(Text, nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    cwe_id = Column(String(50), nullable=True)
    vulnerable_file = Column(String(1024), nullable=True)
    vulnerable_function = Column(String(512), nullable=True)
    affected_lines = Column(Text, nullable=True)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bug_report = relationship("BugReport", back_populates="analysis_results")
    exploit_executions = relationship("ExploitExecution", back_populates="analysis_result")
    scan_results = relationship("ScanResult", back_populates="analysis_result")
    vulnerability_score = relationship("VulnerabilityScore", back_populates="analysis_result", uselist=False)


class Patch(Base):
    """Security patch metadata model."""

    __tablename__ = "patches"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(GUID(), ForeignKey("analyses.id"), nullable=True, index=True)
    cve_id = Column(String(50), nullable=True, index=True)
    cve_ids = Column(Text, nullable=True)  # JSON list
    cvss_score = Column(Float, nullable=True)
    vulnerability_type = Column(String(100), nullable=True)
    affected_versions = Column(Text, nullable=True)  # JSON list
    patch_description = Column(Text, nullable=True)
    patch_url = Column(String(1024), nullable=True)
    patch_content = Column(Text, nullable=True)
    references = Column(Text, nullable=True)  # JSON list
    release_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ExploitExecution(Base):
    """Exploit execution log model."""

    __tablename__ = "exploit_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    exploit_type = Column(String(100), nullable=False)
    exploit_payload = Column(Text, nullable=False)
    execution_status = Column(String(50), nullable=False, default="pending")
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    return_code = Column(Integer, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    vulnerable = Column(Boolean, default=False, nullable=False)
    docker_container_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="exploit_executions")


class ScanResult(Base):
    """Static and dynamic scan results model."""

    __tablename__ = "scan_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    analysis_id = Column(GUID(), ForeignKey("analyses.id"), nullable=True, index=True)
    scan_type = Column(String(50), nullable=False)  # static, dynamic
    scanner_name = Column(String(100), nullable=False)
    finding_count = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    high_count = Column(Integer, default=0, nullable=False)
    medium_count = Column(Integer, default=0, nullable=False)
    low_count = Column(Integer, default=0, nullable=False)
    findings = Column(Text, nullable=True)  # JSON detailed findings
    scan_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="scan_results")


class VulnerabilityScore(Base):
    """Calculated vulnerability score model."""

    __tablename__ = "vulnerability_scores"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, unique=True, index=True)
    analysis_id = Column(GUID(), ForeignKey("analyses.id"), nullable=True, index=True)
    cvss_score = Column(Float, nullable=False)
    cvss_vector = Column(String(255), nullable=True)
    severity = Column(String(20), nullable=False)
    exploitability = Column(Float, nullable=False)
    impact_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    component_breakdown = Column(Text, nullable=True)  # JSON
    recommendations = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="vulnerability_score")


class Report(Base):
    """Generated PDF/HTML report model."""

    __tablename__ = "reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    analysis_id = Column(GUID(), ForeignKey("analyses.id"), nullable=True, index=True)
    report_format = Column(String(20), nullable=False)  # pdf, html, json
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
