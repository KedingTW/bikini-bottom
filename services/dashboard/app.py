"""🏝️ 比奇堡團隊 Dashboard — 角色狀態管理介面"""
import os
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
USERS_FILE = os.environ.get("USERS_FILE", "/etc/dashboard/users.json")
SECRET_KEY = os.environ.get("SESSION_SECRET", "bikini-bottom-dashboard-secret-key-2026")
NAMESPACE = os.environ.get("K8S_NAMESPACE", "bikini-bottom")
BACKEND = os.environ.get("DASHBOARD_BACKEND", "auto")  # "k8s", "docker", or "auto"


def _load_users() -> tuple[set, str]:
    """Load users from mounted JSON file, with fallback defaults."""
    try:
        import json
        with open(USERS_FILE) as f:
            data = json.load(f)
        return set(data.get("users", [])), data.get("password", "")
    except Exception:
        logging.warning(f"⚠️ 無法讀取 {USERS_FILE}，使用內建預設帳號")
        return {"11021395"}, "kd-22963999"


AUTH_USERS, AUTH_PASSWORD = _load_users()

# ─── App Setup ────────────────────────────────────────────
app = FastAPI(title="比奇堡 Dashboard", docs_url=None, redoc_url=None)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

BASE_DIR = Path(__file__).resolve().parent
AGENTS_DIR = Path(os.environ.get("AGENTS_DIR", "/data/agents"))
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

serializer = URLSafeTimedSerializer(SECRET_KEY)

# ─── Agent 角色定義 ───────────────────────────────────────
AGENTS = [
    {"name": "bob", "display": "🧽 海綿寶寶", "role": "全端工程師", "type": "agent", "icon": "🧽"},
    {"name": "patrick", "display": "⭐ 派大星", "role": "後端工程師", "type": "agent", "icon": "⭐"},
    {"name": "pearl", "display": "🐋 珍珍", "role": "全端工程師", "type": "agent", "icon": "🐋"},
    {"name": "larry", "display": "🦞 蝦霸", "role": "後端工程師", "type": "agent", "icon": "🦞"},
    {"name": "squidward", "display": "🦑 章魚哥", "role": "專案經理", "type": "agent", "icon": "🦑"},
    {"name": "sandy", "display": "🐿️ 珊迪", "role": "客戶成功經理", "type": "agent", "icon": "🐿️"},
    {"name": "puff", "display": "🐡 泡芙老師", "role": "Code Review", "type": "agent", "icon": "🐡"},
    {"name": "conch", "display": "🐚 神奇海螺", "role": "團隊神諭者", "type": "agent", "icon": "🐚"},
    {"name": "mermaid-man", "display": "🦸 海超人", "role": "DevOps", "type": "agent", "icon": "🦸"},
    {"name": "slash-bot", "display": "🐌 小蝸", "role": "維運助手", "type": "service", "icon": "🐌"},
    {"name": "gateway", "display": "🌐 Gateway", "role": "WeCom 閘道", "type": "service", "icon": "🌐"},
    {"name": "wecom-bot", "display": "💬 企微Bot", "role": "企業微信", "type": "service", "icon": "💬"},
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
def get_current_user(request: Request) -> str | None:
    """Check session for logged-in user."""
    token = request.session.get("auth_token")
    if not token:
        return None
    try:
        data = serializer.loads(token, max_age=86400)  # 24hr expiry
        return data.get("user")
    except Exception:
        return None


def require_auth(request: Request):
    """Dependency that enforces authentication."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


# ─── Routes ──────────────────────────────────────────────
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login_submit(request: Request, username: str = Form(...), password: str = Form(...)):
    if username in AUTH_USERS and password == AUTH_PASSWORD:
        token = serializer.dumps({"user": username})
        request.session["auth_token"] = token
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "帳號或密碼錯誤"})


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse("dashboard.html", {"request": request, "agents": AGENTS, "user": user})


@app.get("/avatar/{agent_name}")
async def avatar(agent_name: str):
    """Serve agent avatar image. Falls back to 404 if not found."""
    valid_names = {a["name"] for a in AGENTS}
    # slash-bot uses gary's avatar
    avatar_map = {"slash-bot": "gary"}
    lookup_name = avatar_map.get(agent_name, agent_name)

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


# ─── Helpers ──────────────────────────────────────────────
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
            return f"{days}d {hours}h"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
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
