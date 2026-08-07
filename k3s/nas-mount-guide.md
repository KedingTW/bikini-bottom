# KD共用 掛載與斷線防護指南

**作成：章魚哥（PM）+ 珊迪（技術審查）**
**最後更新：2026-08-03**
**狀態：✅ 覆核通過**
**目標讀者：Kiro**

---

## 背景

原架構使用單一 `/mnt/nas` 掛載 `88.BikiniBottom`。現已改為三組獨立掛載，分離比奇堡、科定AI、以及 KD共用 頂層瀏覽需求。

## 掛載總覽

| 掛載點 | 來源路徑 | 權限 | systemd unit |
|--------|----------|------|-------------|
| `/mnt/kd-share` | `//192.168.1.218/KD共用` | ro（唯讀） | `mnt-kd\\x2dshare.mount` |
| `/mnt/kd-dev` | `//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom` | rw | `mnt-kd\\x2ddev.mount` |
| `/mnt/kd-dc` | `//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/89.KedingDC` | rw | `mnt-kd\\x2ddc.mount` |

共用 mount options：`vers=3.0,soft,echo_interval=10,iocharset=utf8,_netdev,x-systemd.automount`

## 關鍵決策

| 項目 | 決策 | 原因 |
|------|------|------|
| 協議 | SMB 3.0（mount.cifs vers=3.0） | 公司僅開 Samba |
| 認證 | AD 帳號 credentials file | 入域後用 AD 帳密 |
| 容器存取方式 | hostPath（不再用 PV/PVC） | 簡化管理，與 keding-dc 一致 |
| kd-share 唯讀 | ro | 僅供查閱，避免誤寫 |

---

## 一、Credentials File

```bash
sudo tee /etc/kd-credentials << 'EOF'
username=AD帳號
password=AD密碼
domain=公司AD_Domain
EOF
sudo chmod 600 /etc/kd-credentials
```

---

## 二、Systemd Mount Units

### /mnt/kd-share（KD共用頂層，唯讀）

```ini
# /etc/systemd/system/mnt-kd\x2dshare.mount
[Unit]
Description=KD Share (Top Level, Read-Only)
After=network-online.target
Wants=network-online.target

[Mount]
What=//192.168.1.218/KD共用
Where=/mnt/kd-share
Type=cifs
Options=credentials=/etc/kd-credentials,ro,soft,echo_interval=10,vers=3.0,iocharset=utf8,file_mode=0755,dir_mode=0755,_netdev
TimeoutSec=30

[Install]
WantedBy=multi-user.target
```

### /mnt/kd-dev（比奇堡，讀寫）

```ini
# /etc/systemd/system/mnt-kd\x2ddev.mount
[Unit]
Description=KD Dev (BikiniBottom)
After=network-online.target
Wants=network-online.target

[Mount]
What=//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom
Where=/mnt/kd-dev
Type=cifs
Options=credentials=/etc/kd-credentials,soft,echo_interval=10,vers=3.0,iocharset=utf8,file_mode=0777,dir_mode=0777,_netdev
TimeoutSec=30

[Install]
WantedBy=multi-user.target
```

### /mnt/kd-dc（科定AI，讀寫）

```ini
# /etc/systemd/system/mnt-kd\x2ddc.mount
[Unit]
Description=KD DC (KedingDC)
After=network-online.target
Wants=network-online.target

[Mount]
What=//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/89.KedingDC
Where=/mnt/kd-dc
Type=cifs
Options=credentials=/etc/kd-credentials,soft,echo_interval=10,vers=3.0,iocharset=utf8,file_mode=0777,dir_mode=0777,_netdev
TimeoutSec=30

[Install]
WantedBy=multi-user.target
```

---

## 三、Systemd Automount Units

每個 mount 對應一個 automount：

```ini
# /etc/systemd/system/mnt-kd\x2dshare.automount
[Unit]
Description=Automount KD Share

[Automount]
Where=/mnt/kd-share
TimeoutIdleSec=0

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/mnt-kd\x2ddev.automount
[Unit]
Description=Automount KD Dev

[Automount]
Where=/mnt/kd-dev
TimeoutIdleSec=0

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/mnt-kd\x2ddc.automount
[Unit]
Description=Automount KD DC

[Automount]
Where=/mnt/kd-dc
TimeoutIdleSec=0

[Install]
WantedBy=multi-user.target
```

---

## 四、啟用掛載

```bash
sudo mkdir -p /mnt/kd-share /mnt/kd-dev /mnt/kd-dc
sudo systemctl daemon-reload
sudo systemctl enable mnt-kd\\x2dshare.automount
sudo systemctl enable mnt-kd\\x2ddev.automount
sudo systemctl enable mnt-kd\\x2ddc.automount
sudo systemctl start mnt-kd\\x2dshare.automount
sudo systemctl start mnt-kd\\x2ddev.automount
sudo systemctl start mnt-kd\\x2ddc.automount
```

⚠️ **不要 enable `.mount`**，只 enable automount。

---

## 五、Watchdog

### 5.1 腳本

```bash
sudo tee /usr/local/bin/kd-mount-watchdog.sh << 'EOF'
#!/bin/bash
MOUNTS=("/mnt/kd-share" "/mnt/kd-dev" "/mnt/kd-dc")
UNITS=("mnt-kd\\x2dshare.mount" "mnt-kd\\x2ddev.mount" "mnt-kd\\x2ddc.mount")

for i in "${!MOUNTS[@]}"; do
    if ! stat "${MOUNTS[$i]}/." &>/dev/null; then
        logger -t kd-watchdog "${MOUNTS[$i]} unreachable, attempting remount"
        systemctl restart "${UNITS[$i]}"
        sleep 5
        if stat "${MOUNTS[$i]}/." &>/dev/null; then
            logger -t kd-watchdog "${MOUNTS[$i]} remount successful"
        else
            logger -t kd-watchdog "${MOUNTS[$i]} remount FAILED - will retry next cycle"
        fi
    fi
done
EOF
sudo chmod +x /usr/local/bin/kd-mount-watchdog.sh
```

### 5.2 Timer

```ini
# /etc/systemd/system/kd-mount-watchdog.service
[Unit]
Description=KD Mount Health Check

[Service]
Type=oneshot
ExecStart=/usr/local/bin/kd-mount-watchdog.sh
```

```ini
# /etc/systemd/system/kd-mount-watchdog.timer
[Unit]
Description=KD Mount Health Check Timer

[Timer]
OnBootSec=60
OnUnitActiveSec=30

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kd-mount-watchdog.timer
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

keding-dc 組改偵測 `/mnt/kd-share/.`。

---

## 七、防護鏈

```
KD共用 瞬斷
  │
  ├─ soft mount → I/O 返回錯誤不 hang → 容器不卡死
  │
  ├─ echo_interval=10 → 30 秒後 kernel 偵測斷線
  │   └─ kd-mount-watchdog stat → 觸發 I/O → kernel 嘗試 reconnect
  │       ├─ 成功 → 透明恢復
  │       └─ 失敗 → watchdog systemctl restart → 強制重掛
  │
  └─ > 45 秒仍未恢復
      └─ K3s livenessProbe 失敗 → Pod 重啟
          └─ automount 觸發 → 重新掛載 → 恢復
```

---

## 八、注意事項

- Unit 檔名必須對應路徑：`/mnt/kd-dev` → `mnt-kd\x2ddev.mount`（`-` 需 escape 為 `\x2d`）
- AD 密碼變更時更新 `/etc/kd-credentials`，然後 restart 三個 mount unit
- 所有 deployment yaml 已改用 hostPath 直接指向 `/mnt/kd-dev` 或 `/mnt/kd-dc`，不再使用 PV/PVC
