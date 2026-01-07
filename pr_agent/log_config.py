"""
Logging configuration for Datadog integration.
Outputs structured JSON logs to stdout for Datadog agent collection.
"""
import json
import logging
import os
import sys
from datetime import datetime


class DatadogJSONFormatter(logging.Formatter):
    """JSON formatter optimized for Datadog log ingestion."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": "pr-agent",
            "env": os.environ.get("ENV", "development"),
            "version": os.environ.get("APP_VERSION", "dev"),
            "dd": {
                "trace_id": getattr(record, "dd_trace_id", None),
                "span_id": getattr(record, "dd_span_id", None),
            },
            "source": {
                "file": record.filename,
                "line": record.lineno,
                "function": record.funcName,
            },
        }
        
        if hasattr(record, "context") and record.context:
            log_record["context"] = record.context
        
        if record.exc_info:
            log_record["error"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stack_trace": self.formatException(record.exc_info),
            }
        
        return json.dumps(log_record, default=str)


def setup_logging(level: str = "INFO") -> None:
    """
    Configure logging for Datadog collection via stdout.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(DatadogJSONFormatter())
    
    logging.basicConfig(
        level=log_level,
        handlers=[handler],
        force=True,
    )
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("litellm").setLevel(logging.WARNING)
    
    logger = logging.getLogger("pr_agent")
    logger.info("Logging configured", extra={"context": {"level": level, "env": os.environ.get("ENV", "development")}})


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that automatically includes context in all log messages."""
    
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        if self.extra:
            context = extra.get("context", {})
            context.update(self.extra)
            extra["context"] = context
        kwargs["extra"] = extra
        return msg, kwargs


def get_context_logger(name: str, **context) -> LoggerAdapter:
    """
    Get a logger with default context attached.
    
    Args:
        name: Logger name
        **context: Default context to include in all log messages
    
    Returns:
        Logger adapter with context
    
    Example:
        logger = get_context_logger(__name__, pr_url="https://...", repo="backend")
        logger.info("Starting review")  # Will include pr_url and repo in context
    """
    return LoggerAdapter(logging.getLogger(name), context)

