import logging
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app_paths import ensure_runtime_dirs, logs_dir


LOG_FILE_NAME = "valorant_tracker.log"
MAX_LOG_BYTES = 1_000_000
BACKUP_COUNT = 5

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(authorization['\"]?\s*[:=]\s*['\"]?)(bearer|basic)\s+[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(x-riot-entitlements-jwt['\"]?\s*[:=]\s*['\"]?)[A-Za-z0-9._~+/=-]+"),
    re.compile(r"(?i)(accessToken\s*['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+"),
    re.compile(r"(?i)(entitlements[_-]?token\s*['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+"),
    re.compile(r"(?i)(password\s*['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+"),
    re.compile(r"(?i)(api[_-]?key\s*['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),
]


def redact_text(value: Any) -> str:
    """
    Returns a log-safe string with known secrets redacted.
    """
    text = str(value)
    for pattern in SENSITIVE_PATTERNS:
        text = pattern.sub(lambda match: f"{match.group(1)}<redacted>" if match.groups() else "<redacted>", text)
    return text


class SensitiveDataFilter(logging.Filter):
    """
    Redacts secrets from formatted log records before handlers write them.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact_text(record.getMessage())
        record.args = ()
        return True


def log_path() -> Path:
    """
    Returns the application log file path.
    """
    return logs_dir() / LOG_FILE_NAME


def configure_logging(debug: bool = False) -> Path:
    """
    Configures application logging to the per-user logs directory.
    """
    ensure_runtime_dirs()
    path = log_path()
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)
    redaction_filter = SensitiveDataFilter()
    root_logger.addFilter(redaction_filter)
    for handler in root_logger.handlers:
        handler.addFilter(redaction_filter)

    existing_file_handler = next(
        (
            handler
            for handler in root_logger.handlers
            if isinstance(handler, RotatingFileHandler)
            and getattr(handler, "baseFilename", "") == str(path)
        ),
        None,
    )
    if existing_file_handler:
        existing_file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        return path

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        path,
        maxBytes=MAX_LOG_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(redaction_filter)
    root_logger.addHandler(file_handler)

    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "httpx"]:
        logging.getLogger(logger_name).addFilter(redaction_filter)

    return path


def get_logger(name: str) -> logging.Logger:
    """
    Returns an application logger.
    """
    return logging.getLogger(name)
