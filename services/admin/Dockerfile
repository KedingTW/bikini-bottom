# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Python backend + serve dist
FROM python:3.12-slim

# Deploy 頁面需要的 CLI 工具：git（讀分支/pull）、docker（build image）、
# kubectl（rollout restart）、k3s（ctr images import）
ARG KUBECTL_VERSION=v1.30.0
ARG K3S_VERSION=v1.30.4+k3s1
ARG DOCKER_VERSION=24.0.7
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl ca-certificates \
    && curl -fsSL "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" \
        -o /usr/local/bin/kubectl && chmod +x /usr/local/bin/kubectl \
    && curl -fsSL "https://github.com/k3s-io/k3s/releases/download/${K3S_VERSION}/k3s" \
        -o /usr/local/bin/k3s && chmod +x /usr/local/bin/k3s \
    && curl -fsSL "https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz" \
        | tar -xz -C /tmp && mv /tmp/docker/docker /usr/local/bin/docker \
        && rm -rf /tmp/docker \
    && rm -rf /var/lib/apt/lists/* \
    && git config --system --add safe.directory /data/repo

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend-build /dist /app/dist

EXPOSE 8501
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8501"]
