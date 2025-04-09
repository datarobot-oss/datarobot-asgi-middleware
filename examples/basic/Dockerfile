FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Install FastAPI and uvicorn
RUN uv venv && uv pip install fastapi[standard] uvicorn

# Copy the package files
COPY ./README.md /app/
COPY ./pyproject.toml /app/

COPY ./src/ /app/src/

# Install the package in development mode
RUN uv pip install -e .

# Copy the example application
COPY ./examples/basic/main.py /app/

# Expose port 8000
EXPOSE 8000

# Command to run the application
CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
