FROM ghcr.io/openabdev/openab:latest
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
# GitHub CLI — Agent 開 PR、管理 PR 用
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# 解決 kiro-cli 2.2.0+ 不繼承容器環境變數的問題
# 在容器啟動時，entrypoint 會將環境變數寫入 .bashrc
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER agent
ENTRYPOINT ["tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["openab", "run"]
