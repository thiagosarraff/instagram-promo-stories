"""Structured logging for affiliate conversions"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


class StructuredLogger:
    """Logger with JSON-formatted structured output"""

    def __init__(self, name: str, log_file: str = 'logs/affiliate_conversions.log'):
        self.logger = logging.getLogger(name)

        # Try to create file handler, fallback to console-only if permission denied
        try:
            # Ensure logs directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Create file handler with JSON formatter
            handler = logging.FileHandler(log_file)
            handler.setFormatter(self._create_json_formatter())
            self.logger.addHandler(handler)
        except (PermissionError, OSError) as e:
            # Fallback: log to console only in production
            print(f"Warning: Could not create log file {log_file}: {e}")
            print("Falling back to console-only logging")

        # Always add console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)

    def _create_json_formatter(self):
        """Create JSON formatter for structured logging"""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                from datetime import timezone
                log_data = {
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'level': record.levelname,
                    'message': record.getMessage(),
                    'module': record.module,
                }
                # Add extra fields if present
                if hasattr(record, 'extra_data'):
                    log_data.update(record.extra_data)
                return json.dumps(log_data)

        return JsonFormatter()

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str):
        """Log error message"""
        self.logger.error(message)

    def log_conversion(
        self,
        marketplace: str,
        original_link: str,
        converted_link: Optional[str],
        status: str,
        error: Optional[str] = None
    ):
        """
        Log affiliate link conversion attempt

        Args:
            marketplace: Name of the marketplace (e.g., 'mercadolivre', 'amazon')
            original_link: Original product link
            converted_link: Converted affiliate link (None if failed)
            status: Conversion status ('success', 'fallback', 'error')
            error: Error message if conversion failed
        """
        extra_data = {
            'marketplace': marketplace,
            'original_link': original_link,
            'converted_link': converted_link,
            'status': status,
            'error': error
        }

        # Create a log record with extra data
        if status == 'success':
            self.logger.info(
                f'Conversion successful for {marketplace}',
                extra={'extra_data': extra_data}
            )
        elif status == 'fallback':
            self.logger.warning(
                f'Conversion failed for {marketplace}, using fallback',
                extra={'extra_data': extra_data}
            )
        else:
            self.logger.error(
                f'Conversion error for {marketplace}',
                extra={'extra_data': extra_data}
            )


# Global logger instance
affiliate_logger = StructuredLogger('affiliate_conversion')
