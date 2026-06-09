"""🏝️ 比奇堡團隊 Dashboard — 角色狀態管理介面"""
import hashlib
import os
import logging
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from itsdangerous import URLSafeTimedSerializer

try:
    from kubernetes import client, config as k8s_config
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ─── Config ───────────────────────────────────────────────
SECRET_KEY = os.environ.get("SESSION_SECRET", "bikini-bottom-dashboard-secret-key-2026")
NAMESPACE = os.environ.get("K8S_NAMESPACE", "bikini-bottom")
BACKEND = os.environ.get("DASHBOARD_BACKEND", "auto")  # "k8s", "docker", or "auto"
METRICS_DB = os.environ.get("METRICS_DB", "/data/metrics/metrics.db")
DEFAULT_PASSWORD = os.environ.get("DASHBOARD_DEFAULT_PASSWORD", "")


# ─── SQLite Metrics Store ─────────────────────────────────
def _init_db():
    """Initialize SQLite database for metrics history."""
    os.makedirs(os.path.dirname(METRICS_DB), exist_ok=True)
    with sqlite3.connect(METRICS_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                agent TEXT NOT NULL,
                cpu_milli REAL NOT NULL,
                memory_mb REAL NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                agent TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                dismissed INTEGER DEFAULT 0
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_ts ON metrics_history(ts)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_agent ON metrics_history(agent)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_ts ON alerts(ts)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                department TEXT DEFAULT '',
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'admin'
            )
        """)
    _seed_users()


def _seed_users():
    """Seed initial users if table is empty."""
    with sqlite3.connect(METRICS_DB) as conn:
        # Add role column if not exists (migration)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'admin'")
            conn.commit()
        except Exception:
            pass
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if count == 0:
            default_pw = hashlib.sha256(DEFAULT_PASSWORD.encode()).hexdigest() if DEFAULT_PASSWORD else ""
            if not default_pw:
                logging.warning("⚠️ DASHBOARD_DEFAULT_PASSWORD 未設定，跳過 seed users")
                return
            initial_users = [
                ("11021395", "蔡旻哲", "系統開發課"),
                ("11020955", "林潔庭", "系統開發課"),
                ("11020550", "吳珈瑄", "系統開發課"),
                ("11110577", "楊詠仁", "系統開發課"),
            ]
            for uid, name, dept in initial_users:
                conn.execute("INSERT OR IGNORE INTO users (id, name, department, password_hash, role) VALUES (?, ?, ?, ?, 'admin')",
                             (uid, name, dept, default_pw))
            conn.commit()


def _store_metrics(metrics: dict):
    """Store current metrics snapshot to SQLite."""
    try:
        with sqlite3.connect(METRICS_DB) as conn:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            rows = []
            for agent_name, m in metrics.items():
                cpu_raw = m.get("cpu_raw", "0")
                mem_raw = m.get("memory_raw", "0")
                cpu_milli = _parse_cpu_milli(cpu_raw)
                mem_mb = _parse_memory_mb(mem_raw)
                rows.append((ts, agent_name, cpu_milli, mem_mb))
            conn.executemany("INSERT INTO metrics_history (ts, agent, cpu_milli, memory_mb) VALUES (?, ?, ?, ?)", rows)
    except Exception as e:
        logging.error(f"Metrics store error: {e}")


def _cleanup_old_metrics():
    """Remove metrics older than 30 days."""
    try:
        with sqlite3.connect(METRICS_DB) as conn:
            cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("DELETE FROM metrics_history WHERE ts < ?", (cutoff,))
    except Exception as e:
        logging.error(f"Metrics cleanup error: {e}")


def _start_metrics_collector():
    """Background thread: collect metrics every 60s, detect anomalies, store to SQLite."""
    import time

    last_restarts = {}  # track restart counts to detect increases

    def _check_alerts():
        """Check k8s pod status for anomalies."""
        if not K8S_AVAILABLE:
            return
        try:
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException:
            try:
                k8s_config.load_kube_config()
            except k8s_config.ConfigException:
                return

        core_api = client.CoreV1Api()
        try:
            pods = core_api.list_namespaced_pod(namespace=NAMESPACE)
        except Exception:
            return

        for pod in pods.items:
            labels = pod.metadata.labels or {}
            app_name = labels.get("app")
            if not app_name:
                continue

            # Check container statuses
            if not pod.status.container_statuses:
                continue
            cs = pod.status.container_statuses[0]

            # Detect restart count increase
            current_restarts = cs.restart_count or 0
            prev_restarts = last_restarts.get(app_name, current_restarts)
            if current_restarts > prev_restarts:
                _insert_alert(app_name, "warning", f"重啟次數增加（{prev_restarts} → {current_restarts}）")
            last_restarts[app_name] = current_restarts

            # Detect waiting state (CrashLoopBackOff, OOMKilled, etc.)
            if cs.state and cs.state.waiting:
                reason = cs.state.waiting.reason or "Unknown"
                if reason in ("CrashLoopBackOff", "OOMKilled", "Error", "ImagePullBackOff"):
                    _insert_alert(app_name, "critical", f"容器異常：{reason}")

            # Detect terminated with error
            if cs.state and cs.state.terminated:
                reason = cs.state.terminated.reason or ""
                if reason == "OOMKilled":
                    _insert_alert(app_name, "critical", f"記憶體不足被終止（OOMKilled）")

    def _collect_loop():
        while True:
            try:
                metrics = _fetch_k8s_metrics()
                if metrics:
                    _store_metrics(metrics)
                _check_alerts()
                if int(time.time()) % 3600 < 60:
                    _cleanup_old_metrics()
            except Exception as e:
                logging.error(f"Metrics collector error: {e}")
            time.sleep(60)

    t = threading.Thread(target=_collect_loop, daemon=True)
    t.start()


def _fetch_k8s_metrics() -> dict:
    """Fetch metrics from K8s metrics-server."""
    if not K8S_AVAILABLE:
        return {}
    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        try:
            k8s_config.load_kube_config()
        except k8s_config.ConfigException:
            return {}
    custom_api = client.CustomObjectsApi()
    try:
        raw = custom_api.list_namespaced_custom_object(
            group="metrics.k8s.io", version="v1beta1",
            namespace=NAMESPACE, plural="pods",
        )
    except Exception:
        return {}
    result = {}
    for item in raw.get("items", []):
        labels = item.get("metadata", {}).get("labels", {})
        app_name = labels.get("app")
        if not app_name:
            continue
        containers = item.get("containers", [])
        if containers:
            c = containers[0]
            result[app_name] = {
                "cpu_raw": c.get("usage", {}).get("cpu", "0"),
                "memory_raw": c.get("usage", {}).get("memory", "0"),
            }
    return result


_init_db()
_start_metrics_collector()


# ─── App Setup ────────────────────────────────────────────
app = FastAPI(title="比奇堡 Dashboard", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

BASE_DIR = Path(__file__).resolve().parent
AGENTS_DIR = Path(os.environ.get("AGENTS_DIR", "/data/agents"))

# Serve Vue SPA build output
DIST_DIR = Path(os.environ.get("DIST_DIR", str((BASE_DIR / ".." / "dist").resolve())))

serializer = URLSafeTimedSerializer(SECRET_KEY)

# ─── Agent 角色定義 ───────────────────────────────────────
AGENTS = [
    {"name": "bob", "display": "海綿寶寶", "role": "全端工程師", "type": "agent", "icon": "🧽"},
    {"name": "patrick", "display": "派大星", "role": "後端工程師", "type": "agent", "icon": "⭐"},
    {"name": "pearl", "display": "珍珍", "role": "全端工程師", "type": "agent", "icon": "🐋"},
    {"name": "larry", "display": "蝦霸", "role": "後端工程師", "type": "agent", "icon": "🦞"},
    {"name": "squidward", "display": "章魚哥", "role": "專案經理", "type": "agent", "icon": "🦑"},
    {"name": "sandy", "display": "珊迪", "role": "客戶成功經理", "type": "agent", "icon": "🐿️"},
    {"name": "puff", "display": "泡芙老師", "role": "Code Review", "type": "agent", "icon": "🐡"},
    {"name": "conch", "display": "神奇海螺", "role": "團隊神諭者", "type": "agent", "icon": "🐚"},
    {"name": "mermaid-man", "display": "海超人", "role": "DevOps", "type": "agent", "icon": "🦸"},
    {"name": "gary", "display": "小蝸", "role": "維運助手", "type": "service", "icon": "🐌"},
    {"name": "gateway", "display": "Gateway", "role": "WeCom 閘道", "type": "service", "icon": "🌐"},
    {"name": "wecom-bot", "display": "企微Bot", "role": "企業微信", "type": "service", "icon": "💬"},
]


# ─── K8s Client ───────────────────────────────────────────
def get_k8s_apps_api():
    """Get Kubernetes AppsV1 API client."""
    if not K8S_AVAILABLE:
        return None
    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        try:
            k8s_config.load_kube_config()
        except k8s_config.ConfigException:
            return None
    return client.AppsV1Api()


def get_k8s_core_api():
    """Get Kubernetes CoreV1 API client."""
    if not K8S_AVAILABLE:
        return None
    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        try:
            k8s_config.load_kube_config()
        except k8s_config.ConfigException:
            return None
    return client.CoreV1Api()


# ─── Docker Client ────────────────────────────────────────
def get_docker_client():
    """Get Docker client."""
    if not DOCKER_AVAILABLE:
        return None
    try:
        return docker.DockerClient(base_url="unix:///var/run/docker.sock")
    except Exception:
        return None


def _detect_backend() -> str:
    """Auto-detect whether to use K8s or Docker."""
    if BACKEND != "auto":
        return BACKEND
    # Try K8s first (in-cluster)
    if K8S_AVAILABLE:
        try:
            k8s_config.load_incluster_config()
            return "k8s"
        except k8s_config.ConfigException:
            pass
    # Fall back to Docker
    if DOCKER_AVAILABLE:
        try:
            c = docker.DockerClient(base_url="unix:///var/run/docker.sock")
            c.ping()
            c.close()
            return "docker"
        except Exception:
            pass
    return "none"


def _docker_get_all_status(docker_client) -> list:
    """Get status of all agents via Docker API."""
    result = []
    for agent in AGENTS:
        try:
            container = docker_client.containers.get(agent["name"])
            status = container.status  # running, exited, restarting, paused, dead
            started_at = container.attrs["State"].get("StartedAt", "")
            restart_count = container.attrs.get("RestartCount", 0)
            uptime = _calc_uptime(started_at) if status == "running" else "-"
            mapped_status = "running" if status == "running" else "failed" if status in ("exited", "dead") else status
            result.append({
                "name": agent["name"],
                "display": agent["display"],
                "role": agent["role"],
                "type": agent["type"],
                "status": mapped_status,
                "uptime": uptime,
                "restarts": restart_count,
                "pod_name": agent["name"],
            })
        except Exception:
            result.append({
                "name": agent["name"],
                "display": agent["display"],
                "role": agent["role"],
                "type": agent["type"],
                "status": "not_found",
                "uptime": "-",
                "restarts": 0,
                "pod_name": None,
            })
    return result


def _docker_restart(docker_client, agent_name: str):
    """Restart a container via Docker API."""
    container = docker_client.containers.get(agent_name)
    container.restart(timeout=10)


def _docker_logs(docker_client, agent_name: str, lines: int = 50) -> str:
    """Get container logs via Docker API."""
    container = docker_client.containers.get(agent_name)
    return container.logs(tail=lines, timestamps=False).decode("utf-8", errors="replace")


# ─── Auth Helpers ─────────────────────────────────────────
def get_current_user(request: Request) -> dict | None:
    """Check session for logged-in user. Returns {'id': ..., 'name': ...} or None."""
    token = request.session.get("auth_token")
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=86400)  # 24hr expiry
        return {"id": data.get("user"), "name": data.get("name", data.get("user"))}
    except Exception:
        return None


def require_auth(request: Request):
    """Dependency that enforces authentication."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


# ─── Routes ──────────────────────────────────────────────
@app.post("/api/login")
async def api_login(request: Request):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="請求格式錯誤")
    username = body.get("username", "") if isinstance(body, dict) else ""
    password = body.get("password", "") if isinstance(body, dict) else ""
    if not username or not password:
        raise HTTPException(status_code=400, detail="請輸入帳號和密碼")
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = sqlite3.connect(METRICS_DB)
    row = conn.execute("SELECT id, name FROM users WHERE id = ? AND password_hash = ?", (username, pw_hash)).fetchone()
    conn.close()
    if row:
        token = serializer.dumps({"user": row[0], "name": row[1]})
        request.session["auth_token"] = token
        return JSONResponse({"ok": True, "name": row[1]})
    raise HTTPException(status_code=401, detail="帳號或密碼錯誤")


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return HTMLResponse((DIST_DIR / "index.html").read_text())


@app.get("/avatar/{agent_name}")
async def avatar(agent_name: str):
    """Serve agent avatar image. Falls back to 404 if not found."""
    valid_names = {a["name"] for a in AGENTS}
    lookup_name = agent_name

    if agent_name not in valid_names:
        raise HTTPException(status_code=404)

    # Search for avatar.png, avatar.jpg
    for ext in ("png", "jpg", "jpeg", "webp"):
        avatar_path = AGENTS_DIR / lookup_name / f"avatar.{ext}"
        if avatar_path.is_file():
            media_types = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}
            from fastapi.responses import FileResponse
            return FileResponse(avatar_path, media_type=media_types.get(ext, "image/png"))

    raise HTTPException(status_code=404)


@app.get("/api/me")
async def api_me(request: Request):
    """取得當前登入使用者資訊"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = sqlite3.connect(METRICS_DB)
    row = conn.execute("SELECT name, department, role FROM users WHERE id = ?", (user["id"],)).fetchone()
    conn.close()
    name = row[0] if row else user["id"]
    role = row[2] if row else "viewer"
    return JSONResponse({"id": user["id"], "name": name, "role": role})


@app.post("/api/change-password")
async def api_change_password(request: Request):
    """修改密碼"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    old_pw = body.get("old_password", "")
    new_pw = body.get("new_password", "")
    if not new_pw or len(new_pw) < 6:
        raise HTTPException(status_code=400, detail="新密碼至少 6 字元")
    old_hash = hashlib.sha256(old_pw.encode()).hexdigest()
    conn = sqlite3.connect(METRICS_DB)
    row = conn.execute("SELECT id FROM users WHERE id = ? AND password_hash = ?", (user["id"], old_hash)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail="舊密碼不正確")
    new_hash = hashlib.sha256(new_pw.encode()).hexdigest()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, user["id"]))
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True, "message": "密碼已更新"})


# ─── User Management API ─────────────────────────────────
@app.get("/api/users")
async def api_users(request: Request):
    """取得所有使用者列表（需 admin 權限）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = sqlite3.connect(METRICS_DB)
    rows = conn.execute("SELECT id, name, department, role FROM users ORDER BY id").fetchall()
    conn.close()
    return JSONResponse({"users": [{"id": r[0], "name": r[1], "department": r[2], "role": r[3]} for r in rows]})


@app.post("/api/users")
async def api_create_user(request: Request):
    """新增使用者（需 admin 權限）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    # Check admin
    conn = sqlite3.connect(METRICS_DB)
    me = conn.execute("SELECT role FROM users WHERE id = ?", (user["id"],)).fetchone()
    if not me or me[0] != "admin":
        conn.close()
        raise HTTPException(status_code=403, detail="權限不足")
    body = await request.json()
    uid = body.get("id", "").strip()
    name = body.get("name", "").strip()
    department = body.get("department", "").strip()
    role = body.get("role", "viewer")
    password = body.get("password", DEFAULT_PASSWORD)
    if not uid or not name:
        conn.close()
        raise HTTPException(status_code=400, detail="員工編號和姓名為必填")
    if role not in ("admin", "viewer"):
        role = "viewer"
    pw_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        conn.execute("INSERT INTO users (id, name, department, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                     (uid, name, department, pw_hash, role))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="該員工編號已存在")
    conn.close()
    return JSONResponse({"ok": True, "message": f"已新增使用者 {name}"})


@app.delete("/api/users/{user_id}")
async def api_delete_user(user_id: str, request: Request):
    """刪除使用者（需 admin 權限，不能刪除自己）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = sqlite3.connect(METRICS_DB)
    me = conn.execute("SELECT role FROM users WHERE id = ?", (user["id"],)).fetchone()
    if not me or me[0] != "admin":
        conn.close()
        raise HTTPException(status_code=403, detail="權限不足")
    if user_id == user["id"]:
        conn.close()
        raise HTTPException(status_code=400, detail="不能刪除自己")
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True})


@app.post("/api/users/{user_id}/reset-password")
async def api_reset_password(user_id: str, request: Request):
    """重設使用者密碼為預設值（需 admin 權限）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = sqlite3.connect(METRICS_DB)
    me = conn.execute("SELECT role FROM users WHERE id = ?", (user["id"],)).fetchone()
    if not me or me[0] != "admin":
        conn.close()
        raise HTTPException(status_code=403, detail="權限不足")
    default_pw = hashlib.sha256(DEFAULT_PASSWORD.encode()).hexdigest() if DEFAULT_PASSWORD else ""
    if not default_pw:
        raise HTTPException(status_code=500, detail="DASHBOARD_DEFAULT_PASSWORD 未設定")
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (default_pw, user_id))
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True, "message": "密碼已重設為預設值"})


@app.put("/api/users/{user_id}/role")
async def api_update_role(user_id: str, request: Request):
    """修改使用者角色（需 admin 權限）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = sqlite3.connect(METRICS_DB)
    me = conn.execute("SELECT role FROM users WHERE id = ?", (user["id"],)).fetchone()
    if not me or me[0] != "admin":
        conn.close()
        raise HTTPException(status_code=403, detail="權限不足")
    body = await request.json()
    new_role = body.get("role", "viewer")
    if new_role not in ("admin", "viewer"):
        new_role = "viewer"
    conn.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True})


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """使用者管理頁面"""
    return HTMLResponse((DIST_DIR / "index.html").read_text())


@app.get("/api/status")
async def api_status(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    backend = _detect_backend()

    if backend == "docker":
        docker_client = get_docker_client()
        if not docker_client:
            return JSONResponse({"error": "Docker 連線失敗", "agents": _mock_status()})
        try:
            agents = _docker_get_all_status(docker_client)
            docker_client.close()
            return JSONResponse({"error": None, "agents": agents})
        except Exception as e:
            docker_client.close()
            return JSONResponse({"error": str(e), "agents": []})

    elif backend == "k8s":
        core_api = get_k8s_core_api()
        if not core_api:
            return JSONResponse({"error": "K8s 連線失敗", "agents": _mock_status()})
        try:
            pods = core_api.list_namespaced_pod(namespace=NAMESPACE)
        except Exception as e:
            logging.error(f"K8s API 失敗：{e}")
            return JSONResponse({"error": str(e), "agents": []})

        result = []
        for agent in AGENTS:
            pod_info = _find_pod_for_agent(agent["name"], pods.items)
            result.append({
                "name": agent["name"],
                "display": agent["display"],
                "role": agent["role"],
                "type": agent["type"],
                **pod_info,
            })
        return JSONResponse({"error": None, "agents": result})

    else:
        return JSONResponse({"error": "無可用後端（Docker/K8s 皆無法連線）", "agents": _mock_status()})


@app.post("/api/restart/{agent_name}")
async def api_restart(agent_name: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    valid_names = [a["name"] for a in AGENTS]
    if agent_name not in valid_names:
        raise HTTPException(status_code=400, detail=f"未知角色：{agent_name}")

    backend = _detect_backend()

    if backend == "docker":
        docker_client = get_docker_client()
        if not docker_client:
            raise HTTPException(status_code=503, detail="Docker 連線失敗")
        try:
            _docker_restart(docker_client, agent_name)
            docker_client.close()
            logging.info(f"✅ 已重啟 {agent_name} (by {user}) [docker]")
            return JSONResponse({"success": True, "message": f"{agent_name} 已觸發重啟"})
        except Exception as e:
            docker_client.close()
            raise HTTPException(status_code=500, detail=f"重啟失敗：{e}")

    elif backend == "k8s":
        apps_api = get_k8s_apps_api()
        if not apps_api:
            raise HTTPException(status_code=503, detail="K8s 連線失敗")
        try:
            now = datetime.now(timezone.utc).isoformat()
            body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": now
                            }
                        }
                    }
                }
            }
            apps_api.patch_namespaced_deployment(
                name=agent_name,
                namespace=NAMESPACE,
                body=body,
            )
            logging.info(f"✅ 已重啟 {agent_name} (by {user}) [k8s]")
            return JSONResponse({"success": True, "message": f"{agent_name} 已觸發重啟"})
        except Exception as e:
            logging.error(f"重啟 {agent_name} 失敗：{e}")
            raise HTTPException(status_code=500, detail=f"重啟失敗：{e}")

    else:
        raise HTTPException(status_code=503, detail="無可用後端")


# ─── Deploy APIs ─────────────────────────────────────────
REPO_DIR = Path(os.environ.get("REPO_DIR", "/data/repo"))


def _init_deploy_table():
    with sqlite3.connect(METRICS_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deploy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                agent TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT DEFAULT ''
            )
        """)


_init_deploy_table()


@app.get("/api/deploy/git-status")
async def api_deploy_git_status(request: Request):
    """取得 repo 的 git 狀態"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    import subprocess
    repo_dir = str(REPO_DIR) if REPO_DIR.exists() else "/data/repo"
    try:
        branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_dir, capture_output=True, text=True, timeout=5).stdout.strip()
        log = subprocess.run(["git", "log", "--oneline", "-10"], cwd=repo_dir, capture_output=True, text=True, timeout=5).stdout.strip()
        status = subprocess.run(["git", "status", "--short"], cwd=repo_dir, capture_output=True, text=True, timeout=5).stdout.strip()
        return JSONResponse({"branch": branch, "log": log.split("\n") if log else [], "uncommitted": status.split("\n") if status else []})
    except Exception as e:
        return JSONResponse({"branch": "unknown", "log": [], "uncommitted": [], "error": str(e)})


@app.get("/api/deploy/history")
async def api_deploy_history(request: Request):
    """取得部署歷史"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = sqlite3.connect(METRICS_DB)
    rows = conn.execute("SELECT ts, user_name, agent, action, status, message FROM deploy_history ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    history = [{"ts": r[0], "user": r[1], "agent": r[2], "action": r[3], "status": r[4], "message": r[5]} for r in rows]
    return JSONResponse({"history": history})


@app.post("/api/deploy/{agent_name}")
async def api_deploy(agent_name: str, request: Request):
    """一鍵部署：build image + import to k3s + restart"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    valid_names = [a["name"] for a in AGENTS] + ["admin"]
    if agent_name not in valid_names:
        raise HTTPException(status_code=400, detail=f"未知目標：{agent_name}")

    import subprocess
    tz = timezone(timedelta(hours=8))
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    repo_dir = str(REPO_DIR) if REPO_DIR.exists() else "/data/repo"
    steps = []

    def log_deploy(action, status, message=""):
        conn = sqlite3.connect(METRICS_DB)
        conn.execute("INSERT INTO deploy_history (ts, user_id, user_name, agent, action, status, message) VALUES (?, ?, ?, ?, ?, ?, ?)",
                     (now_str, user["id"], user["name"], agent_name, action, status, message))
        conn.commit()
        conn.close()

    # Step 1: git pull
    try:
        r = subprocess.run(["git", "pull", "origin", "master"], cwd=repo_dir, capture_output=True, text=True, timeout=30)
        steps.append({"step": "git pull", "ok": r.returncode == 0, "output": (r.stdout + r.stderr).strip()[-200:]})
        if r.returncode != 0:
            log_deploy("deploy", "failed", f"git pull 失敗: {r.stderr.strip()[:100]}")
            return JSONResponse({"success": False, "steps": steps, "error": "git pull 失敗"})
    except Exception as e:
        steps.append({"step": "git pull", "ok": False, "output": str(e)})
        log_deploy("deploy", "failed", f"git pull 例外: {e}")
        return JSONResponse({"success": False, "steps": steps, "error": str(e)})

    # Step 2: docker build
    if agent_name == "admin":
        dockerfile = f"{repo_dir}/services/admin/Dockerfile"
        context = f"{repo_dir}/services/admin"
        image_tag = "bikini-bottom/admin:latest"
    else:
        dockerfile = f"{repo_dir}/Dockerfile"
        context = repo_dir
        image_tag = "bikini-bottom/agent:latest"
    try:
        r = subprocess.run(["docker", "build", "-f", dockerfile, "-t", image_tag, context],
                           capture_output=True, text=True, timeout=300)
        steps.append({"step": "docker build", "ok": r.returncode == 0, "output": (r.stdout + r.stderr).strip()[-300:]})
        if r.returncode != 0:
            log_deploy("deploy", "failed", "docker build 失敗")
            return JSONResponse({"success": False, "steps": steps, "error": "docker build 失敗"})
    except Exception as e:
        steps.append({"step": "docker build", "ok": False, "output": str(e)})
        log_deploy("deploy", "failed", f"docker build 例外: {e}")
        return JSONResponse({"success": False, "steps": steps, "error": str(e)})

    # Step 3: import to k3s
    try:
        save_r = subprocess.run(["docker", "save", image_tag], capture_output=True, timeout=120)
        import_r = subprocess.run(["k3s", "ctr", "images", "import", "-"], input=save_r.stdout, capture_output=True, timeout=120)
        ok = import_r.returncode == 0
        steps.append({"step": "k3s import", "ok": ok, "output": import_r.stderr.decode()[:200] if not ok else "OK"})
        if not ok:
            log_deploy("deploy", "failed", "k3s import 失敗")
            return JSONResponse({"success": False, "steps": steps, "error": "k3s import 失敗"})
    except Exception as e:
        steps.append({"step": "k3s import", "ok": False, "output": str(e)})
        log_deploy("deploy", "failed", f"k3s import 例外: {e}")
        return JSONResponse({"success": False, "steps": steps, "error": str(e)})

    # Step 4: restart deployment
    try:
        deploy_name = agent_name if agent_name != "admin" else "admin"
        r = subprocess.run(["kubectl", "rollout", "restart", f"deployment/{deploy_name}", "-n", NAMESPACE],
                           capture_output=True, text=True, timeout=30)
        steps.append({"step": "restart", "ok": r.returncode == 0, "output": (r.stdout + r.stderr).strip()[:200]})
        if r.returncode != 0:
            log_deploy("deploy", "failed", "restart 失敗")
            return JSONResponse({"success": False, "steps": steps, "error": "restart 失敗"})
    except Exception as e:
        steps.append({"step": "restart", "ok": False, "output": str(e)})
        log_deploy("deploy", "failed", f"restart 例外: {e}")
        return JSONResponse({"success": False, "steps": steps, "error": str(e)})

    log_deploy("deploy", "success", f"部署完成")
    return JSONResponse({"success": True, "steps": steps})


@app.get("/api/logs/{agent_name}")
async def api_logs(agent_name: str, request: Request, lines: int = 50):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    valid_names = [a["name"] for a in AGENTS]
    if agent_name not in valid_names:
        raise HTTPException(status_code=400, detail=f"未知角色：{agent_name}")

    lines = min(lines, 200)
    backend = _detect_backend()

    if backend == "docker":
        docker_client = get_docker_client()
        if not docker_client:
            raise HTTPException(status_code=503, detail="Docker 連線失敗")
        try:
            log_text = _docker_logs(docker_client, agent_name, lines)
            docker_client.close()
            return JSONResponse({"logs": log_text or "(無 log)"})
        except Exception as e:
            docker_client.close()
            return JSONResponse({"logs": f"讀取失敗：{e}"})

    elif backend == "k8s":
        core_api = get_k8s_core_api()
        if not core_api:
            raise HTTPException(status_code=503, detail="K8s 連線失敗")
        try:
            pods = core_api.list_namespaced_pod(
                namespace=NAMESPACE,
                label_selector=f"app={agent_name}",
            )
            if not pods.items:
                return JSONResponse({"logs": f"找不到 {agent_name} 的 Pod"})
            pod_name = pods.items[0].metadata.name
            log_text = core_api.read_namespaced_pod_log(
                name=pod_name,
                namespace=NAMESPACE,
                tail_lines=lines,
            )
            return JSONResponse({"logs": log_text or "(無 log)"})
        except Exception as e:
            return JSONResponse({"logs": f"讀取失敗：{e}"})

    else:
        return JSONResponse({"logs": "無可用後端"})


@app.get("/api/logs/search")
async def api_logs_search(request: Request, keyword: str = "", agents: str = "", lines: int = 100, since_hours: int = 24):
    """跨 Pod 搜尋 log 關鍵字"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    import subprocess
    target_agents = [a.strip() for a in agents.split(",") if a.strip()] if agents else [a["name"] for a in AGENTS]
    valid_names = [a["name"] for a in AGENTS] + ["admin"]
    target_agents = [a for a in target_agents if a in valid_names]
    lines = min(lines, 500)
    results = []

    for agent_name in target_agents:
        try:
            r = subprocess.run(
                ["kubectl", "logs", f"deployment/{agent_name}", "-n", NAMESPACE,
                 f"--since={since_hours}h", f"--tail={lines}"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0 and r.stdout:
                log_lines = r.stdout.strip().split("\n")
                if keyword:
                    log_lines = [l for l in log_lines if keyword.lower() in l.lower()]
                if log_lines:
                    results.append({"agent": agent_name, "lines": log_lines[-200:], "total": len(log_lines)})
        except Exception:
            pass

    return JSONResponse({"results": results, "keyword": keyword, "since_hours": since_hours})


@app.get("/api/logs/export")
async def api_logs_export(request: Request, agents: str = "", since_hours: int = 24):
    """匯出所有 log 為純文字"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    import subprocess
    target_agents = [a.strip() for a in agents.split(",") if a.strip()] if agents else [a["name"] for a in AGENTS]
    valid_names = [a["name"] for a in AGENTS] + ["admin"]
    target_agents = [a for a in target_agents if a in valid_names]
    output = []

    for agent_name in target_agents:
        try:
            r = subprocess.run(
                ["kubectl", "logs", f"deployment/{agent_name}", "-n", NAMESPACE,
                 f"--since={since_hours}h", "--tail=1000"],
                capture_output=True, text=True, timeout=15
            )
            if r.returncode == 0 and r.stdout:
                output.append(f"=== {agent_name} ===")
                output.append(r.stdout.strip())
                output.append("")
        except Exception:
            pass

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("\n".join(output), headers={"Content-Disposition": "attachment; filename=logs-export.txt"})


@app.get("/api/metrics")
async def api_metrics(request: Request):
    """取得各 pod 的 CPU/Memory 即時用量（需 metrics-server）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    backend = _detect_backend()
    if backend != "k8s":
        return JSONResponse({"error": "僅支援 K8s 後端", "metrics": {}})

    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        try:
            k8s_config.load_kube_config()
        except k8s_config.ConfigException:
            return JSONResponse({"error": "K8s 連線失敗", "metrics": {}})

    custom_api = client.CustomObjectsApi()
    try:
        metrics = custom_api.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace=NAMESPACE,
            plural="pods",
        )
    except Exception as e:
        logging.error(f"Metrics API 失敗：{e}")
        return JSONResponse({"error": str(e), "metrics": {}})

    result = {}
    for item in metrics.get("items", []):
        labels = item.get("metadata", {}).get("labels", {})
        app_name = labels.get("app")
        if not app_name:
            continue
        containers = item.get("containers", [])
        if containers:
            c = containers[0]
            cpu_raw = c.get("usage", {}).get("cpu", "0")
            mem_raw = c.get("usage", {}).get("memory", "0")
            result[app_name] = {
                "cpu": _parse_cpu(cpu_raw),
                "memory": _parse_memory(mem_raw),
                "cpu_raw": cpu_raw,
                "memory_raw": mem_raw,
            }

    return JSONResponse({"error": None, "metrics": result})


@app.get("/api/metrics/history")
async def api_metrics_history(request: Request, hours: int = 6, agent: str = ""):
    """取得歷史 metrics 數據（用於圖表）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    hours = min(hours, 720)  # Max 30 days
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(METRICS_DB)
        if agent:
            rows = conn.execute(
                "SELECT ts, agent, cpu_milli, memory_mb FROM metrics_history WHERE ts >= ? AND agent = ? ORDER BY ts",
                (since, agent),
            ).fetchall()
        else:
            # Aggregate total across all agents per timestamp
            rows = conn.execute(
                "SELECT ts, 'total' as agent, SUM(cpu_milli), SUM(memory_mb) FROM metrics_history WHERE ts >= ? GROUP BY ts ORDER BY ts",
                (since,),
            ).fetchall()
        conn.close()
    except Exception as e:
        return JSONResponse({"error": str(e), "data": []})

    data = [{"ts": r[0], "agent": r[1], "cpu_pct": round(r[2] / 10, 2), "memory_mb": round(r[3], 1)} for r in rows]
    return JSONResponse({"error": None, "data": data})


@app.get("/metrics", response_class=HTMLResponse)
async def metrics_page(request: Request):
    return HTMLResponse((DIST_DIR / "index.html").read_text())


# ─── Alerts API ───────────────────────────────────────────
@app.get("/api/alerts")
async def api_alerts(request: Request):
    """取得未關閉的異常通知列表"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        conn = sqlite3.connect(METRICS_DB)
        rows = conn.execute(
            "SELECT id, ts, agent, level, message FROM alerts WHERE dismissed = 0 ORDER BY ts DESC LIMIT 50"
        ).fetchall()
        conn.close()
        alerts = [{"id": r[0], "ts": r[1], "agent": r[2], "level": r[3], "message": r[4]} for r in rows]
        return JSONResponse({"alerts": alerts})
    except Exception as e:
        return JSONResponse({"alerts": [], "error": str(e)})


@app.post("/api/alerts/{alert_id}/dismiss")
async def api_dismiss_alert(alert_id: int, request: Request):
    """關閉（dismiss）一則異常通知"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        conn = sqlite3.connect(METRICS_DB)
        conn.execute("UPDATE alerts SET dismissed = 1 WHERE id = ?", (alert_id,))
        conn.commit()
        conn.close()
        return JSONResponse({"ok": True})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _insert_alert(agent: str, level: str, message: str):
    """Insert an alert into SQLite."""
    try:
        with sqlite3.connect(METRICS_DB) as conn:
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            conn.execute("INSERT INTO alerts (ts, agent, level, message) VALUES (?, ?, ?, ?)", (ts, agent, level, message))
    except Exception as e:
        logging.error(f"Insert alert error: {e}")


@app.get("/api/alerts/history")
async def api_alerts_history(request: Request, days: int = 7, agent: str = ""):
    """取得異常通知歷史紀錄（含已關閉）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    days = min(days, 30)
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = sqlite3.connect(METRICS_DB)
        if agent:
            rows = conn.execute(
                "SELECT id, ts, agent, level, message, dismissed FROM alerts WHERE ts >= ? AND agent = ? ORDER BY ts DESC",
                (since, agent),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, ts, agent, level, message, dismissed FROM alerts WHERE ts >= ? ORDER BY ts DESC",
                (since,),
            ).fetchall()
        conn.close()
        alerts = [{"id": r[0], "ts": r[1], "agent": r[2], "level": r[3], "message": r[4], "dismissed": bool(r[5])} for r in rows]
        return JSONResponse({"alerts": alerts})
    except Exception as e:
        return JSONResponse({"alerts": [], "error": str(e)})


@app.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    return HTMLResponse((DIST_DIR / "index.html").read_text())


def _parse_cpu_milli(val: str) -> float:
    """Parse CPU string to millicores (numeric)."""
    try:
        if val.endswith("n"):
            return int(val[:-1]) / 1_000_000
        elif val.endswith("m"):
            return int(val[:-1])
        else:
            return int(val) * 1000
    except ValueError:
        return 0


def _parse_memory_mb(val: str) -> float:
    """Parse memory string to MB (numeric)."""
    try:
        if val.endswith("Ki"):
            return int(val[:-2]) / 1024
        elif val.endswith("Mi"):
            return int(val[:-2])
        elif val.endswith("Gi"):
            return int(val[:-2]) * 1024
        else:
            return int(val) / (1024 * 1024)
    except ValueError:
        return 0


def _parse_cpu(val: str) -> str:
    """Parse CPU like '1234567n' or '5m' to percentage of 1 core."""
    milli = _parse_cpu_milli(val)
    if milli == 0 and val not in ("0", "0m", "0n"):
        return val
    pct = milli / 10  # 1000m = 1 core = 100%
    if pct < 0.1:
        return "<0.1%"
    return f"{pct:.1f}%"


def _parse_memory(val: str) -> str:
    """Parse memory like '91234Ki' to MB."""
    mb = _parse_memory_mb(val)
    if mb == 0 and val not in ("0", "0Ki", "0Mi", "0Gi"):
        return val
    if mb >= 1024:
        return f"{mb / 1024:.1f} GB"
    return f"{mb:.0f} MB"


def _find_pod_for_agent(agent_name: str, pods) -> dict:
    """Find pod matching the agent and extract status info."""
    for pod in pods:
        labels = pod.metadata.labels or {}
        if labels.get("app") == agent_name:
            phase = pod.status.phase  # Running, Pending, Failed, Succeeded, Unknown
            started_at = None
            ready = False
            restart_count = 0

            if pod.status.container_statuses:
                cs = pod.status.container_statuses[0]
                restart_count = cs.restart_count or 0
                ready = cs.ready or False
                if cs.state and cs.state.running:
                    started_at = cs.state.running.started_at

            uptime = _calc_uptime(started_at) if started_at else "-"
            status = "running" if phase == "Running" and ready else phase.lower()

            return {
                "status": status,
                "uptime": uptime,
                "restarts": restart_count,
                "pod_name": pod.metadata.name,
            }
    return {"status": "not_found", "uptime": "-", "restarts": 0, "pod_name": None}


def _calc_uptime(started_at) -> str:
    """Calculate human-readable uptime."""
    if not started_at:
        return "-"
    try:
        if isinstance(started_at, str):
            started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        else:
            started = started_at
        delta = datetime.now(timezone.utc) - started
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes = remainder // 60
        if days > 0:
            return f"{days}天{hours}時"
        elif hours > 0:
            return f"{hours}時{minutes}分"
        else:
            return f"{minutes}分"
    except Exception:
        return "?"


def _mock_status() -> list:
    """Return mock data when K8s is not available (development mode)."""
    return [
        {
            "name": a["name"],
            "display": a["display"],
            "role": a["role"],
            "type": a["type"],
            "status": "unknown",
            "uptime": "-",
            "restarts": 0,
            "pod_name": None,
        }
        for a in AGENTS
    ]

# ─── Cost Monitoring APIs ─────────────────────────────────
@app.get("/costs", response_class=HTMLResponse)
async def costs_page(request: Request):
    """成本監控頁面"""
    return HTMLResponse((DIST_DIR / "index.html").read_text())


@app.get("/api/costs/kiro-usage")
async def api_kiro_usage(request: Request, range: str = "1", refresh: str = "0"):
    """查詢 Kiro 額度消耗（有快取，refresh=1 強制重新查詢）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        import json as json_mod
        cache_key = f"kiro_usage_{range}"
        conn = sqlite3.connect(METRICS_DB)
        conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, data TEXT, ts TEXT)")
        if refresh != "1":
            row = conn.execute("SELECT data, ts FROM cache WHERE key = ? AND ts > datetime('now', '-1 hour')", (cache_key,)).fetchone()
            if row:
                conn.close()
                return JSONResponse({"error": None, "data": json_mod.loads(row[0]), "cached": True})
        conn.close()

        from query_usage import get_usage_data, query_usage
        data = get_usage_data(range)

        # Also compute daily_totals for chart
        if data.get("periods"):
            from collections import defaultdict
            p = data["periods"][0]  # Use first period's date range
            # Aggregate from raw user data by date
            daily = defaultdict(lambda: {"credits": 0, "messages": 0, "conversations": 0})
            for u in p.get("raw_data", []):
                d = daily[u["date"]]
                d["credits"] += u.get("credits_used", 0) or u.get("credits", 0)
                d["messages"] += u.get("total_messages", 0) or u.get("messages", 0)
                d["conversations"] += u.get("chat_conversations", 0) or u.get("conversations", 0)

            if not daily:
                # Fallback: try query directly
                try:
                    from datetime import date
                    raw = query_usage(p.get("_start", date.today()), p.get("_end", date.today()))
                    for r in raw:
                        d = daily[r["date"]]
                        d["credits"] += r.get("credits_used", 0)
                        d["messages"] += r.get("total_messages", 0)
                        d["conversations"] += r.get("chat_conversations", 0)
                except Exception:
                    pass

            data["daily_totals"] = [
                {"date": k, "credits": v["credits"], "messages": v["messages"], "conversations": v["conversations"]}
                for k, v in sorted(daily.items())
            ]

        conn = sqlite3.connect(METRICS_DB)
        conn.execute("INSERT OR REPLACE INTO cache (key, data, ts) VALUES (?, ?, datetime('now'))", (cache_key, json_mod.dumps(data)))
        conn.commit()
        conn.close()

        return JSONResponse({"error": None, "data": data, "cached": False})
    except Exception as e:
        logging.error(f"Kiro usage query failed: {e}")
        return JSONResponse({"error": str(e), "data": None})


@app.get("/api/costs/openai")
async def api_openai_costs(request: Request, range: str = "1", type: str = "all"):
    """查詢 OpenAI 費用與 token 用量（有快取）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        import json as json_mod
        cache_key = f"openai_{range}_{type}"
        conn = sqlite3.connect(METRICS_DB)
        conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, data TEXT, ts TEXT)")
        row = conn.execute("SELECT data, ts FROM cache WHERE key = ? AND ts > datetime('now', '-30 minutes')", (cache_key,)).fetchone()
        conn.close()
        if row:
            return JSONResponse({"error": None, "data": json_mod.loads(row[0]), "cached": True})

        from query_openai_usage import query_costs, query_completions_usage
        result = {}
        if type in ("all", "cost"):
            result["costs"] = await query_costs(range)
        if type in ("all", "tokens"):
            result["tokens"] = await query_completions_usage(range)

        conn = sqlite3.connect(METRICS_DB)
        conn.execute("INSERT OR REPLACE INTO cache (key, data, ts) VALUES (?, ?, datetime('now'))", (cache_key, json_mod.dumps(result)))
        conn.commit()
        conn.close()

        return JSONResponse({"error": None, "data": result, "cached": False})
    except Exception as e:
        logging.error(f"OpenAI usage query failed: {e}")
        return JSONResponse({"error": str(e), "data": None})


# ─── Discord Management APIs ─────────────────────────────
@app.get("/threads", response_class=HTMLResponse)
async def threads_page(request: Request):
    return HTMLResponse((DIST_DIR / "index.html").read_text())


@app.get("/api/discord/members")
async def api_discord_members(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from discord_api import list_members
        members = await list_members(limit=200)
        return JSONResponse({"error": None, "members": members})
    except Exception as e:
        return JSONResponse({"error": str(e), "members": []})


@app.get("/api/discord/roles")
async def api_discord_roles(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from discord_api import list_roles
        roles = await list_roles()
        return JSONResponse({"error": None, "roles": roles})
    except Exception as e:
        return JSONResponse({"error": str(e), "roles": []})


@app.post("/api/discord/members/{user_id}/roles/{role_id}")
async def api_discord_add_role(user_id: str, role_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from discord_api import add_role
        await add_role(user_id, role_id)
        return JSONResponse({"ok": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/discord/members/{user_id}/roles/{role_id}")
async def api_discord_remove_role(user_id: str, role_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from discord_api import remove_role
        await remove_role(user_id, role_id)
        return JSONResponse({"ok": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.patch("/api/discord/members/{user_id}/nick")
async def api_discord_set_nick(user_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    nick = body.get("nick", "").strip()
    try:
        from discord_api import set_nickname
        await set_nickname(user_id, nick)
        return JSONResponse({"ok": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/discord/channels")
async def api_discord_channels(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from discord_api import list_channels
        channels = await list_channels()
        return JSONResponse({"error": None, "channels": channels})
    except Exception as e:
        return JSONResponse({"error": str(e), "channels": []})


@app.post("/api/discord/channels/{channel_id}/messages")
async def api_discord_send_message(channel_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="訊息內容不能為空")
    try:
        from discord_api import send_message
        msg = await send_message(channel_id, content)
        _log_push(user, "discord", channel_id, content)
        return JSONResponse({"ok": True, "message_id": msg.get("id")})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── Messaging APIs ──────────────────────────────────────
def _init_push_table():
    with sqlite3.connect(METRICS_DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS push_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                user_name TEXT NOT NULL,
                platform TEXT NOT NULL,
                target TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'sent',
                scheduled_at TEXT DEFAULT ''
            )
        """)


_init_push_table()


def _log_push(user, platform, target, content, scheduled_at=""):
    tz = timezone(timedelta(hours=8))
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(METRICS_DB)
    conn.execute("INSERT INTO push_history (ts, user_name, platform, target, content, status, scheduled_at) VALUES (?, ?, ?, ?, ?, 'sent', ?)",
                 (now_str, user["name"], platform, target, content[:200], scheduled_at))
    conn.commit()
    conn.close()


@app.get("/api/messaging/history")
async def api_messaging_history(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    conn = sqlite3.connect(METRICS_DB)
    rows = conn.execute("SELECT ts, user_name, platform, target, content, status, scheduled_at FROM push_history ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return JSONResponse({"history": [{"ts": r[0], "user": r[1], "platform": r[2], "target": r[3], "content": r[4], "status": r[5], "scheduled_at": r[6]} for r in rows]})


@app.post("/api/messaging/wecom")
async def api_messaging_wecom(request: Request):
    """推送訊息到企業微信 webhook"""
    import httpx
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="請求格式錯誤")
    content = body.get("content", "").strip() if isinstance(body, dict) else ""
    webhook_url = body.get("webhook_url", "").strip() if isinstance(body, dict) else ""
    if not content:
        raise HTTPException(status_code=400, detail="訊息內容不能為空")
    if not webhook_url:
        raise HTTPException(status_code=400, detail="請提供 Webhook URL")
    from urllib.parse import urlparse
    parsed = urlparse(webhook_url)
    if parsed.hostname != "qyapi.weixin.qq.com":
        raise HTTPException(status_code=400, detail="僅允許企業微信官方 Webhook 域名（qyapi.weixin.qq.com）")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(webhook_url, json={"msgtype": "text", "text": {"content": content}})
            r.raise_for_status()
        _log_push(user, "wecom", "webhook", content)
        return JSONResponse({"ok": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"推送失敗：{e}")


@app.post("/api/messaging/schedule")
async def api_messaging_schedule(request: Request):
    """排程推送（寫入 push_history 標記 scheduled）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="請求格式錯誤")
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="請求格式錯誤")
    content = body.get("content", "").strip()
    platform = body.get("platform", "")
    target = body.get("target", "")
    scheduled_at = body.get("scheduled_at", "")
    if not content or not scheduled_at:
        raise HTTPException(status_code=400, detail="請填寫內容和排程時間")
    tz = timezone(timedelta(hours=8))
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(METRICS_DB)
    conn.execute("INSERT INTO push_history (ts, user_name, platform, target, content, status, scheduled_at) VALUES (?, ?, ?, ?, ?, 'scheduled', ?)",
                 (now_str, user["name"], platform, target, content[:200], scheduled_at))
    conn.commit()
    conn.close()
    return JSONResponse({"ok": True, "message": f"已排程於 {scheduled_at} 發送"})


@app.get("/api/discord/threads")
async def api_discord_threads(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from discord_api import list_active_threads, list_channels, list_forum_tags
        threads = await list_active_threads()
        channels = await list_channels()
        # 過濾掉舊版頻道
        EXCLUDED_CHANNEL_IDS = {"1492090122257170526", "1503703338800382002", "1508387929364631562"}
        old_channel_ids = EXCLUDED_CHANNEL_IDS
        threads = [t for t in threads if t.get("parent_id") not in old_channel_ids]
        # Get tags for forum channels
        forum_channels = [c for c in channels if c["type"] == 15 and c["id"] not in EXCLUDED_CHANNEL_IDS]
        tags_map = {}
        for fc in forum_channels:
            try:
                tags = await list_forum_tags(fc["id"])
                tags_map[fc["id"]] = tags
            except Exception:
                pass
        return JSONResponse({"error": None, "threads": threads, "tags_map": tags_map, "channels": channels})
    except Exception as e:
        return JSONResponse({"error": str(e), "threads": [], "tags_map": {}, "channels": []})


@app.post("/api/discord/threads/{thread_id}/archive")
async def api_discord_archive_thread(thread_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from discord_api import archive_thread
        await archive_thread(thread_id)
        return JSONResponse({"ok": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/discord/threads/{thread_id}/tags")
async def api_discord_update_tags(thread_id: str, request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    tag_ids = body.get("tag_ids", [])
    try:
        from discord_api import update_thread_tags
        await update_thread_tags(thread_id, tag_ids)
        return JSONResponse({"ok": True})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/discord/threads/{thread_id}/messages")
async def api_discord_thread_messages(thread_id: str, request: Request, limit: int = 10, before: str = "", mode: str = "preview"):
    """取得討論串訊息。mode=preview 最後N則（分頁），mode=all 全部（分析用，有快取）"""
    import json as json_mod
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        from discord_api import get_channel_messages, NICK_MAP

        if mode == "all":
            # Full fetch for analytics (cached 1 hour)
            cache_key = f"thread_msgs_{thread_id}"
            conn = sqlite3.connect(METRICS_DB)
            conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, data TEXT, ts TEXT)")
            row = conn.execute("SELECT data FROM cache WHERE key = ? AND ts > datetime('now', '-1 hour')", (cache_key,)).fetchone()
            conn.close()
            if row:
                return JSONResponse(json_mod.loads(row[0]))

            all_msgs = []
            bf = None
            for _ in range(20):
                msgs = await get_channel_messages(thread_id, limit=100, before=bf)
                if not msgs:
                    break
                all_msgs.extend(msgs)
                bf = msgs[-1]["id"]
                if len(msgs) < 100:
                    break
            messages = []
            for m in all_msgs:
                author = m.get("author", {})
                uid = author.get("id", "")
                display = NICK_MAP.get(uid) or author.get("global_name") or author.get("username", "")
                messages.append({"timestamp": m["timestamp"], "author": display, "author_id": uid, "is_bot": author.get("bot", False), "avatar": f"https://cdn.discordapp.com/avatars/{uid}/{author.get('avatar')}.png?size=32" if author.get("avatar") else None})
            result = {"error": None, "messages": messages, "total": len(messages), "has_more": False}
            conn = sqlite3.connect(METRICS_DB)
            conn.execute("INSERT OR REPLACE INTO cache (key, data, ts) VALUES (?, ?, datetime('now'))", (cache_key, json_mod.dumps(result)))
            conn.commit()
            conn.close()
            return JSONResponse(result)

        # Preview mode — last N messages
        import re
        def resolve_mentions(content, mentions_list):
            """Replace <@id> with display name."""
            def repl(match):
                uid = match.group(1)
                # Check mentions list from message
                for u in mentions_list:
                    if u.get("id") == uid:
                        return f"@{NICK_MAP.get(uid) or u.get('global_name') or u.get('username', uid)}"
                # Fallback to NICK_MAP
                if uid in NICK_MAP:
                    return f"@{NICK_MAP[uid]}"
                return match.group(0)
            return re.sub(r'<@!?(\d+)>', repl, content) if content else ""

        msgs = await get_channel_messages(thread_id, limit=min(limit, 100), before=before or None)
        messages = []
        for m in msgs:
            author = m.get("author", {})
            uid = author.get("id", "")
            display = NICK_MAP.get(uid) or author.get("global_name") or author.get("username", "")
            messages.append({
                "id": m.get("id"),
                "timestamp": m["timestamp"],
                "author": display,
                "author_id": uid,
                "is_bot": author.get("bot", False),
                "avatar": f"https://cdn.discordapp.com/avatars/{uid}/{author.get('avatar')}.png?size=32" if author.get("avatar") else None,
                "content": resolve_mentions(m.get("content", ""), m.get("mentions", []))[:500],
                "attachments": len(m.get("attachments", [])),
            })
        return JSONResponse({"error": None, "messages": messages, "has_more": len(msgs) == min(limit, 100)})
    except Exception as e:
        return JSONResponse({"error": str(e), "messages": [], "has_more": False})


@app.get("/api/discord/activity")
async def api_discord_activity(request: Request):
    """Forum 討論串活躍度分析（有快取）"""
    import json as json_mod
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        # Check cache
        cache_key = "discord_activity"
        conn = sqlite3.connect(METRICS_DB)
        conn.execute("CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, data TEXT, ts TEXT)")
        row = conn.execute("SELECT data, ts FROM cache WHERE key = ? AND ts > datetime('now', '-10 minutes')", (cache_key,)).fetchone()
        conn.close()
        if row:
            return JSONResponse({"error": None, **json_mod.loads(row[0]), "cached": True})

        from discord_api import list_active_threads, list_channels, list_forum_tags
        threads = await list_active_threads()
        channels = await list_channels()

        # 過濾掉舊版（準備關閉）頻道的 threads
        EXCLUDED_CHANNEL_IDS = {"1492090122257170526", "1503703338800382002", "1508387929364631562"}
        old_channel_ids = EXCLUDED_CHANNEL_IDS
        threads = [t for t in threads if t.get("parent_id") not in old_channel_ids]

        # Get tags for forum channels
        forum_channels = [c for c in channels if c["type"] == 15 and c["id"] not in EXCLUDED_CHANNEL_IDS]
        tags_map = {}
        for fc in forum_channels:
            try:
                tags = await list_forum_tags(fc["id"])
                tags_map[fc["id"]] = tags
            except Exception:
                pass

        # Build daily creation chart (group threads by created date)
        from collections import defaultdict
        daily_posts = defaultdict(int)
        for t in threads:
            if t.get("created_at"):
                try:
                    date_str = t["created_at"][:10]  # YYYY-MM-DD
                    daily_posts[date_str] += 1
                except Exception:
                    pass

        daily_chart = [{"date": k, "count": v} for k, v in sorted(daily_posts.items())]

        # Top threads by message count
        top_threads = sorted(threads, key=lambda x: x.get("message_count", 0), reverse=True)[:20]
        top_list = []
        for t in top_threads:
            parent_name = next((c["name"] for c in channels if c["id"] == t.get("parent_id")), "")
            tag_names = []
            parent_tags = tags_map.get(t.get("parent_id"), [])
            for tid in t.get("applied_tags", []):
                tag = next((tg for tg in parent_tags if tg["id"] == tid), None)
                if tag:
                    tag_names.append(tag["name"])
            top_list.append({
                "id": t["id"], "name": t["name"], "message_count": t.get("message_count", 0),
                "parent": parent_name, "tags": tag_names, "created_at": t.get("created_at", "")[:10],
                "last_activity": t.get("last_activity", ""),
                "owner_id": t.get("owner_id", ""),
            })

        # Summary
        result = {
            "total_threads": len(threads),
            "forum_count": len(forum_channels),
            "daily_chart": daily_chart,
            "top_threads": top_list,
        }

        # Store cache
        conn = sqlite3.connect(METRICS_DB)
        conn.execute("INSERT OR REPLACE INTO cache (key, data, ts) VALUES (?, ?, datetime('now'))", (cache_key, json_mod.dumps(result)))
        conn.commit()
        conn.close()

        return JSONResponse({"error": None, **result, "cached": False})
    except Exception as e:
        logging.error(f"Discord activity failed: {e}")
        return JSONResponse({"error": str(e), "total_threads": 0, "daily_chart": [], "top_threads": []})


# ─── Agent Config APIs ────────────────────────────────────
def _parse_skill_meta(skill_dir: Path) -> dict:
    """Parse SKILL.md frontmatter (name, description)."""
    skill_md = skill_dir / "SKILL.md"
    meta = {"name": skill_dir.name, "description": ""}
    if not skill_md.exists():
        return meta
    try:
        text = skill_md.read_text()
        if text.startswith("---"):
            end = text.find("---", 3)
            if end > 0:
                fm = text[3:end]
                for line in fm.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in ("name", "description"):
                            meta[k] = v
    except Exception:
        pass
    return meta


def _parse_cronjob_toml(content: str) -> list:
    """Parse cronjob.toml into structured job list."""
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        data = tomllib.loads(content)
        return data.get("jobs", [])
    except Exception:
        return []


def _read_kb_contexts(kb_path: Path) -> list:
    """Read contexts.json and merge file size/mtime info."""
    import json as json_mod
    contexts_file = kb_path / "kiro_default" / "contexts.json"
    if not contexts_file.exists():
        return []
    try:
        ctx_data = json_mod.loads(contexts_file.read_text())
        result = []
        for cid, c in ctx_data.items():
            ctx_dir = kb_path / "kiro_default" / cid
            size = 0
            if ctx_dir.exists():
                for f in ctx_dir.rglob("*"):
                    if f.is_file():
                        size += f.stat().st_size
            result.append({
                "id": cid,
                "name": c.get("name", cid),
                "description": c.get("description", ""),
                "source_path": c.get("source_path", ""),
                "item_count": c.get("item_count", 0),
                "updated_at": c.get("updated_at", ""),
                "persistent": c.get("persistent", False),
                "auto_sync": c.get("auto_sync", False),
                "size_bytes": size,
            })
        return result
    except Exception:
        return []


@app.get("/api/agents")
async def api_agents_list(request: Request):
    """列出所有角色及其配置摘要"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    import json as json_mod
    agents_dir = AGENTS_DIR
    result = []
    for agent in AGENTS:
        name = agent["name"]
        agent_path = agents_dir / name
        if not agent_path.is_dir():
            continue
        # MCP config
        mcp_path = agent_path / ".kiro" / "settings" / "mcp.json"
        mcp_servers = 0
        mcp_enabled = 0
        if mcp_path.exists():
            try:
                data = json_mod.loads(mcp_path.read_text())
                servers = data.get("mcpServers", {})
                mcp_servers = len(servers)
                mcp_enabled = sum(1 for s in servers.values() if not s.get("disabled", False))
            except Exception:
                pass
        # Skills (resolve symlinks)
        skills_path = agent_path / ".kiro" / "skills"
        skills_meta = []
        if skills_path.exists():
            for d in sorted(skills_path.iterdir()):
                if d.is_dir() or d.is_symlink():
                    target = d.resolve() if d.is_symlink() else d
                    if target.is_dir():
                        skills_meta.append(_parse_skill_meta(target))
        # Steering
        steering_path = agent_path / ".kiro" / "steering"
        steering = sorted([f.name for f in steering_path.iterdir() if f.suffix == ".md"]) if steering_path.exists() else []
        # Cronjob
        cron_path = agent_path / ".openab" / "cronjob.toml"
        cron_jobs = []
        if cron_path.exists():
            cron_jobs = _parse_cronjob_toml(cron_path.read_text())
        # KB
        kb_path = agent_path / ".local" / "share" / "kiro-cli" / "knowledge_bases"
        kb_count = len(_read_kb_contexts(kb_path)) if kb_path.exists() else 0

        result.append({
            "name": name,
            "display": agent["display"],
            "role": agent["role"],
            "mcp_servers": mcp_servers,
            "mcp_enabled": mcp_enabled,
            "skills_count": len(skills_meta),
            "steering_count": len(steering),
            "cronjob_count": len(cron_jobs),
            "cronjob_enabled": sum(1 for j in cron_jobs if j.get("enabled", False)),
            "kb_count": kb_count,
            "skills": [s["name"] for s in skills_meta],
            "skills_meta": skills_meta,
            "steering": steering,
        })
    return JSONResponse({"agents": result})


@app.get("/api/agents/{agent_name}/config")
async def api_agent_config(agent_name: str, request: Request):
    """取得角色的 config.toml"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    config_path = AGENTS_DIR / agent_name / "config.toml"
    if not config_path.exists():
        return JSONResponse({"error": None, "raw": ""})
    try:
        return JSONResponse({"error": None, "raw": config_path.read_text()})
    except Exception as e:
        return JSONResponse({"error": str(e), "raw": ""})


@app.put("/api/agents/{agent_name}/config")
async def api_agent_config_save(agent_name: str, request: Request):
    """儲存角色的 config.toml"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="請求格式錯誤")
    raw = body.get("raw", "") if isinstance(body, dict) else ""
    config_path = AGENTS_DIR / agent_name / "config.toml"
    if not config_path.parent.exists():
        raise HTTPException(status_code=404, detail="Agent 不存在")
    config_path.write_text(raw)
    return JSONResponse({"ok": True, "message": "已儲存"})


@app.get("/api/agents/{agent_name}/mcp")
async def api_agent_mcp(agent_name: str, request: Request):
    """取得角色的 MCP 配置"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    import json as json_mod
    mcp_path = AGENTS_DIR / agent_name / ".kiro" / "settings" / "mcp.json"
    if not mcp_path.exists():
        return JSONResponse({"error": None, "config": {}, "raw": "{}"})
    try:
        raw = mcp_path.read_text()
        config = json_mod.loads(raw)
        return JSONResponse({"error": None, "config": config, "raw": raw})
    except Exception as e:
        return JSONResponse({"error": str(e), "config": {}, "raw": ""})


@app.put("/api/agents/{agent_name}/mcp")
async def api_agent_mcp_save(agent_name: str, request: Request):
    """儲存角色的 MCP 配置"""
    import json as json_mod
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    raw = body.get("raw", "")
    # Validate JSON
    try:
        json_mod.loads(raw)
    except json_mod.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON 語法錯誤：{e}")
    mcp_path = AGENTS_DIR / agent_name / ".kiro" / "settings" / "mcp.json"
    mcp_path.parent.mkdir(parents=True, exist_ok=True)
    mcp_path.write_text(raw)
    return JSONResponse({"ok": True, "message": "已儲存"})


@app.get("/api/agents/{agent_name}/steering/{filename}")
async def api_agent_steering(agent_name: str, filename: str, request: Request):
    """取得 steering 檔案內容"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    path = AGENTS_DIR / agent_name / ".kiro" / "steering" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="檔案不存在")
    return JSONResponse({"content": path.read_text(), "filename": filename})


@app.get("/api/agents/{agent_name}/skills/{skill_name}")
async def api_agent_skill_view(agent_name: str, skill_name: str, request: Request):
    """取得 skill 的 SKILL.md 內容"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    skill_path = AGENTS_DIR / agent_name / ".kiro" / "skills" / skill_name
    if skill_path.is_symlink():
        skill_path = skill_path.resolve()
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        raise HTTPException(status_code=404, detail="SKILL.md 不存在")
    return JSONResponse({"content": skill_md.read_text(), "filename": f"{skill_name}/SKILL.md"})


@app.get("/api/agents/{agent_name}/cronjob")
async def api_agent_cronjob(agent_name: str, request: Request):
    """取得角色的 cronjob 配置（含 raw 與 parsed）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    path = AGENTS_DIR / agent_name / ".openab" / "cronjob.toml"
    if not path.exists():
        return JSONResponse({"content": "", "jobs": []})
    raw = path.read_text()
    return JSONResponse({"content": raw, "jobs": _parse_cronjob_toml(raw)})


@app.put("/api/agents/{agent_name}/cronjob/{job_index}/toggle")
async def api_agent_cronjob_toggle(agent_name: str, job_index: int, request: Request):
    """切換特定 cronjob 的 enabled 狀態"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    path = AGENTS_DIR / agent_name / ".openab" / "cronjob.toml"
    if not path.exists():
        raise HTTPException(status_code=404, detail="cronjob.toml 不存在")
    raw = path.read_text()
    # Find [[jobs]] block boundaries and toggle the job_index-th block's `enabled`
    import re
    # Split by [[jobs]] markers
    blocks = re.split(r'(?=^\[\[jobs\]\])', raw, flags=re.MULTILINE)
    # blocks[0] is preamble (may not have [[jobs]]), rest are job blocks
    job_blocks = [b for b in blocks if b.startswith("[[jobs]]")]
    preamble = "".join([b for b in blocks if not b.startswith("[[jobs]]")])
    if job_index < 0 or job_index >= len(job_blocks):
        raise HTTPException(status_code=400, detail=f"job_index 超出範圍：{len(job_blocks)} jobs")
    block = job_blocks[job_index]
    # Toggle enabled = true/false
    if re.search(r'^enabled\s*=\s*true', block, re.MULTILINE):
        new_block = re.sub(r'^enabled\s*=\s*true', 'enabled = false', block, count=1, flags=re.MULTILINE)
    elif re.search(r'^enabled\s*=\s*false', block, re.MULTILINE):
        new_block = re.sub(r'^enabled\s*=\s*false', 'enabled = true', block, count=1, flags=re.MULTILINE)
    else:
        # Add enabled = true after schedule line
        new_block = re.sub(r'(^schedule\s*=.*$)', r'\1\nenabled = true', block, count=1, flags=re.MULTILINE)
    job_blocks[job_index] = new_block
    new_raw = preamble + "".join(job_blocks)
    path.write_text(new_raw)
    return JSONResponse({"ok": True, "jobs": _parse_cronjob_toml(new_raw)})


@app.put("/api/agents/{agent_name}/cronjob")
async def api_agent_cronjob_save(agent_name: str, request: Request):
    """儲存 cronjob.toml raw 內容（搭配 raw editor）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    body = await request.json()
    raw = body.get("content", "")
    # Try parse to validate
    if _parse_cronjob_toml(raw) is None:
        raise HTTPException(status_code=400, detail="TOML 語法錯誤")
    path = AGENTS_DIR / agent_name / ".openab" / "cronjob.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(raw)
    return JSONResponse({"ok": True})


@app.get("/api/agents/{agent_name}/kb")
async def api_agent_kb(agent_name: str, request: Request):
    """取得角色的 Knowledge Base 列表（從 contexts.json 讀人類可讀名稱）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    kb_path = AGENTS_DIR / agent_name / ".local" / "share" / "kiro-cli" / "knowledge_bases"
    contexts = _read_kb_contexts(kb_path) if kb_path.exists() else []
    return JSONResponse({"contexts": contexts})


@app.get("/api/agents/{agent_name}/kb/{kb_id}")
async def api_agent_kb_view(agent_name: str, kb_id: str, request: Request):
    """取得 KB 來源檔案資訊（顯示路徑、嘗試讀取內容）"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    import json as json_mod
    kb_path = AGENTS_DIR / agent_name / ".local" / "share" / "kiro-cli" / "knowledge_bases"
    contexts_file = kb_path / "kiro_default" / "contexts.json"
    if not contexts_file.exists():
        raise HTTPException(status_code=404, detail="contexts.json 不存在")
    try:
        ctx_data = json_mod.loads(contexts_file.read_text())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"contexts.json 解析失敗：{e}")
    if kb_id not in ctx_data:
        raise HTTPException(status_code=404, detail="KB context 不存在")
    ctx = ctx_data[kb_id]
    # Try to read source file content (read-only preview)
    source_path = ctx.get("source_path", "")
    content = ""
    content_error = ""
    if source_path:
        try:
            sp = Path(source_path)
            if sp.exists() and sp.is_file():
                content = sp.read_text(errors="replace")
            else:
                content_error = f"來源檔案不存在或無法讀取：{source_path}"
        except Exception as e:
            content_error = f"讀取錯誤：{e}"
    return JSONResponse({
        "context": ctx,
        "content": content,
        "content_error": content_error,
    })


# ─── SPA catch-all for client-side routes ───
SPA_ROUTES = ["/login", "/messaging", "/members", "/threads", "/thread-analytics",
              "/agent-config", "/cronjobs", "/knowledge",
              "/system", "/logs", "/deploy", "/api-keys"]

for _route in SPA_ROUTES:
    @app.get(_route, response_class=HTMLResponse)
    async def _spa_page(request: Request, _r=_route):
        return HTMLResponse((DIST_DIR / "index.html").read_text())


# ─── Mount Vue SPA dist at root (MUST be LAST, after all routes) ───
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="spa")
