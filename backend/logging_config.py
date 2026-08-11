"""
Centralized logging setup. Import configure_logging() once from main.py.

Local dev: human-readable lines to stdout.
Production (ENV=production): still stdout (never write app logs to a local
file in a container — the platform's log collector is the source of truth
on Render/Railway/Docker), but with request-id-friendly formatting.
"""
import logging
import os
import sys


def configure_logging():
    env = os.getenv("ENV", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO" if env == "production" else "DEBUG")

    handler = logging.StreamHandler(sys.stdout)
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    handler.setFormatter(logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S"))

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(log_level)

    # Quiet noisy third-party loggers down to WARNING so real signal isn't buried
    for noisy in ("uvicorn.access", "passlib", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("finguard").info(f"Logging configured — env={env}, level={log_level}")


logger = logging.getLogger("finguard")
