from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class VulnerabilityType(str, Enum):
    BUFFER_OVERFLOW = "buffer_overflow"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    AUTH_BYPASS = "auth_bypass"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    OTHER = "other"

class AnalysisResult(BaseModel):
    id: str
    project_id: str
    file_path: str
    language: str
    vulnerability_type: VulnerabilityType
    severity: Severity
    description: str
    line_number: Optional[int]
    code_snippet: Optional[str]
    recommendation: str
    confidence_score: float
    detection_method: str  # "llm", "static", or "hybrid"
    created_at: datetime
    metadata: Optional[Dict] = {}

class ProjectAnalysis(BaseModel):
    project_id: str
    project_name: str
    total_files: int
    analyzed_files: int
    vulnerabilities_found: int
    analysis_start_time: datetime
    analysis_end_time: Optional[datetime]
    results: List[AnalysisResult]
    summary: Dict[str, int]  # Count of vulnerabilities by severity
    status: str  # "running", "completed", "failed"
    error_message: Optional[str] = None 