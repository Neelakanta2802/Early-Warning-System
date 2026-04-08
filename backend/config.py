"""
Configuration settings for the Early Warning System backend.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Literal
from pathlib import Path

# Absolute path to .env — resolves correctly regardless of CWD
_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Supabase Configuration
    supabase_url: str
    supabase_key: str
    supabase_anon_key: str = ""  # Optional: Defined but not currently used in code
    
    # Database Configuration
    database_url: str = ""
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_reload: bool = True

    @field_validator("api_host", mode="before")
    @classmethod
    def _strip_api_host(cls, v):
        # Be resilient to accidental whitespace/quotes in .env (common on Windows edits),
        # e.g. "'127.0.0.1'" or " 127.0.0.1 ".
        if isinstance(v, str):
            s = v.strip()
            if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                s = s[1:-1].strip()
            return s
        return v

    @field_validator("api_port", mode="before")
    @classmethod
    def _strip_api_port(cls, v):
        # Be resilient to accidental whitespace in .env (common on Windows edits),
        # e.g. "8003 " which would otherwise fail int parsing.
        if isinstance(v, str):
            return v.strip()
        return v
    
    # ML Model Configuration
    model_type: Literal[
        "random_forest", "logistic_regression", "gradient_boosting", "hybrid",
        "xgboost", "lightgbm", "catboost", "neural_network", "ensemble"
    ] = "xgboost"  # Default to most powerful model
    model_version: str = "2.0"
    
    # Risk Thresholds (0-100 scale)
    risk_threshold_low: int = 30
    risk_threshold_medium: int = 60
    risk_threshold_high: int = 80
    
    # Attendance Thresholds (percentage)
    attendance_threshold_warning: float = 75.0
    attendance_threshold_critical: float = 60.0
    
    # GPA Thresholds (0-4.0 scale)
    gpa_threshold_warning: float = 2.5
    gpa_threshold_critical: float = 2.0
    
    # Monitoring Configuration
    monitoring_interval_minutes: int = 60
    alert_cooldown_hours: int = 24
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = str(_ENV_FILE)
        case_sensitive = False
        protected_namespaces = ('settings_',)


# Global settings instance
settings = Settings()
