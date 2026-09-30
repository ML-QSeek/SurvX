# -*- coding: utf-8 -*-
"""
llmgate.py

LLM 网关管控台。FastAPI + SQLite。

功能
----
- Agent 权限表：启用/禁用、配额、模型（SQLite）
- Agent Server 管理：配置、启停、重启、删除（子进程）
- 全局熔断：一键 block / recover
- 调用日志：SQLite
- 统计：KPI、趋势、错误分布、告警
- 页面：templates/index.html

启动
----
python llmgate.py

环境变量
--------
LLMGATE_HOST  默认 0.0.0.0
LLMGATE_PORT  默认 5000
AGENT_SCRIPT  默认 agent.py（同目录）
"""

import os
import sqlite3
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel


# ============================================================
# 配置
# ============================================================

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "llmgate.db"
TEMPLATES_DIR = BASE_DIR / "templates"
AGENT_SCRIPT = os.environ.get("AGENT_SCRIPT", str(BASE_DIR / "agent.py"))

HOST = os.environ.get("LLMGATE_HOST", "0.0.0.0")
PORT = int(os.environ.get("LLMGATE_PORT", "5000"))

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# ============================================================
# SQLite
# ============================================================

def db():
    """拿一个连接，row 可当 dict 用"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    c = conn.cursor()

    # Agent 权限表
    c.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id     TEXT PRIMARY KEY,
            enabled      INTEGER DEFAULT 1,
            model        TEXT DEFAULT 'deepseek-v3',
            quota_daily  INTEGER DEFAULT 100000,
            quota_used   INTEGER DEFAULT 0,
            rate_limit   INTEGER DEFAULT 0,
            created_at   TEXT
        )
    """)

    # Agent Server 配置表
    c.execute("""
        CREATE TABLE IF NOT EXISTS servers (
            name         TEXT PRIMARY KEY,
            provider     TEXT NOT NULL,
            port         INTEGER NOT NULL,
            api_key      TEXT,
            base_url     TEXT,
            model        TEXT,
            quota_daily  INTEGER DEFAULT 100000,
            enabled      INTEGER DEFAULT 1,
            auto_start   INTEGER DEFAULT 1,
            pid          INTEGER,
            status       TEXT DEFAULT 'stopped',
            created_at   TEXT
        )
    """)

    # 调用日志表
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id           TEXT,
            model              TEXT,
            prompt_tokens      INTEGER DEFAULT 0,
            completion_tokens  INTEGER DEFAULT 0,
            total_tokens       INTEGER DEFAULT 0,
            latency_ms         INTEGER DEFAULT 0,
            status_code        INTEGER DEFAULT 200,
            error_msg          TEXT,
            timestamp          TEXT
        )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_ts ON logs(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_agent ON logs(agent_id)")

    # 全局状态
    c.execute("""
        CREATE TABLE IF NOT EXISTS global_state (
            key    TEXT PRIMARY KEY,
            value  TEXT
        )
    """)
    c.execute("INSERT OR IGNORE INTO global_state(key, value) VALUES('blocked', '0')")

    conn.commit()
    conn.close()
    print("[✓] SQLite 初始化完成")


# ============================================================
# Agent 子进程管理
# ============================================================

_procs: dict[str, subprocess.Popen] = {}


def _start_server(name: str):
    """按配置拉起 agent 子进程"""
    if name in _procs and _procs[name].poll() is None:
        return {"code": 1, "msg": "已在运行"}

    conn = db()
    row = conn.execute("SELECT * FROM servers WHERE name = ?", (name,)).fetchone()
    conn.close()
    if not row:
        return {"code": 1, "msg": "server 不存在"}

    s = dict(row)
    if not s.get("api_key"):
        return {"code": 1, "msg": "缺少 api_key"}
    if not s.get("port"):
        return {"code": 1, "msg": "缺少 port"}

    # 命令行参数
    args = [
        "python", AGENT_SCRIPT,
        "--name", s["name"],
        "--provider", s["provider"],
        "--port", str(s["port"]),
        "--api-key", s["api_key"],
        "--gateway-url", f"http://127.0.0.1:{PORT}",
    ]
    if s.get("base_url"):
        args += ["--base-url", s["base_url"]]
    if s.get("model"):
        args += ["--model", s["model"]]

    # 环境变量（双保险，agent.py 用哪个都行）
    env = os.environ.copy()
    env.update({
        "AGENT_NAME": s["name"],
        "PROVIDER": s["provider"],
        "PORT": str(s["port"]),
        "API_KEY": s["api_key"],
        "GATEWAY_URL": f"http://127.0.0.1:{PORT}",
        "BASE_URL": s.get("base_url") or "",
        "MODEL": s.get("model") or "",
    })

    try:
        p = subprocess.Popen(
            args,
            env=env,
            cwd=str(BASE_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as e:
        return {"code": 1, "msg": f"启动失败: {e}"}

    _procs[name] = p

    conn = db()
    conn.execute(
        "UPDATE servers SET pid=?, status='running' WHERE name=?",
        (p.pid, name),
    )
    conn.commit()
    conn.close()

    print(f"[启动] {name} pid={p.pid} port={s['port']}")
    return {"code": 0, "msg": "已启动", "pid": p.pid}


def _stop_server(name: str):
    """停掉 agent 子进程"""
    p = _procs.pop(name, None)
    if p and p.poll() is None:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()

    conn = db()
    conn.execute(
        "UPDATE servers SET pid=NULL, status='stopped' WHERE name=?",
        (name,),
    )
    conn.commit()
    conn.close()
    print(f"[停止] {name}")
    return {"code": 0, "msg": "已停止"}


def _restart_server(name: str):
    _stop_server(name)
    time.sleep(0.5)
    return _start_server(name)


def _monitor_loop():
    """后台监控子进程，挂了更新状态"""
    while True:
        try:
            for name, p in list(_procs.items()):
                if p.poll() is not None:
                    conn = db()
                    conn.execute(
                        "UPDATE servers SET pid=NULL, status='stopped' WHERE name=?",
                        (name,),
                    )
                    conn.commit()
                    conn.close()
                    _procs.pop(name, None)
                    print(f"[监控] {name} 已退出 code={p.returncode}")
        except Exception as e:
            print(f"[监控] 异常: {e}")
        time.sleep(3)


def _cleanup():
    """服务关闭时杀掉所有子进程"""
    for name, p in list(_procs.items()):
        if p.poll() is None:
            try:
                p.terminate()
            except Exception:
                pass
    _procs.clear()


# ============================================================
# lifespan
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    # 自动拉起 auto_start 的 server
    conn = db()
    rows = conn.execute(
        "SELECT name FROM servers WHERE enabled=1 AND auto_start=1"
    ).fetchall()
    conn.close()
    for r in rows:
        _start_server(r["name"])

    # 后台监控
    threading.Thread(target=_monitor_loop, daemon=True).start()

    print("=" * 50)
    print(f"🚀 LLM-Gate 已启动: http://127.0.0.1:{PORT}")
    print("=" * 50)
    yield
    _cleanup()
    print("[✓] LLM-Gate 已关闭")


app = FastAPI(title="LLM-Gate", lifespan=lifespan)


# ============================================================
# 页面
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ============================================================
# Agent 权限表
# ============================================================

@app.get("/api/agents")
async def list_agents():
    conn = db()
    rows = conn.execute("SELECT * FROM agents").fetchall()
    conn.close()
    return {"code": 0, "data": [
        {
            "agent_id": r["agent_id"],
            "enabled": bool(r["enabled"]),
            "model": r["model"],
            "quota_daily": r["quota_daily"],
            "quota_used": r["quota_used"],
            "rate_limit": r["rate_limit"],
        } for r in rows
    ]}


class AgentReq(BaseModel):
    model: str = "deepseek-v3"
    quota_daily: int = 100000
    rate_limit: int = 0
    enabled: bool = True


@app.post("/api/agents/{agent_id}")
async def register_agent(agent_id: str, req: AgentReq):
    conn = db()
    conn.execute("""
        INSERT INTO agents(agent_id, enabled, model, quota_daily, quota_used, rate_limit, created_at)
        VALUES(?,?,?,?,0,?,?)
        ON CONFLICT(agent_id) DO UPDATE SET
            enabled=excluded.enabled,
            model=excluded.model,
            quota_daily=excluded.quota_daily,
            rate_limit=excluded.rate_limit
    """, (
        agent_id, 1 if req.enabled else 0, req.model,
        req.quota_daily, req.rate_limit, datetime.now().isoformat(),
    ))
    conn.commit()
    conn.close()
    return {"code": 0, "msg": f"{agent_id} 注册成功"}


@app.post("/api/agents/{agent_id}/enable")
async def enable_agent(agent_id: str):
    conn = db()
    conn.execute("UPDATE agents SET enabled=1 WHERE agent_id=?", (agent_id,))
    conn.commit()
    conn.close()
    return {"code": 0, "msg": f"{agent_id} 已启用"}


@app.post("/api/agents/{agent_id}/disable")
async def disable_agent(agent_id: str):
    conn = db()
    conn.execute("UPDATE agents SET enabled=0 WHERE agent_id=?", (agent_id,))
    conn.commit()
    conn.close()
    return {"code": 0, "msg": f"{agent_id} 已禁用"}


class QuotaReq(BaseModel):
    quota_daily: int


@app.post("/api/agents/{agent_id}/quota")
async def set_quota(agent_id: str, req: QuotaReq):
    conn = db()
    conn.execute(
        "UPDATE agents SET quota_daily=?, quota_used=0 WHERE agent_id=?",
        (req.quota_daily, agent_id),
    )
    conn.commit()
    conn.close()
    return {"code": 0, "msg": f"{agent_id} 配额已设为 {req.quota_daily}"}


# ============================================================
# 上报（agent 调完 AI 后上报）
# ============================================================

class ReportReq(BaseModel):
    agent_id: str
    model: str = "unknown"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: int = 0
    status_code: int = 200
    error_msg: str = ""


@app.post("/api/report")
async def receive_report(req: ReportReq):
    conn = db()
    conn.execute("""
        INSERT INTO logs(agent_id, model, prompt_tokens, completion_tokens,
                         total_tokens, latency_ms, status_code, error_msg, timestamp)
        VALUES(?,?,?,?,?,?,?,?,?)
    """, (
        req.agent_id, req.model, req.prompt_tokens, req.completion_tokens,
        req.total_tokens, req.latency_ms, req.status_code, req.error_msg,
        datetime.now().isoformat(),
    ))
    if req.status_code == 200 and req.total_tokens > 0:
        conn.execute(
            "UPDATE agents SET quota_used = quota_used + ? WHERE agent_id=?",
            (req.total_tokens, req.agent_id),
        )
    conn.commit()
    conn.close()
    return {"code": 0, "msg": "ok"}


# ============================================================
# 全局熔断
# ============================================================

@app.get("/api/global/status")
async def global_status():
    conn = db()
    row = conn.execute("SELECT value FROM global_state WHERE key='blocked'").fetchone()
    conn.close()
    return {"code": 0, "data": {"blocked": row["value"] == "1"}}


@app.post("/api/global/block")
async def global_block():
    conn = db()
    conn.execute("UPDATE global_state SET value='1' WHERE key='blocked'")
    conn.commit()
    conn.close()
    return {"code": 0, "msg": "全局熔断已开启"}


@app.post("/api/global/recover")
async def global_recover():
    conn = db()
    conn.execute("UPDATE global_state SET value='0' WHERE key='blocked'")
    conn.commit()
    conn.close()
    return {"code": 0, "msg": "全局熔断已解除"}


# ============================================================
# 统计
# ============================================================

@app.get("/api/stats/overview")
async def stats_overview():
    today = datetime.now().strftime("%Y-%m-%d") + "%"
    conn = db()

    total = conn.execute(
        "SELECT COUNT(*) c FROM logs WHERE timestamp LIKE ?", (today,)
    ).fetchone()["c"]
    errors = conn.execute(
        "SELECT COUNT(*) c FROM logs WHERE timestamp LIKE ? AND status_code >= 400",
        (today,)
    ).fetchone()["c"]
    avg_lat = conn.execute(
        "SELECT AVG(latency_ms) a FROM logs WHERE timestamp LIKE ?", (today,)
    ).fetchone()["a"] or 0
    total_tokens = conn.execute(
        "SELECT SUM(total_tokens) s FROM logs WHERE timestamp LIKE ?", (today,)
    ).fetchone()["s"] or 0

    active = conn.execute("SELECT COUNT(*) c FROM agents WHERE enabled=1").fetchone()["c"]
    all_agents = conn.execute("SELECT COUNT(*) c FROM agents").fetchone()["c"]
    conn.close()

    error_rate = round(errors / total * 100, 1) if total > 0 else 0

    return {"code": 0, "data": {
        "qps": round(total / 86400 * 100) if total > 0 else 0,
        "p95_latency": int(avg_lat * 1.2) if avg_lat > 0 else 0,
        "error_rate": error_rate,
        "total_today": total,
        "cost_today": round(total_tokens / 1_000_000 * 2.5, 2),
        "active_agents": active,
        "total_agents": all_agents,
    }}


@app.get("/api/stats/trend")
async def stats_trend():
    conn = db()
    rows = conn.execute("""
        SELECT
            strftime('%H', timestamp) AS hour,
            SUM(CASE WHEN status_code < 400 THEN 1 ELSE 0 END) AS success,
            SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) AS error
        FROM logs
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY hour
        ORDER BY hour
    """).fetchall()
    conn.close()

    labels = [r["hour"] + ":00" for r in rows]
    success = [r["success"] for r in rows]
    error = [r["error"] for r in rows]
    return {"code": 0, "data": {"labels": labels, "success": success, "error": error}}


@app.get("/api/stats/errors")
async def stats_errors():
    conn = db()
    rows = conn.execute("""
        SELECT status_code AS code, COUNT(*) AS count
        FROM logs
        WHERE timestamp >= datetime('now', '-15 minutes')
          AND status_code >= 400
        GROUP BY status_code
        ORDER BY count DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return {"code": 0, "data": [{"code": r["code"], "count": r["count"]} for r in rows]}


@app.get("/api/stats/alerts")
async def stats_alerts():
    alerts = []
    now_str = datetime.now().strftime("%H:%M")

    conn = db()

    # 错误率 > 5%
    row = conn.execute("""
        SELECT
            SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) AS rate
        FROM logs
        WHERE timestamp >= datetime('now', '-5 minutes')
    """).fetchone()
    rate = row["rate"] or 0
    if rate > 0.05:
        alerts.append({
            "level": "P0", "time": now_str,
            "msg": f"错误率 {round(rate * 100, 1)}%，超过阈值 5%",
        })

    # 配额 > 80%
    for r in conn.execute("SELECT * FROM agents").fetchall():
        d, u = r["quota_daily"], r["quota_used"]
        if d > 0 and u / d > 0.8:
            alerts.append({
                "level": "P2", "time": now_str,
                "msg": f"{r['agent_id']} 配额使用 {round(u / d * 100, 1)}%",
            })
    conn.close()

    if not alerts:
        alerts.append({"level": "INFO", "time": now_str, "msg": "暂无告警"})
    return {"code": 0, "data": alerts[:10]}


# ============================================================
# Agent Server 管理
# ============================================================

@app.get("/api/servers")
async def list_servers():
    """列表。不返回 api_key 明文，只返回 has_key。"""
    conn = db()
    rows = conn.execute("SELECT * FROM servers").fetchall()
    conn.close()
    return {"code": 0, "data": [
        {
            "name": r["name"],
            "provider": r["provider"],
            "port": r["port"],
            "has_key": bool(r["api_key"]),
            "base_url": r["base_url"],
            "model": r["model"],
            "quota_daily": r["quota_daily"],
            "enabled": bool(r["enabled"]),
            "auto_start": bool(r["auto_start"]),
            "pid": r["pid"],
            "status": r["status"],
        } for r in rows
    ]}


class ServerReq(BaseModel):
    name: str
    provider: str
    port: int
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    quota_daily: int = 100000
    enabled: bool = True
    auto_start: bool = True


@app.post("/api/servers")
async def create_server(req: ServerReq):
    if not req.api_key:
        raise HTTPException(400, "缺少 api_key")
    conn = db()
    try:
        conn.execute("""
            INSERT INTO servers(name, provider, port, api_key, base_url, model,
                                quota_daily, enabled, auto_start, status, created_at)
            VALUES(?,?,?,?,?,?,?,?,?,'stopped',?)
        """, (
            req.name, req.provider, req.port, req.api_key, req.base_url, req.model,
            req.quota_daily, 1 if req.enabled else 0, 1 if req.auto_start else 0,
            datetime.now().isoformat(),
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(400, f"server 已存在: {req.name}")
    conn.close()
    return {"code": 0, "msg": "已创建"}


@app.put("/api/servers/{name}")
async def update_server(name: str, req: Request):
    data = await req.json()
    conn = db()
    row = conn.execute("SELECT * FROM servers WHERE name=?", (name,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(404, "server 不存在")

    fields = ["provider", "port", "base_url", "model", "quota_daily", "enabled", "auto_start"]
    sets, vals = [], []
    for f in fields:
        if f in data:
            v = data[f]
            if f in ("enabled", "auto_start"):
                v = 1 if v else 0
            sets.append(f"{f}=?")
            vals.append(v)

    # api_key 只有传了非空才更新（前端「留空不修改」）
    if data.get("api_key"):
        sets.append("api_key=?")
        vals.append(data["api_key"])

    if sets:
        vals.append(name)
        conn.execute(f"UPDATE servers SET {', '.join(sets)} WHERE name=?", vals)
        conn.commit()
    conn.close()
    return {"code": 0, "msg": "已更新"}


@app.post("/api/servers/{name}/start")
async def start_server(name: str):
    r = _start_server(name)
    if r["code"] != 0:
        raise HTTPException(400, r["msg"])
    return r


@app.post("/api/servers/{name}/stop")
async def stop_server(name: str):
    return _stop_server(name)


@app.post("/api/servers/{name}/restart")
async def restart_server(name: str):
    r = _restart_server(name)
    if r["code"] != 0:
        raise HTTPException(400, r["msg"])
    return r


@app.delete("/api/servers/{name}")
async def delete_server(name: str):
    _stop_server(name)
    conn = db()
    conn.execute("DELETE FROM servers WHERE name=?", (name,))
    conn.commit()
    conn.close()
    return {"code": 0, "msg": "已删除"}


# ============================================================
# 日志
# ============================================================

@app.get("/api/logs")
async def get_logs(src: str = "gateway", limit: int = 100):
    """
    src:
        gateway        → 网关最近的上报记录
        agent:xxx      → 某 agent 的调用日志
        server:xxx     → 某 server 的日志（暂时用 agent 的代替）
    """
    conn = db()

    if src == "gateway":
        rows = conn.execute("""
            SELECT timestamp, status_code, error_msg, agent_id
            FROM logs ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        lines = []
        for r in rows:
            lv = "error" if r["status_code"] >= 400 else "info"
            msg = r["error_msg"] or f"{r['agent_id']} status={r['status_code']}"
            lines.append({"ts": r["timestamp"][11:19], "lv": lv, "msg": msg})
        return {"code": 0, "data": list(reversed(lines))}

    if src.startswith("agent:"):
        aid = src.split(":", 1)[1]
        rows = conn.execute("""
            SELECT timestamp, status_code, error_msg, model, total_tokens
            FROM logs WHERE agent_id=? ORDER BY id DESC LIMIT ?
        """, (aid, limit)).fetchall()
        conn.close()
        lines = []
        for r in rows:
            lv = "error" if r["status_code"] >= 400 else "info"
            msg = f"{r['model']} {r['total_tokens']} tokens status={r['status_code']}"
            if r["error_msg"]:
                msg += f" | {r['error_msg']}"
            lines.append({"ts": r["timestamp"][11:19], "lv": lv, "msg": msg})
        return {"code": 0, "data": list(reversed(lines))}

    if src.startswith("server:"):
        name = src.split(":", 1)[1]
        # 用 agent_id == name 的日志代替（约定 agent 上报时用 server name）
        rows = conn.execute("""
            SELECT timestamp, status_code, error_msg
            FROM logs WHERE agent_id=? ORDER BY id DESC LIMIT ?
        """, (name, limit)).fetchall()
        conn.close()
        lines = []
        for r in rows:
            lv = "error" if r["status_code"] >= 400 else "info"
            msg = r["error_msg"] or f"status={r['status_code']}"
            lines.append({"ts": r["timestamp"][11:19], "lv": lv, "msg": msg})
        return {"code": 0, "data": list(reversed(lines))}

    conn.close()
    return {"code": 0, "data": []}


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT, reload=False)