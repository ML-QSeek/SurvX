#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codefield.py

AI 代码调试器（多项目版，FastAPI，无页面）。

定位
----
9000 是调试节点。接收「写代码 / 修代码 / 跑代码」的指令，
通过 agent（8000）拿代码，本地跑，产出日志 + 版本。

无页面。纯 API。可被前端、脚本、其他服务调用。

功能
----
- 多项目管理（切换、创建、列表）
- 版本管理（每个项目 main_v{n}.py + log_v{n}.txt）
- 调 agent 拿代码
- 本地 subprocess 跑代码
- 上报网关

启动
----
python debugger.py

环境变量
--------
DEBUGGER_HOST       默认 0.0.0.0
DEBUGGER_PORT       默认 9000
GATEWAY_URL         默认 http://127.0.0.1:5000
AGENT_ID            默认 agent-debugger
AGENT_MODEL         默认 deepseek-chat
AGENT_QUOTA_DAILY   默认 500000
API_URL             agent 地址，默认 http://127.0.0.1:8000
WORKSPACE_ROOT      默认 ./workspace
RUN_TIMEOUT         默认 180
"""

import os
import re
import json
import time
import uuid
import asyncio
import logging
import argparse
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


# ============================================================
# 配置
# ============================================================

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--host")
_parser.add_argument("--port", type=int)
_parser.add_argument("--gateway-url")
_parser.add_argument("--api-url")
_parser.add_argument("--workspace")
_parser.add_argument("--agent-id")
_parser.add_argument("--model")
_args, _ = _parser.parse_known_args()


class Config:
    HOST = _args.host or _env("DEBUGGER_HOST", "0.0.0.0")
    PORT = _args.port or int(_env("DEBUGGER_PORT", "9000"))

    GATEWAY_URL = (_args.gateway_url or _env("GATEWAY_URL", "http://127.0.0.1:5000")).rstrip("/")
    AGENT_ID = _args.agent_id or _env("AGENT_ID", "agent-debugger")
    AGENT_MODEL = _args.model or _env("AGENT_MODEL", "deepseek-chat")
    AGENT_QUOTA_DAILY = int(_env("AGENT_QUOTA_DAILY", "500000"))

    API_URL = (_args.api_url or _env("API_URL", "http://127.0.0.1:8000")).rstrip("/")

    WORKSPACE_ROOT = Path(_args.workspace or _env("WORKSPACE_ROOT", "./workspace"))
    CURRENT_PROJECT_FILE = ".current"

    RUN_TIMEOUT = int(_env("RUN_TIMEOUT", "180"))


config = Config()


# ============================================================
# 日志
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("debugger")


# ============================================================
# 项目管理
# ============================================================

def _current_project_file() -> Path:
    return config.WORKSPACE_ROOT / config.CURRENT_PROJECT_FILE


def get_current_project() -> str:
    f = _current_project_file()
    if f.exists():
        name = f.read_text(encoding="utf-8").strip()
        if name and (config.WORKSPACE_ROOT / name).is_dir():
            return name
    return "default"


def set_current_project(name: str):
    if not re.match(r"^[a-zA-Z0-9_\-.]+$", name):
        raise ValueError("项目名只能包含字母、数字、下划线、中划线、点")
    _current_project_file().write_text(name, encoding="utf-8")


def get_project_path(name: Optional[str] = None) -> Path:
    return config.WORKSPACE_ROOT / (name or get_current_project())


def ensure_project(name: Optional[str] = None) -> Path:
    p = get_project_path(name)
    p.mkdir(parents=True, exist_ok=True)
    return p


def list_projects() -> List[str]:
    if not config.WORKSPACE_ROOT.exists():
        return []
    projects = [
        d.name for d in config.WORKSPACE_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
    projects.sort()
    if not projects:
        ensure_project("default")
        projects = ["default"]
    return projects


# ---------- 版本 ----------

def get_current_version(project: Optional[str] = None) -> int:
    f = get_project_path(project) / "current_version.txt"
    if f.exists():
        try:
            return int(f.read_text().strip())
        except Exception:
            return 0
    return 0


def set_current_version(v: int, project: Optional[str] = None):
    f = get_project_path(project) / "current_version.txt"
    f.write_text(str(v))


def get_code_file(v: int, project: Optional[str] = None) -> Path:
    return get_project_path(project) / f"main_v{v}.py"


def get_log_file(v: int, project: Optional[str] = None) -> Path:
    return get_project_path(project) / f"log_v{v}.txt"


def get_version_code(v: int, project: Optional[str] = None) -> str:
    f = get_code_file(v, project)
    return f.read_text(encoding="utf-8") if f.exists() else ""


def get_version_log(v: int, project: Optional[str] = None) -> str:
    f = get_log_file(v, project)
    return f.read_text(encoding="utf-8") if f.exists() else ""


def get_version_status(v: int, project: Optional[str] = None) -> str:
    log = get_version_log(v, project)
    if not log:
        return "unknown"
    if "✅" in log or "运行成功" in log:
        return "success"
    if "❌" in log or "报错" in log or "Error" in log or "Traceback" in log:
        return "error"
    if "⏰" in log or "超时" in log:
        return "timeout"
    return "unknown"


def save_code_version(v: int, code: str, project: Optional[str] = None):
    f = get_code_file(v, project)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(code, encoding="utf-8")


def save_log_version(v: int, log: str, project: Optional[str] = None):
    f = get_log_file(v, project)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(log, encoding="utf-8")


# ---------- 上下文 ----------

def get_context(project: Optional[str] = None) -> str:
    f = get_project_path(project) / "context.txt"
    return f.read_text(encoding="utf-8") if f.exists() else ""


def save_context(content: str, project: Optional[str] = None):
    p = get_project_path(project)
    p.mkdir(parents=True, exist_ok=True)
    (p / "context.txt").write_text(content, encoding="utf-8")


def get_project_files(project: Optional[str] = None) -> List[str]:
    p = get_project_path(project)
    if not p.exists():
        return []
    files = [
        f.name for f in p.iterdir()
        if f.is_file() and f.name not in ("current_version.txt", "context.txt", ".current")
    ]

    def sort_key(name: str) -> int:
        m = re.search(r"_v(\d+)", name)
        return int(m.group(1)) if m else 0

    files.sort(key=sort_key)
    return files


# ============================================================
# 网关客户端
# ============================================================

class GatewayClient:
    def __init__(self, gateway_url: str, agent_id: str):
        self.gateway_url = gateway_url.rstrip("/")
        self.agent_id = agent_id
        self.registered = False

    def register(self) -> bool:
        try:
            url = f"{self.gateway_url}/api/agents/{self.agent_id}"
            payload = {
                "model": config.AGENT_MODEL,
                "quota_daily": config.AGENT_QUOTA_DAILY,
                "enabled": True,
            }
            r = requests.post(url, json=payload, timeout=5)
            if r.status_code == 200:
                self.registered = True
                logger.info(f"✅ 向网关注册成功: {self.agent_id}")
                return True
            logger.warning(f"⚠️ 网关注册失败: {r.text}")
            return False
        except Exception as e:
            logger.warning(f"⚠️ 网关注册异常: {e}")
            return False

    def report(self, data: dict):
        try:
            requests.post(f"{self.gateway_url}/api/report", json=data, timeout=3)
        except Exception:
            pass

    def report_async(self, data: dict):
        threading.Thread(target=self.report, args=(data,), daemon=True).start()


gateway = GatewayClient(config.GATEWAY_URL, config.AGENT_ID)


# ============================================================
# 调 agent
# ============================================================

def extract_code_from_markdown(text: str) -> str:
    """从 markdown 里抠代码块"""
    matches = re.findall(r"```(?:python)?\n(.*?)\n```", text, re.DOTALL)
    if matches:
        return "\n\n".join(matches).strip()
    if text.strip().startswith("```"):
        lines = text.strip().split("\n")
        if len(lines) > 2:
            return "\n".join(lines[1:-1]).strip()
    return text.strip()


def call_agent_write_code(prompt: str) -> str:
    """调 agent 拿代码（同步，mode=chat，让 agent 只返回 content）"""
    try:
        r = requests.post(f"{config.API_URL}/chat", json={
            "mode": "chat",
            "message": prompt,
            "system_prompt": (
                "你是一个 Python 程序员。根据用户需求写 Python 代码。"
                "只输出代码，不要解释，不要用 markdown 代码块包裹。代码应可直接运行。"
            ),
            "model": config.AGENT_MODEL,
            "temperature": 0.3,
            "max_tokens": 4096,
        }, timeout=120)
        if r.status_code != 200:
            return f"# 调 agent 失败: {r.text}\nprint('调 agent 失败')"
        data = r.json()
        if not data.get("success"):
            return f"# agent 返回错误: {data.get('error')}\nprint('agent 返回错误')"
        return extract_code_from_markdown(data.get("content", ""))
    except Exception as e:
        return f"# 调 agent 异常: {e}\nprint('调 agent 异常')"


def call_agent_chat(message: str, system_prompt: Optional[str] = None) -> str:
    """调 agent 聊天（同步，mode=chat）"""
    try:
        r = requests.post(f"{config.API_URL}/chat", json={
            "mode": "chat",
            "message": message,
            "system_prompt": system_prompt or "你是一个 AI 助手，帮助调试代码和回答问题。",
            "model": config.AGENT_MODEL,
            "temperature": 0.7,
            "max_tokens": 4096,
        }, timeout=120)
        if r.status_code != 200:
            return f"调 agent 失败: {r.text}"
        data = r.json()
        if not data.get("success"):
            return f"agent 返回错误: {data.get('error')}"
        return data.get("content", "")
    except Exception as e:
        return f"请求失败: {e}"


# ============================================================
# 跑代码
# ============================================================

def run_python_code(code: str, version: int, project: Optional[str] = None) -> Tuple[str, str, int]:
    """
    把代码写到 main_v{version}.py，跑，返回 (log, status, elapsed_ms)。
    log 也写进 log_v{version}.txt。
    """
    code_file = get_code_file(version, project)
    log_file = get_log_file(version, project)
    code_file.parent.mkdir(parents=True, exist_ok=True)
    code_file.write_text(code, encoding="utf-8")
    logger.info(f"📝 保存代码: {code_file}")

    t0 = time.time()
    try:
        r = subprocess.run(
            ["python", str(code_file)],
            capture_output=True, text=True,
            timeout=config.RUN_TIMEOUT,
            cwd=str(code_file.parent),
        )
        elapsed = int((time.time() - t0) * 1000)

        log = ""
        if r.stdout:
            log += r.stdout
        if r.stderr:
            if log:
                log += "\n"
            log += r.stderr

        status = "success" if r.returncode == 0 else "error"
        log_file.write_text(log, encoding="utf-8")
        logger.info(f"📋 保存日志: {log_file} status={status} {elapsed}ms")
        return log, status, elapsed

    except subprocess.TimeoutExpired:
        elapsed = int((time.time() - t0) * 1000)
        log = f"⏰ 代码运行超时（超过 {config.RUN_TIMEOUT} 秒）"
        log_file.write_text(log, encoding="utf-8")
        return log, "timeout", elapsed
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        log = f"❌ 运行异常: {e}"
        log_file.write_text(log, encoding="utf-8")
        return log, "error", elapsed


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(title=f"AI Debugger ({config.AGENT_ID})")


@app.on_event("startup")
async def on_startup():
    config.WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    ensure_project("default")
    if not _current_project_file().exists():
        set_current_project("default")

    print("=" * 60)
    print("🤖 AI 代码调试器（FastAPI，无页面）")
    print("=" * 60)
    print(f"  服务地址 : http://{config.HOST}:{config.PORT}")
    print(f"  网关地址 : {config.GATEWAY_URL}")
    print(f"  Agent ID : {config.AGENT_ID}")
    print(f"  Agent    : {config.API_URL}")
    print(f"  工作区   : {config.WORKSPACE_ROOT}")
    print(f"  当前项目 : {get_current_project()}")
    print(f"  运行超时 : {config.RUN_TIMEOUT}s")
    print("=" * 60)

    gateway.register()


# ---------- 基本 ----------

@app.get("/")
async def root():
    return {
        "service": "AI Debugger",
        "agent_id": config.AGENT_ID,
        "workspace": str(config.WORKSPACE_ROOT),
        "current_project": get_current_project(),
        "api_url": config.API_URL,
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_id": config.AGENT_ID,
        "gateway_connected": gateway.registered,
    }


# ---------- 项目管理 ----------

@app.get("/api/projects")
async def api_list_projects():
    return {
        "success": True,
        "projects": list_projects(),
        "current": get_current_project(),
    }


@app.get("/api/projects/current")
async def api_get_current_project():
    return {"success": True, "project": get_current_project()}


class SwitchReq(BaseModel):
    project: str


@app.post("/api/projects/switch")
async def api_switch_project(req: SwitchReq):
    name = req.project.strip()
    if not name:
        raise HTTPException(400, "项目名不能为空")
    p = get_project_path(name)
    if not p.exists() or not p.is_dir():
        raise HTTPException(404, f'项目 "{name}" 不存在')
    set_current_project(name)
    logger.info(f"🔄 切换到项目: {name}")
    total = get_current_version()
    return {
        "success": True,
        "project": name,
        "total_versions": total,
        "current_version": total,
    }


class CreateProjectReq(BaseModel):
    project: str


@app.post("/api/projects/create")
async def api_create_project(req: CreateProjectReq):
    name = req.project.strip()
    if not name:
        raise HTTPException(400, "项目名不能为空")
    if not re.match(r"^[a-zA-Z0-9_\-.]+$", name):
        raise HTTPException(400, "项目名只能包含字母、数字、下划线、中划线、点")
    p = get_project_path(name)
    if p.exists():
        raise HTTPException(400, f'项目 "{name}" 已存在')
    p.mkdir(parents=True, exist_ok=True)
    logger.info(f"🆕 创建项目: {name}")
    return {"success": True, "project": name}


# ---------- 状态 / 版本 ----------

@app.get("/api/status")
async def get_status():
    return {
        "success": True,
        "project": get_current_project(),
        "total_versions": get_current_version(),
        "current_version": get_current_version(),
    }


@app.get("/api/version/{v}")
async def get_version(v: int):
    if v < 1:
        raise HTTPException(400, "版本号从 1 开始")
    code = get_version_code(v)
    log = get_version_log(v)
    if not code and not log:
        raise HTTPException(404, f"版本 {v} 不存在")
    return {
        "success": True,
        "version": v,
        "code": code,
        "log": log,
        "status": get_version_status(v),
    }


# ---------- 背景要求 ----------

class ContextReq(BaseModel):
    content: str


@app.get("/api/context")
async def get_context_api():
    return {"success": True, "content": get_context()}


@app.post("/api/context")
async def save_context_api(req: ContextReq):
    save_context(req.content)
    return {"success": True, "message": "已保存"}


# ---------- 文件 ----------

@app.get("/api/files")
async def list_files():
    return {"success": True, "files": get_project_files()}


@app.get("/api/file/{filename}")
async def get_file(filename: str):
    p = get_project_path() / filename
    if not p.exists():
        raise HTTPException(404, "文件不存在")
    return {
        "success": True,
        "filename": filename,
        "content": p.read_text(encoding="utf-8"),
    }


# ---------- 核心操作 ----------

class SendReq(BaseModel):
    mode: str = "code"        # code | chat
    content: str


@app.post("/api/send")
async def send(req: SendReq):
    """
    「发送」按钮。
    mode=chat  → 聊天，直接返回
    mode=code  → 写代码 + 跑 + 版本 +1
    """
    content = req.content.strip()
    if not content:
        raise HTTPException(400, "请输入内容")

    project = get_current_project()

    if req.mode == "chat":
        reply = await asyncio.to_thread(call_agent_chat, content)
        return {"success": True, "mode": "chat", "content": reply}

    current_v = get_current_version()
    if current_v == 0:
        prompt = (
            f"请写一个 Python 脚本，实现以下功能：\n{content}\n\n"
            f"只输出代码，不要解释，不要用 markdown 包裹。"
        )
    else:
        current_code = get_version_code(current_v)
        current_log = get_version_log(current_v)
        prompt = (
            f"你之前写的代码，现在用户提出了新需求，请修改代码：\n\n"
            f"【当前代码】\n{current_code}\n\n"
            f"【运行日志】\n{current_log or '（无日志）'}\n\n"
            f"【用户需求】\n{content}\n\n"
            f"请只输出修改后的完整 Python 代码，不要解释，不要用 markdown 包裹。"
        )

    new_v = current_v + 1
    code = await asyncio.to_thread(call_agent_write_code, prompt)
    log, status, elapsed = await asyncio.to_thread(run_python_code, code, new_v, project)
    set_current_version(new_v)

    gateway.report_async({
        "agent_id": config.AGENT_ID,
        "model": config.AGENT_MODEL,
        "prompt_tokens": len(prompt) // 2,
        "completion_tokens": len(code) // 2,
        "total_tokens": (len(prompt) + len(code)) // 2,
        "latency_ms": elapsed,
        "status_code": 200 if status == "success" else 500,
        "error_msg": "" if status == "success" else log[:200],
    })

    return {
        "success": True,
        "mode": "code",
        "version": new_v,
        "total_versions": new_v,
        "code": code,
        "log": log,
        "status": status,
        "elapsed_ms": elapsed,
    }


class FixReq(BaseModel):
    code: str = ""
    log: str = ""
    instruction: str
    mode: str = "code"        # code | chat


@app.post("/api/fix")
async def fix(req: FixReq):
    """
    「提交代码」按钮。
    带当前代码 + 日志 + 指令，让 AI 修。
    """
    instruction = req.instruction.strip()
    if not instruction:
        raise HTTPException(400, "请输入内容")

    project = get_current_project()
    ctx = get_context()
    ctx_text = f"\n\n【背景要求】\n{ctx}" if ctx else ""

    if req.mode == "chat":
        prompt = (
            f"用户想和你讨论代码，请根据以下信息回答：\n\n"
            f"【当前代码】\n{req.code or '（无代码）'}\n\n"
            f"【运行日志】\n{req.log or '（无日志）'}{ctx_text}\n\n"
            f"【用户问题】\n{instruction}\n\n"
            f"请给出详细的回答和建议。"
        )
        reply = await asyncio.to_thread(call_agent_chat, prompt)
        return {"success": True, "mode": "chat", "content": reply}

    if not req.code:
        raise HTTPException(400, "代码不能为空")

    prompt = (
        f"你之前写的代码运行后产生了以下结果，请修复或修改代码：\n\n"
        f"【当前代码】\n{req.code}\n\n"
        f"【运行日志】\n{req.log or '（无日志）'}{ctx_text}\n\n"
        f"【用户指令】\n{instruction}\n\n"
        f"请只输出修正后的完整 Python 代码，不要解释，不要用 markdown 包裹。"
    )

    new_v = get_current_version() + 1
    new_code = await asyncio.to_thread(call_agent_write_code, prompt)
    new_log, status, elapsed = await asyncio.to_thread(run_python_code, new_code, new_v, project)
    set_current_version(new_v)

    gateway.report_async({
        "agent_id": config.AGENT_ID,
        "model": config.AGENT_MODEL,
        "prompt_tokens": len(prompt) // 2,
        "completion_tokens": len(new_code) // 2,
        "total_tokens": (len(prompt) + len(new_code)) // 2,
        "latency_ms": elapsed,
        "status_code": 200 if status == "success" else 500,
        "error_msg": "" if status == "success" else new_log[:200],
    })

    return {
        "success": True,
        "mode": "code",
        "version": new_v,
        "total_versions": new_v,
        "code": new_code,
        "log": new_log,
        "status": status,
        "elapsed_ms": elapsed,
    }


class RunReq(BaseModel):
    code: str


@app.post("/api/run")
async def run(req: RunReq):
    """直接跑给定代码，版本 +1"""
    code = req.code.strip()
    if not code:
        raise HTTPException(400, "代码不能为空")

    project = get_current_project()
    new_v = get_current_version() + 1
    log, status, elapsed = await asyncio.to_thread(run_python_code, code, new_v, project)
    set_current_version(new_v)

    gateway.report_async({
        "agent_id": config.AGENT_ID,
        "model": config.AGENT_MODEL,
        "prompt_tokens": len(code) // 2,
        "completion_tokens": 0,
        "total_tokens": len(code) // 2,
        "latency_ms": elapsed,
        "status_code": 200 if status == "success" else 500,
        "error_msg": "" if status == "success" else log[:200],
    })

    return {
        "success": True,
        "version": new_v,
        "total_versions": new_v,
        "code": code,
        "log": log,
        "status": status,
        "elapsed_ms": elapsed,
    }


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=False)