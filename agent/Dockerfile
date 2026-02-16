# Dockerfile
# Build args:
#   --build-arg WITH_LOCAL_INFERENCE=true  → includes cmake + llama.cpp build tools
#   (default)                              → lean image for API-only mode

ARG WITH_LOCAL_INFERENCE=false
FROM python:3.9-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install llama.cpp build dependencies only when requested
ARG WITH_LOCAL_INFERENCE
RUN if [ "$WITH_LOCAL_INFERENCE" = "true" ]; then \
    apt-get update && apt-get install -y \
      cmake \
      g++ \
      make \
    && rm -rf /var/lib/apt/lists/*; \
  fi

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a directory for the persistent database
RUN mkdir -p /data

# When running with local inference, pre-build llama.cpp at image build time
# (requires GGUF model to be volume-mounted at runtime)
RUN if [ "$WITH_LOCAL_INFERENCE" = "true" ] && [ -f local_inference/setup_llama_cpp.sh ]; then \
    cd local_inference && chmod +x setup_llama_cpp.sh && ./setup_llama_cpp.sh; \
  fi

# Command to run the application
CMD ["python", "run_pipeline.py"]
