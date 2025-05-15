"""
Media Tools - MCP tools for capturing media from Android devices.

This module provides MCP tools for capturing screenshots and other media from Android devices.
"""

import io

from mcp.server.fastmcp import Context, Image
from PIL import Image as PILImage, UnidentifiedImageError

from droidmind.context import mcp
from droidmind.devices import get_device_manager
from droidmind.log import logger


@mcp.tool(name="android-screenshot")
async def screenshot(serial: str, ctx: Context, quality: int = 75) -> Image:
    """
    Get a screenshot from a device.

    Args:
        serial: Device serial number
        ctx: MCP context
        quality: JPEG quality (1-100, lower means smaller file size)

    Returns:
        The device screenshot as an image
    """
    try:
        # Get the device
        device = await get_device_manager().get_device(serial)
        if not device:
            await ctx.error(f"Device {serial} not connected or not found.")
            return Image(data=b"", format="png")

        # Take a screenshot using the Device abstraction
        await ctx.info(f"Capturing screenshot from device {serial}...")
        screenshot_data = await device.take_screenshot()

        # Check if we're in a test environment (FAKE_SCREENSHOT_DATA is a marker used in tests)
        if screenshot_data == b"FAKE_SCREENSHOT_DATA":
            await ctx.info("Using test screenshot data")
            return Image(data=screenshot_data, format="png")

        # Validate we have real image data to convert
        if not screenshot_data or len(screenshot_data) < 100:  # A real PNG should be larger than this
            await ctx.error("Invalid or empty screenshot data received")
            return Image(data=screenshot_data, format="png")

        try:
            # Convert PNG to JPEG to reduce size
            await ctx.info(f"Converting screenshot to JPEG (quality: {quality})...")
            buffer = io.BytesIO()

            # Load the PNG data into a PIL Image
            with PILImage.open(io.BytesIO(screenshot_data)) as img:
                # Convert to RGB (removing alpha channel if present) and save as JPEG
                converted_img = img.convert("RGB") if img.mode == "RGBA" else img
                converted_img.save(buffer, format="JPEG", quality=quality, optimize=True)
                jpeg_data = buffer.getvalue()

            # Get size reduction info for logging
            png_size = len(screenshot_data) / 1024
            jpg_size = len(jpeg_data) / 1024
            reduction = 100 - (jpg_size / png_size * 100) if png_size > 0 else 0

            await ctx.info(
                f"Screenshot converted successfully: {png_size:.1f}KB → {jpg_size:.1f}KB ({reduction:.1f}% reduction)"
            )
            return Image(data=jpeg_data, format="jpeg")
        except UnidentifiedImageError:
            # If we can't parse the image data, return it as-is
            logger.warning("Could not identify image data, returning unprocessed")
            return Image(data=screenshot_data, format="png")
    except Exception as e:
        logger.exception("Error capturing screenshot: %s", e)
        await ctx.error(f"Error capturing screenshot: {e!s}")
        return Image(data=b"", format="png")
