#!/bin/bash
# Wrapper entrypoint: 建立共用 steering symlink 後啟動 OpenAB

/usr/local/bin/link-shared-steering.sh

# 執行原始 entrypoint（openab）
exec openab "$@"
