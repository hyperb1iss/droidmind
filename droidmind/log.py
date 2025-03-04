import logging
from logging import Handler

logger = logging.getLogger("droidmind")


def setup_logging(log_level: str, debug: bool, handler: Handler) -> None:
    """Configure logging for the application.

    Args:
        log_level: The logging level to use
        debug: Whether debug mode is enabled
        handler: The RichHandler to use for logging
    """
    logging.basicConfig(
        level=getattr(logging, str(log_level)),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[handler],
        force=True,
    )
    logger.setLevel(logging.DEBUG if debug else getattr(logging, log_level))
    logger.handlers = [handler]
    logger.propagate = False

    # Also configure Uvicorn loggers with our custom handler
    for uv_logger in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        uvicorn_logger = logging.getLogger(uv_logger)
        uvicorn_logger.handlers = [handler]
        uvicorn_logger.propagate = False

    # Set higher log level for protocol-level logs
    logging.getLogger("mcp.server.sse").setLevel(logging.INFO)
    logging.getLogger("mcp.server.stdio").setLevel(logging.INFO)
    logging.getLogger("mcp.server.fastmcp").setLevel(logging.INFO)
    logging.getLogger("starlette").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
