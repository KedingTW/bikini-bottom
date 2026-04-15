FROM ghcr.io/openabdev/openab:latest
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
USER agent
