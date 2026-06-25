# CIFS 掛載與斷線防護指南

**作成：章魚哥（PM）+ 珊迪（技術審查）**
**日期：2026-06-04**
**狀態：✅ 覆核通過，可執行**
**目標讀者：Kiro**

---

## 背景

原架構（Windows + WSL2 + Docker Compose）使用 Docker CIFS volume 掛載共用儲存，瞬斷後容器 hang 死需手動重啟。遷移到 Ubuntu 24.04 + K3s 後，改為 host level mount + hostPath，搭配多層防護確保斷線自動恢復。

## 關鍵決策

| 項目 | 決策 | 原因 |
|------|------|------|
| 協議 | SMB 3.0（mount.cifs vers=3.0） | 公司儲存僅開 Samba，全 Windows 用 net use，無需改設定 |
| 認證 | AD 帳號 credentials file | 入域後用 AD 帳密，不用 Kerberos（簡單優先） |
| 掛載路徑 | `/mnt/kd-dev`、`/mnt/kd-dc`、`/mnt/kd-share` | 依用途區分三組掛載 |
| 容器存取方式 | hostPath volume | deployment yaml 直接用 hostPath |

### 掛載對照

| 掛載路徑 | 遠端路徑 | 讀寫 | 用途 |
|----------|----------|------|------|
| `/mnt/kd-dev` | `//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom` | rw | 比奇堡共用儲存 |
| `/mnt/kd-dc` | `//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/89.KedingDC` | rw | 科定AI 工作區 |
| `/mnt/kd-share` | `//192.168.1.218/KD共用` | ro | 公司全共用區（唯讀） |

---

## 一、Credentials File

```bash
sudo tee /etc/kd-dev-credentials << 'EOF'
username=AD帳號
password=AD密碼
domain=公司AD_Domain
EOF
sudo chmod 600 /etc/kd-dev-credentials
```

---

## 二、Systemd Mount Unit（以 kd-dev 為例）

```ini
# /etc/systemd/system/mnt-kd\x2ddev.mount
[Unit]
Description=KD-DEV Share (BikiniBottom)
After=network-online.target
Wants=network-online.target

[Mount]
What=//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom
Where=/mnt/kd-dev
Type=cifs
Options=credentials=/etc/kd-dev-credentials,soft,echo_interval=10,vers=3.0,iocharset=utf8,file_mode=0777,dir_mode=0777,_netdev
TimeoutSec=30

[Install]
WantedBy=multi-user.target
```

---

## 三、Systemd Automount Unit

```ini
# /etc/systemd/system/mnt-kd\x2ddev.automount
[Unit]
Description=Automount KD-DEV Share

[Automount]
Where=/mnt/kd-dev
TimeoutIdleSec=0

[Install]
WantedBy=multi-user.target
```

---

## 四、啟用掛載

```bash
sudo mkdir -p /mnt/kd-dev
sudo systemctl daemon-reload
sudo systemctl enable mnt-kd\\x2ddev.automount
sudo systemctl start mnt-kd\\x2ddev.automount
```

⚠️ **不要 enable mount unit**，只 enable automount。Mount 由 automount 按需觸發。

---

## 五、Watchdog

### 5.1 腳本

```bash
sudo tee /usr/local/bin/kd-dev-watchdog.sh << 'EOF'
#!/bin/bash
MOUNT_POINT="/mnt/kd-dev"
SYSTEMD_UNIT="mnt-kd\\x2ddev.mount"

if ! stat "$MOUNT_POINT/." &>/dev/null; then
    logger -t kd-dev-watchdog "kd-dev unreachable, attempting remount"
    systemctl restart "$SYSTEMD_UNIT"
    sleep 5
    if stat "$MOUNT_POINT/." &>/dev/null; then
        logger -t kd-dev-watchdog "kd-dev remount successful"
    else
        logger -t kd-dev-watchdog "kd-dev remount FAILED - will retry next cycle"
    fi
fi
EOF
sudo chmod +x /usr/local/bin/kd-dev-watchdog.sh
```

### 5.2 Timer

```ini
# /etc/systemd/system/kd-dev-watchdog.service
[Unit]
Description=KD-DEV Health Check

[Service]
Type=oneshot
ExecStart=/usr/local/bin/kd-dev-watchdog.sh
```

```ini
# /etc/systemd/system/kd-dev-watchdog.timer
[Unit]
Description=KD-DEV Health Check Timer

[Timer]
OnBootSec=60
OnUnitActiveSec=30

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kd-dev-watchdog.timer
```

---

## 六、K3s Pod livenessProbe

在每個 agent deployment 的 container spec 加入：

```yaml
livenessProbe:
  exec:
    command:
      - stat
      - /mnt/kd-dev/.
  initialDelaySeconds: 30
  periodSeconds: 15
  failureThreshold: 3
readinessProbe:
  exec:
    command:
      - stat
      - /mnt/kd-dev/.
  periodSeconds: 10
  failureThreshold: 2
```

---

## 七、防護鏈

```
共用儲存瞬斷
  │
  ├─ soft mount（預設）→ I/O 返回錯誤不 hang → 容器不卡死
  │
  ├─ echo_interval=10 → 30 秒後 kernel 偵測斷線
  │   └─ watchdog stat → 觸發 I/O → kernel 嘗試 reconnect
  │       ├─ 成功 → 透明恢復
  │       └─ 失敗 → watchdog systemctl restart → 強制重掛
  │
  └─ > 45 秒仍未恢復
      └─ K3s livenessProbe 失敗 → Pod 重啟
          └─ automount 觸發 → 重新掛載 → 恢復
```

---

## 八、Mount Options 核實

| 參數 | 說明 | 核實來源 |
|------|------|---------|
| `soft` | I/O 失敗返回錯誤不 hang（CIFS 預設值，顯式寫明） | mount.cifs(8) man page |
| `echo_interval=10` | keep-alive 間隔，reconnect = 3×10 = 30 秒 | mount.cifs(8) man page |
| `vers=3.0` | SMB 3.0 協議（非古老的 SMB1/CIFS） | mount.cifs(8) man page |
| `_netdev` | 等網路就緒後掛載 | systemd/fstab 標準做法 |

**注意：`retry` 不是 mount.cifs 的有效選項（那是 NFS 的），不要使用。**

---

## 九、Checklist

| # | 項目 | 確認指令 |
|---|------|---------|
| 1 | Ubuntu 24.04 就緒 | `lsb_release -a` |
| 2 | AD 入域成功 | `realm list` |
| 3 | credentials file | `ls -la /etc/kd-dev-credentials` → 600 |
| 4 | 手動 mount 測試 | `sudo mount -t cifs -o credentials=/etc/kd-dev-credentials,vers=3.0 "//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom" /mnt/kd-dev && ls /mnt/kd-dev` |
| 5 | automount 啟用 | `systemctl status mnt-kd\\x2ddev.automount` → active |
| 6 | automount 測試 | `sudo umount /mnt/kd-dev && ls /mnt/kd-dev`（應自動掛回） |
| 7 | watchdog 運作 | `systemctl status kd-dev-watchdog.timer` → active |
| 8 | K3s ready | `sudo kubectl get nodes` → Ready |
| 9 | Pods running | `sudo kubectl get pods -n bikini-bottom` |
| 10 | **斷線模擬** | `sudo iptables -A OUTPUT -d 192.168.1.218 -j DROP` |
| 11 | **恢復確認** | `sudo iptables -D OUTPUT -d 192.168.1.218 -j DROP` → Pod 自動恢復 |

---

## 十、注意事項

- Unit 檔名必須對應路徑：`/mnt/kd-dev` → `mnt-kd\x2ddev.mount` / `mnt-kd\x2ddev.automount`
- AD 密碼變更時更新 credentials file，然後 `systemctl restart mnt-kd\x2ddev.mount`
- 儲存 IP 變更時修改 mount unit 的 `What=`，`systemctl daemon-reload`
- deployment yaml 已用 hostPath 指向 `/mnt/kd-dev`，無需修改
