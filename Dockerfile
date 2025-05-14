FROM python:3.13-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set up the application directory
WORKDIR /app

# Copy essential files for dependency installation
COPY pyproject.toml ./
COPY LICENSE ./
COPY README.md ./

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .[sse]

# Final stage
FROM python:3.13-slim-bookworm

# Install runtime dependencies: adb and procps (for 'ps' command often used with adb)
RUN apt-get update && \
    apt-get install -y --no-install-recommends android-sdk-platform-tools procps && \
    rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code and entrypoint script
WORKDIR /app
COPY droidmind ./droidmind
COPY README.md ./
COPY LICENSE ./
COPY entrypoint.sh ./

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Ensure the DroidMind CLI is accessible and scripts are executable
ENV PATH="/opt/venv/bin:/app/.venv/bin:${PATH}"

# Default port (still useful if user switches to SSE)
EXPOSE 4256

# Use the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]

# Default command to run the server (will be processed by entrypoint.sh)
# Now defaults to stdio via the entrypoint script logic
CMD ["droidmind"] 