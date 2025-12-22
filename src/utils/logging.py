import logging
import sys
from pathlib import Path

def setup_logging(verbose: bool = False, log_file: str = None):
    """Configure logging for the scanner"""
    level = logging.DEBUG if verbose else logging.INFO

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except PermissionError:
            logger.warning(f"Cannot write to {log_file} (permission denied). "
                          f"Try using --log-file ~/scanner.log or run with sudo.")
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")

    return logger

