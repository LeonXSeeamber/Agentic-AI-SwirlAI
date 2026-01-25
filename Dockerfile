
# ghcr.io/astral-sh/uv base image with Python 3.13 on Debian Bookworm slim

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Enviromnment variables
# Enable bytecode compilation and Python optimization
ENV UV_COMPILE_BYTECODE=1
ENV PYTHONOPTIMIZE=1
ENV UV_LINK_MODE=copy

# Set Python path to include the src directory for imports
ENV PYTHONPATH="/app/src:$PYTHONPATH"

# What to copy and install
# Copy only dependency files first for better layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package chatbot_ui

# Copy application code
COPY src ./src/

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user and set permissions
RUN addgroup --system app && \
    adduser --system --ingroup app app && \
    chown -R app:app /app && \
    mkdir -p /home/app && \
    chown -R app:app /home/app && \
    mkdir -p /home/app/.streamlit && \
    mkdir -p /home/app/.streamlit/data && \
    mkdir -p /home/app/.streamlit/cache && \
    chown -R app:app /home/app/.streamlit

# Set home directory for the user
ENV HOME=/home/app

# Switch to non-root user
USER app

# Expose the Streamlit port
EXPOSE 8501

# Command to run the application
CMD ["uv", "run", "streamlit", "run", "./src/app.py", "--server.address=0.0.0.0"]