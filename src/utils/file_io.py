"""
File I/O utilities for managing quarantined data.
"""

import json
import os
from datetime import datetime, date, UTC
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)


class QuarantineManager:
    """
    Manages the quarantining of records that fail validation.

    This manager handles the creation of quarantine directories and files,
    and writes failed records in a structured JSON format.
    """

    def __init__(self, enabled: bool = True, base_dir: str = "dlq/validation_failures"):
        """
        Initialize the QuarantineManager.

        Args:
            enabled: If False, quarantine operations will be skipped.
            base_dir: The base directory to store quarantined files.
        """
        self.enabled = enabled
        self.base_dir = Path(base_dir)
        if self.enabled:
            self._ensure_base_dir_exists()

    def _ensure_base_dir_exists(self) -> None:
        """Create the base quarantine directory if it doesn't exist."""
        try:
            self.base_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(
                "Failed to create quarantine directory",
                path=str(self.base_dir),
                error=str(e)
            )
            self.enabled = False  # Disable if we can't create the directory

    def quarantine_record(
        self,
        schema_type: str,
        validation_rule: str,
        error_message: str,
        original_record: Dict[str, Any],
        transformed_record: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Writes a failed record to a quarantine file.

        Args:
            schema_type: The schema of the failed record (e.g., 'ohlcv').
            validation_rule: The name of the validation rule that failed.
            error_message: The error message from the validation failure.
            original_record: The raw record data that failed.
            transformed_record: The transformed record data, if available.
        """
        if not self.enabled:
            return

        now = datetime.now(UTC)
        session_dir = self.base_dir / now.strftime("%Y-%m-%d_%H-%M-%S")
        session_dir.mkdir(exist_ok=True)

        file_path = session_dir / f"{schema_type}_failures.jsonl"

        quarantine_entry = {
            "timestamp": now.isoformat(),
            "schema_type": schema_type,
            "validation_rule": validation_rule,
            "error_message": error_message,
            "original_record": self._serialize_record(original_record),
            "transformed_record": self._serialize_record(transformed_record) if transformed_record else None
        }

        try:
            with file_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(quarantine_entry) + "\n")
        except IOError as e:
            logger.error(
                "Failed to write to quarantine file",
                path=str(file_path),
                error=str(e)
            )

    def _serialize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize a record's values to be JSON-compatible.
        Converts datetime, date, and Decimal objects to strings.
        """
        serialized = {}
        for key, value in record.items():
            if isinstance(value, (datetime, date)):
                serialized[key] = value.isoformat()
            elif isinstance(value, Decimal):
                serialized[key] = str(value)
            else:
                serialized[key] = value
        return serialized
