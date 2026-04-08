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
    repository_url = Column(String(1024), nullable=False)
    vulnerability_type = Column(String(100), nullable=False)
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
    environment_type = Column(String(100), nullable=True)  # python, nodejs, php, java
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    bug_report = relationship("BugReport", back_populates="analysis_results")
    exploit_executions = relationship("ExploitExecution", back_populates="analysis_result")
    scan_results = relationship("ScanResult", back_populates="analysis_result")
    vulnerability_score = relationship("VulnerabilityScore", back_populates="analysis_result", uselist=False)
    payload_results = relationship("PayloadResult", back_populates="analysis_result")
    ollama_prompts = relationship("OllamaPrompt", back_populates="analysis_result")
    docker_logs = relationship("DockerLog", back_populates="analysis_result")
    backend_stage_logs = relationship("BackendStageLog", back_populates="analysis_result")
    dynamic_scan_logs = relationship("DynamicScanLog", back_populates="analysis_result")


class Patch(Base):
    """Security patch metadata model."""

    __tablename__ = "patches"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    cve_id = Column(String(50), nullable=False, unique=True, index=True)
    vulnerability_type = Column(String(100), nullable=False)
    affected_versions = Column(Text, nullable=False)  # JSON list
    patch_url = Column(String(1024), nullable=True)
    patch_content = Column(Text, nullable=True)
    release_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ExploitExecution(Base):
    """Exploit execution log model."""

    __tablename__ = "exploit_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    exploit_type = Column(String(100), nullable=False)  # SQL_INJECTION, XSS, COMMAND_INJECTION, etc.
    exploit_payload = Column(Text, nullable=False)
    execution_status = Column(String(50), nullable=False, default="pending")  # pending, running, success, failed
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
    scan_type = Column(String(50), nullable=False)  # static, dynamic, sast, dast
    scanner_name = Column(String(100), nullable=False)
    finding_count = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    high_count = Column(Integer, default=0, nullable=False)
    medium_count = Column(Integer, default=0, nullable=False)
    low_count = Column(Integer, default=0, nullable=False)
    scan_output = Column(Text, nullable=True)  # Raw scanner output
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="scan_results")


class VulnerabilityScore(Base):
    """Calculated vulnerability score model."""

    __tablename__ = "vulnerability_scores"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, unique=True, index=True)
    cvss_score = Column(Float, nullable=False)  # 0.0 - 10.0
    cvss_vector = Column(String(255), nullable=True)
    severity = Column(String(20), nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    exploitability = Column(Float, nullable=False)  # 0.0 - 1.0
    impact_score = Column(Float, nullable=False)  # 0.0 - 1.0
    confidence = Column(Float, nullable=False)  # 0.0 - 1.0
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="vulnerability_score")


class Report(Base):
    """Generated PDF/HTML report model."""

    __tablename__ = "reports"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, unique=True, index=True)
    report_format = Column(String(20), nullable=False)  # pdf, html, json
    file_path = Column(String(1024), nullable=False)
    file_size = Column(Integer, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LogEntry(Base):
    """Log entry model for pipeline execution tracking."""

    __tablename__ = "log_entries"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=True, index=True)
    stage = Column(String(100), nullable=False)
    level = Column(String(20), nullable=False, default="INFO")
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    extra = Column(Text, nullable=True)


class AppSetting(Base):
    """Application settings model."""

    __tablename__ = "app_settings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)


class Analysis(Base):
    """Analysis model."""

    __tablename__ = "analyses"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# ======================================================================
# NEW MODELS — Admin observability tables
# ======================================================================

class PayloadResult(Base):
    """Individual payload execution result — visible in dashboard."""

    __tablename__ = "payload_results"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    payload_id = Column(String(100), nullable=False)         # e.g. sql_basic_01
    payload_type = Column(String(100), nullable=False)        # e.g. SQL_INJECTION
    payload_category = Column(String(100), nullable=False)    # e.g. basic_or_injection
    payload_string = Column(Text, nullable=False)             # the actual payload text
    execution_status = Column(String(50), nullable=False, default="pending")
    response_output = Column(Text, nullable=True)
    exploit_success = Column(Boolean, default=False, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="payload_results")


class OllamaPrompt(Base):
    """Stores all Ollama-generated prompts for admin visibility."""

    __tablename__ = "ollama_prompts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    prompt_type = Column(String(100), nullable=False)         # environment, analysis, etc.
    prompt_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    generated_time = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="ollama_prompts")


class DockerLog(Base):
    """Docker container execution logs."""

    __tablename__ = "docker_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    container_id = Column(String(255), nullable=True)
    log_output = Column(Text, nullable=True)
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    exit_code = Column(Integer, nullable=True)
    execution_time = Column(Integer, nullable=True)   # ms
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="docker_logs")


class BackendStageLog(Base):
    """Pipeline stage execution tracking for admin panel."""

    __tablename__ = "backend_stage_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    stage_name = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, default="pending")   # pending, running, completed, failed
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    output_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="backend_stage_logs")


class DynamicScanLog(Base):
    """Repository change detection and dynamic scan tracking."""

    __tablename__ = "dynamic_scan_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    analysis_result_id = Column(GUID(), ForeignKey("analysis_results.id"), nullable=False, index=True)
    repo_url = Column(String(1024), nullable=False)
    change_detected = Column(Boolean, default=False, nullable=False)
    change_log = Column(Text, nullable=True)
    scan_status = Column(String(50), nullable=False, default="idle")  # idle, scanning, completed
    scan_output = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="dynamic_scan_logs")
