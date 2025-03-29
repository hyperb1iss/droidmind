import logging
from logging import FileHandler, Handler, NullHandler, StreamHandler
import os

logger = logging.getLogger("droidmind")


def setup_logging(
    log_level: str,
    debug: bool,
    handler: Handler | None = None,
    log_file: str | None = None,
    disable_console_logging: bool = False,
) -> None:
    """Configure logging for the application.

    Args:
        log_level: The logging level to use
        debug: Whether debug mode is enabled
        handler: The RichHandler to use for logging (optional)
        log_file: Path to a file to log to (optional)
        disable_console_logging: If True, suppress all console output (for stdio mode)
    """
    # Determine handlers to use
    handlers: list[Handler] = []

    if log_file:
        # Create directory for log file if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create file handler
        file_handler = FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        handlers.append(file_handler)

    if handler and not disable_console_logging:
        handlers.append(handler)

    # If no handlers specified, use a basic stream handler as fallback
    # BUT only if not explicitly disabled
    if not handlers and not disable_console_logging:
        stream_handler = StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        )
        handlers.append(stream_handler)

    # If we need to suppress all console logging and have no file handler,
    # use a NullHandler to avoid "No handlers could be found" warnings
    if disable_console_logging and not handlers:
        handlers.append(NullHandler())

    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, str(log_level)),
        format="%(message)s"
        if handler and not disable_console_logging
        else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="[%X]" if handler and not disable_console_logging else "%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )

    # Configure our logger
    logger.setLevel(logging.DEBUG if debug else getattr(logging, log_level))
    logger.handlers = handlers
    logger.propagate = False

    # Also configure Uvicorn loggers
    for uv_logger in ["uvicorn", "uvicorn.access", "uvicorn.error", "asyncio"]:
        uvicorn_logger = logging.getLogger(uv_logger)
        uvicorn_logger.handlers = handlers
        uvicorn_logger.propagate = False

    # Set higher log level for protocol-level logs
    logging.getLogger("mcp.server.sse").setLevel(logging.INFO)
    logging.getLogger("mcp.server.stdio").setLevel(logging.INFO)
    logging.getLogger("mcp.server.fastmcp").setLevel(logging.INFO)
    logging.getLogger("starlette").setLevel(logging.INFO)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("asyncio").setLevel(logging.INFO if not debug else logging.DEBUG)
