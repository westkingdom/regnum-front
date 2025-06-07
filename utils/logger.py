import logging
import os
import sys
import json
from datetime import datetime

# Configure logging based on environment
def setup_logger(name=None):
    """
    Configure and return a logger instance with appropriate handlers based on the environment.
    
    In production (Cloud Run), logs are formatted as JSON for Cloud Logging.
    In development, logs are formatted for better readability in the console.
    
    Args:
        name: Optional name for the logger (default: None, uses root logger)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if handlers haven't been set up
    if not logger.handlers:
        logger.setLevel(logging.WARNING)
        
        # Determine if we're running in Cloud Run
        in_cloud_run = os.environ.get('K_SERVICE') is not None
        
        if in_cloud_run:
            # Cloud Run environment - set up JSON structured logging
            handler = logging.StreamHandler(sys.stdout)
            
            class JsonFormatter(logging.Formatter):
                def format(self, record):
                    log_entry = {
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'severity': record.levelname,
                        'message': record.getMessage(),
                        'logger': record.name,
                    }
                    
                    # Add exception info if available
                    if record.exc_info:
                        log_entry['exception'] = self.formatException(record.exc_info)
                    
                    # Add custom fields if available
                    if hasattr(record, 'fields'):
                        for key, value in record.fields.items():
                            log_entry[key] = value
                    
                    return json.dumps(log_entry)
            
            handler.setFormatter(JsonFormatter())
        else:
            # Development environment - human-readable format
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger

# Convenience method to add custom fields to log record
def log_with_fields(logger, level, message, **fields):
    """
    Log a message with additional structured fields.
    
    Args:
        logger: Logger instance to use
        level: Logging level (e.g., logging.INFO)
        message: Log message
        **fields: Additional fields to include in the log entry
    """
    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname='',
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.fields = fields
    
    logger_fn = {
        logging.DEBUG: logger.debug,
        logging.INFO: logger.info,
        logging.WARNING: logger.warning,
        logging.ERROR: logger.error,
        logging.CRITICAL: logger.critical
    }.get(level, logger.info)
    
    logger_fn(message, extra={'fields': fields})

# Create a default app logger
app_logger = setup_logger('regnum') 