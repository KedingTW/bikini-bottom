# 比奇堡團隊 — Agent Image
# 含 git、gh CLI、pandoc、Python 文件生成套件
# entrypoint: entrypoint-bikini-bottom.sh（NAS symlink + shared steering/skills + 降權）

FROM ghcr.io/openabdev/openab:0.8.4
USER root

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# GitHub CLI — Agent 開 PR、管理 PR 用
RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
      -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
      > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# 文件生成用 Python 套件（xlsx, pdf, pptx, docx skills）
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip pandoc \
    && pip3 install --no-cache-dir --break-system-packages \
        openpyxl pandas xlsxwriter \
        pypdf reportlab \
        python-pptx \
        python-docx \
        markitdown \
    && rm -rf /var/lib/apt/lists/*

# Entrypoint scripts
COPY scripts/bikini-bottom/link-shared-steering.sh /usr/local/bin/link-shared-steering.sh
COPY scripts/bikini-bottom/link-shared-skills.sh /usr/local/bin/link-shared-skills.sh
COPY scripts/bikini-bottom/entrypoint.sh /usr/local/bin/entrypoint-bikini-bottom.sh
RUN chmod +x /usr/local/bin/link-shared-steering.sh /usr/local/bin/link-shared-skills.sh /usr/local/bin/entrypoint-bikini-bottom.sh

# 預建 /nas 目錄
RUN mkdir -p /nas

ENTRYPOINT ["/usr/local/bin/entrypoint-bikini-bottom.sh"]
