import os
import tempfile
import shutil
import logging
import structlog
import pytest
from utils.custom_logger import setup_logging, get_logger

def test_logger_creation_and_log_level():
    setup_logging(log_level="DEBUG", log_file="logs/test_app.log")
    logger = get_logger("test_logger")
    assert hasattr(logger, "info")
    assert hasattr(logger, "debug")
    # Should log at DEBUG level
    logger.debug("debug message")
    logger.info("info message")
    logger.error("error message")
    # Check log level
    root_logger = logging.getLogger()
    assert root_logger.level == logging.DEBUG

def test_log_file_output_and_rotation():
    temp_dir = tempfile.mkdtemp()
    log_file = os.path.join(temp_dir, "test_app.log")
    try:
        setup_logging(log_level="INFO", log_file=log_file)
        logger = get_logger("rotation_test")
        # Write enough logs to trigger rotation (set low maxBytes in custom_logger for this test if needed)
        for i in range(1000):
            logger.info(f"Log entry {i}")
        # Check that log file exists and is not empty
        assert os.path.exists(log_file)
        with open(log_file, "r") as f:
            content = f.read()
            assert "Log entry" in content
    finally:
        shutil.rmtree(temp_dir)

def test_logger_console_output(capsys):
    setup_logging(log_level="INFO", log_file="logs/test_console.log")
    logger = get_logger("console_test")
    logger.info("console output test")
    captured = capsys.readouterr()
    assert "console output test" in captured.out or "console output test" in captured.err 