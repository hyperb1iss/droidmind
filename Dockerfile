FROM python:3.13-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set up the application directory
WORKDIR /app

# Create virtual environment and install uv
RUN python -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:${PATH}"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

# Copy dependency metadata and sync from lockfile
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --active --no-install-project

# Copy the application code and install the project (deps already installed)
COPY droidmind ./droidmind
COPY README.md ./
COPY LICENSE ./
RUN pip install --no-cache-dir --no-deps .

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

# Ensure the DroidMind CLI is accessible
ENV PATH="/opt/venv/bin:${PATH}"

# Default port (still useful if user switches to SSE)
EXPOSE 4256

# Use the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]

# Default command to run the server (will be processed by entrypoint.sh)
# Now defaults to stdio via the entrypoint script logic
CMD ["droidmind"] 
