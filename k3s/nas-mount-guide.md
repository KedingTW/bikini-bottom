# NAS 掛載與斷線防護指南

**作成：章魚哥（PM）+ 珊迪（技術審查）**
**日期：2026-06-04**
**狀態：✅ 覆核通過，可執行**
**目標讀者：Kiro**

---

## 背景

原架構（Windows + WSL2 + Docker Compose）使用 Docker CIFS volume 掛載 NAS，瞬斷後容器 hang 死需手動重啟。遷移到 Ubuntu 24.04 + K3s 後，改為 host level mount + hostPath，搭配多層防護確保斷線自動恢復。

## 關鍵決策

| 項目 | 決策 | 原因 |
|------|------|------|
| 協議 | SMB 3.0（mount.cifs vers=3.0） | 公司 NAS 僅開 Samba，全 Windows 用 net use，無需改 NAS 設定 |
| 認證 | AD 帳號 credentials file | 入域後用 AD 帳密，不用 Kerberos（簡單優先） |
| 掛載路徑 | `/mnt/nas` | 與本目錄 yaml 一致（nas-pv.yaml 已指向此路徑） |
| 容器存取方式 | hostPath / PV+PVC | Kiro 已有的 deployment yaml 不需修改 |

---

## 一、Credentials File

```bash
sudo tee /etc/nas-credentials << 'EOF'
username=AD帳號
password=AD密碼
domain=公司AD_Domain
EOF
sudo chmod 600 /etc/nas-credentials
```

---

## 二、Systemd Mount Unit

```ini
# /etc/systemd/system/mnt-nas.mount
[Unit]
Description=KD NAS Share (BikiniBottom)
After=network-online.target
Wants=network-online.target

[Mount]
What=//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom
Where=/mnt/nas
Type=cifs
Options=credentials=/etc/nas-credentials,soft,echo_interval=10,vers=3.0,iocharset=utf8,file_mode=0777,dir_mode=0777,_netdev
TimeoutSec=30

[Install]
WantedBy=multi-user.target
```

---

## 三、Systemd Automount Unit

```ini
# /etc/systemd/system/mnt-nas.automount
[Unit]
Description=Automount KD NAS Share

[Automount]
Where=/mnt/nas
TimeoutIdleSec=0

[Install]
WantedBy=multi-user.target
```

---

## 四、啟用掛載

```bash
sudo mkdir -p /mnt/nas
sudo systemctl daemon-reload
sudo systemctl enable mnt-nas.automount
sudo systemctl start mnt-nas.automount
```

⚠️ **不要 enable `mnt-nas.mount`**，只 enable automount。Mount 由 automount 按需觸發。

---

## 五、NAS Watchdog

### 5.1 腳本

```bash
sudo tee /usr/local/bin/nas-watchdog.sh << 'EOF'
#!/bin/bash
MOUNT_POINT="/mnt/nas"
SYSTEMD_UNIT="mnt-nas.mount"

# stat 產生 I/O，讓 kernel 有機會觸發 reconnect
if ! stat "$MOUNT_POINT/." &>/dev/null; then
    logger -t nas-watchdog "NAS unreachable, attempting remount"
    systemctl restart "$SYSTEMD_UNIT"
    sleep 5
    if stat "$MOUNT_POINT/." &>/dev/null; then
        logger -t nas-watchdog "NAS remount successful"
    else
        logger -t nas-watchdog "NAS remount FAILED - will retry next cycle"
    fi
fi
EOF
sudo chmod +x /usr/local/bin/nas-watchdog.sh
```

### 5.2 Timer

```ini
# /etc/systemd/system/nas-watchdog.service
[Unit]
Description=NAS Health Check

[Service]
Type=oneshot
ExecStart=/usr/local/bin/nas-watchdog.sh
```

```ini
# /etc/systemd/system/nas-watchdog.timer
[Unit]
Description=NAS Health Check Timer

[Timer]
OnBootSec=60
OnUnitActiveSec=30

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nas-watchdog.timer
```

---

## 六、K3s Pod livenessProbe

在每個 agent deployment 的 container spec 加入：

```yaml
livenessProbe:
  exec:
    command:
      - stat
      - /nas/.
  initialDelaySeconds: 30
  periodSeconds: 15
  failureThreshold: 3
readinessProbe:
  exec:
    command:
      - stat
      - /nas/.
  periodSeconds: 10
  failureThreshold: 2
```

Pod 內 NAS mount 路徑為 `/nas`（由 PVC 掛入），所以 probe 偵測 `/nas/.`。

---

## 七、防護鏈

```
NAS 瞬斷
  │
  ├─ soft mount（預設）→ I/O 返回錯誤不 hang → 容器不卡死
  │
  ├─ echo_interval=10 → 30 秒後 kernel 偵測斷線
  │   └─ nas-watchdog stat → 觸發 I/O → kernel 嘗試 reconnect
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
| 3 | credentials file | `ls -la /etc/nas-credentials` → 600 |
| 4 | 手動 mount 測試 | `sudo mount -t cifs -o credentials=/etc/nas-credentials,vers=3.0 "//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom" /mnt/nas && ls /mnt/nas` |
| 5 | automount 啟用 | `systemctl status mnt-nas.automount` → active |
| 6 | automount 測試 | `sudo umount /mnt/nas && ls /mnt/nas`（應自動掛回） |
| 7 | watchdog 運作 | `systemctl status nas-watchdog.timer` → active |
| 8 | K3s ready | `sudo kubectl get nodes` → Ready |
| 9 | Pods running | `sudo kubectl get pods -n bikini-bottom` |
| 10 | **斷線模擬** | `sudo iptables -A OUTPUT -d 192.168.1.218 -j DROP` |
| 11 | **恢復確認** | `sudo iptables -D OUTPUT -d 192.168.1.218 -j DROP` → Pod 自動恢復 |

---

## 十、注意事項

- Unit 檔名必須對應路徑：`/mnt/nas` → `mnt-nas.mount` / `mnt-nas.automount`
- AD 密碼變更時更新 `/etc/nas-credentials`，然後 `systemctl restart mnt-nas.mount`
- NAS IP 變更時修改 mount unit 的 `What=`，`systemctl daemon-reload`
- 本目錄的 deployment yaml 已用 PVC 指向 `/mnt/nas`，無需修改
