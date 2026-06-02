#!/bin/bash
# 🏝️ 比奇堡 K3s 環境設置腳本
# 在 Ubuntu Desktop 24.04 上執行
# 用法: sudo bash scripts/k3s-setup.sh

set -e

echo "🏝️ 比奇堡 K3s 環境設置"
echo "========================"
echo ""

# ─── 檢查是否為 root ───
if [ "$EUID" -ne 0 ]; then
  echo "❌ 請用 sudo 執行此腳本"
  exit 1
fi

REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(eval echo ~$REAL_USER)

# ─── Step 1: 安裝 Docker（build image 用）───
echo ""
echo "📦 Step 1: 安裝 Docker..."
if command -v docker &>/dev/null; then
  echo "  ✅ Docker 已安裝: $(docker --version)"
else
  apt-get update
  apt-get install -y ca-certificates curl
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin
  usermod -aG docker $REAL_USER
  echo "  ✅ Docker 安裝完成（需重新登入才能免 sudo 使用）"
fi

# ─── Step 2: 安裝 K3s ───
echo ""
echo "☸️  Step 2: 安裝 K3s..."
if command -v k3s &>/dev/null; then
  echo "  ✅ K3s 已安裝: $(k3s --version)"
else
  curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--disable=traefik --write-kubeconfig-mode=644" sh -
  echo "  ✅ K3s 安裝完成"
fi

# 設定 kubectl 給一般使用者
echo ""
echo "🔧 設定 kubectl..."
mkdir -p $REAL_HOME/.kube
cp /etc/rancher/k3s/k3s.yaml $REAL_HOME/.kube/config
chown $REAL_USER:$REAL_USER $REAL_HOME/.kube/config
chmod 600 $REAL_HOME/.kube/config

# 驗證
su - $REAL_USER -c "kubectl get nodes" && echo "  ✅ kubectl 正常" || echo "  ❌ kubectl 連線失敗"

# ─── Step 3: 安裝 cifs-utils（NAS 掛載用）───
echo ""
echo "📂 Step 3: 安裝 cifs-utils..."
if dpkg -l | grep -q cifs-utils; then
  echo "  ✅ cifs-utils 已安裝"
else
  apt-get install -y cifs-utils
  echo "  ✅ cifs-utils 安裝完成"
fi

# ─── Step 4: NAS 掛載設定 ───
echo ""
echo "🗄️  Step 4: 設定 NAS 掛載..."

NAS_CRED_FILE="/etc/nas-credentials"
NAS_MOUNT="/mnt/nas"
NAS_DEVICE="//192.168.1.218/KD共用/18_各部門共享區/21_系統開發課/88.BikiniBottom"

if [ ! -f "$NAS_CRED_FILE" ]; then
  echo "  需要 NAS 帳號密碼（跟舊機 .env 裡的 NAS_USER / NAS_PASSWORD 一樣）"
  read -p "  NAS 使用者名稱: " NAS_USER
  read -sp "  NAS 密碼: " NAS_PASS
  echo ""
  
  cat > $NAS_CRED_FILE <<EOF
username=$NAS_USER
password=$NAS_PASS
EOF
  chmod 600 $NAS_CRED_FILE
  echo "  ✅ NAS credential 已建立: $NAS_CRED_FILE"
else
  echo "  ✅ NAS credential 已存在: $NAS_CRED_FILE"
fi

# 建立掛載點
mkdir -p $NAS_MOUNT

# 檢查 fstab 是否已有
if grep -q "88.BikiniBottom" /etc/fstab; then
  echo "  ✅ fstab 已有 NAS 設定"
else
  echo "$NAS_DEVICE $NAS_MOUNT cifs credentials=$NAS_CRED_FILE,file_mode=0777,dir_mode=0777,vers=3.0,iocharset=utf8,echo_interval=10,_netdev,x-systemd.automount 0 0" >> /etc/fstab
  echo "  ✅ fstab 已新增 NAS 掛載設定"
fi

# 掛載
systemctl daemon-reload
mount -a 2>/dev/null || true

if mountpoint -q $NAS_MOUNT; then
  echo "  ✅ NAS 已掛載到 $NAS_MOUNT"
  echo "  📂 內容: $(ls $NAS_MOUNT/ 2>/dev/null | head -5)"
else
  echo "  ⚠️  NAS 尚未掛載（可能 NAS 不在線或帳密錯誤）"
  echo "  之後可執行: sudo mount -a"
fi

# ─── Step 5: 安裝 GitHub CLI（選用）───
echo ""
echo "🐙 Step 5: 安裝 GitHub CLI..."
if command -v gh &>/dev/null; then
  echo "  ✅ gh 已安裝: $(gh --version | head -1)"
else
  curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list
  apt-get update
  apt-get install -y gh
  echo "  ✅ gh 安裝完成"
fi

# ─── 完成 ───
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 環境設置完成！"
echo ""
echo "下一步："
echo "  1. 重新登入（讓 docker group 生效）"
echo "  2. 執行 Phase 2: build image + import"
echo "     docker build -t bikini-bottom/agent:latest ."
echo "     docker save bikini-bottom/agent:latest | sudo k3s ctr images import -"
echo "  3. 從舊機複製 .env 到本機 repo 根目錄"
echo "  4. 執行: bash scripts/k3s-create-secrets.sh"
echo "  5. 執行: kubectl apply -k k3s/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
