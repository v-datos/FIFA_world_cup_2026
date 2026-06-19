# Stage 1: Build the React frontend
FROM node:20 AS frontend-builder
WORKDIR /build/src/frontend
COPY src/frontend/package*.json ./
RUN npm install
COPY src/frontend/ ./
# teamIdentity.ts imports the repo-canonical contract via ../../../../data/...,
# so the data file must keep its position relative to src/frontend in the build.
COPY data/reference/team_identity.json /build/data/reference/team_identity.json
RUN npm run build

# Stage 2: Build the Python backend and assemble
FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app

# Install system dependencies, including curl for healthchecks/live API requests
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python backend code
COPY . .

# Copy built React frontend files to FastAPI static folder
COPY --from=frontend-builder /build/src/frontend/dist /app/src/api/static

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8080

ENTRYPOINT ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
