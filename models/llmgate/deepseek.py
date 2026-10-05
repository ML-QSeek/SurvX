# -*- coding: utf-8 -*-
"""
deepseek.py

中文：DeepSeek Agent 服务（网关适配版）。启动时从命令行 / 环境变量读取配置，向 llmgate 网关注册；提供同步对话、流式对话、异步脚本生成与文件拉取，并通过 WebSocket 广播脚本完成事件。
English: DeepSeek Agent service (gateway-adapted). On startup reads config from CLI args / env vars and registers with the llmgate gateway; provides synchronous chat, streaming chat, async script generation and file fetching, and broadcasts script-ready events over WebSocket.

版本: 20260929150000
作者: quruyi
时间: 20260929150000 # 最后修改时间

用法:
    # 由 llmgate 拉起（推荐）
    python deepseek.py --name agent-deepseek --provider deepseek --port 8000 \
        --api-key sk-xxx --gateway-url http://127.0.0.1:5000

    # 手动运行
    python deepseek.py --port 8000 --api-key sk-xxx --name agent-deepseek

环境变量:
    AGENT_NAME    实例名（如 agent-deepseek）
    PROVIDER      固定 deepseek
    PORT          监听端口
    API_KEY       DeepSeek API Key
    BASE_URL      API 地址（可选，默认 https://api.deepseek.com）
    MODEL         默认模型（可选，默认 deepseek-chat）
    GATEWAY_URL   网关地址（默认 http://127.0.0.1:5000）
    HOST          监听地址（默认 0.0.0.0）

接口:
    GET  /                    服务信息
    GET  /health              健康检查
    GET  /stats               统计
    POST /chat                对话（mode=chat 同步；mode=script 异步）
    POST /chat/stream         流式对话（SSE）
    GET  /files/{file_id}     拉脚本文件
    WS   /ws/script_ready     订阅脚本完成广播

说明:
    - chat 模式：同步等 AI 返回 content，适合聊天
    - script 模式：立即返回 task_id，agent 后台跑；完成后通过 WS 广播 file_id，客户端来拉文件
    - 每次调用 AI 后向网关 /api/report 上报 token 用量与延迟，网关据此累计配额
    - 调用前会向网关 /api/agents 查权限；网关不可用时默认放行，保障业务
    - 脚本文件存到 generated_code/{task_id}/{file_id}.py，重启后按目录扫描恢复 file_id 映射
    - 失败任务也会存 {file_id}_error.py 并广播 success=false
    - WebSocket 广播池共用一份连接集合，按 session_id 让客户端认领自己的任务
"""

import os
import re
import json
import time
import uuid
import asyncio
import logging
import argparse
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

import requests
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel


# ============================================================
# 配置
# ============================================================

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# 命令行参数（llmgate 用命令行拉起）
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("--name")
_parser.add_argument("--provider")
_parser.add_argument("--port", type=int)
_parser.add_argument("--api-key")
_parser.add_argument("--base-url")
_parser.add_argument("--model")
_parser.add_argument("--gateway-url")
_args, _ = _parser.parse_known_args()


class Config:
    AGENT_ID = _args.name or _env("AGENT_NAME", "agent-deepseek")
    PROVIDER = _args.provider or _env("PROVIDER", "deepseek")

    API_KEY = _args.api_key or _env("API_KEY", "")
    BASE_URL = (_args.base_url or _env("BASE_URL", "https://api.deepseek.com")).rstrip("/")
    MODEL = _args.model or _env("MODEL", "deepseek-chat")

    GATEWAY_URL = (_args.gateway_url or _env("GATEWAY_URL", "http://127.0.0.1:5000")).rstrip("/")

    HOST = _env("HOST", "0.0.0.0")
    PORT = _args.port or int(_env("PORT", "8000"))

    # 脚本存储目录
    CODE_DIR = Path(__file__).parent / "generated_code"


config = Config()


# ============================================================
# 日志
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(config.AGENT_ID)


# ============================================================
# 网关客户端
# ============================================================

class GatewayClient:
    """负责与网关通信：注册、查权限、上报"""

    def __init__(self, gateway_url: str, agent_id: str):
        self.gateway_url = gateway_url.rstrip("/")
        self.agent_id = agent_id
        self.registered = False

    def register(self) -> bool:
        """向网关注册"""
        try:
            url = f"{self.gateway_url}/api/agents/{self.agent_id}"
            payload = {
                "model": config.MODEL,
                "quota_daily": 100000,
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

    def check_permission(self) -> tuple:
        """
        查权限。
        返回 (allowed, reason, quota_used, quota_daily)
        网关不可用时默认放行（保障业务）。
        """
        try:
            r = requests.get(f"{self.gateway_url}/api/agents", timeout=3)
            if r.status_code != 200:
                return True, "网关返回错误，默认放行", 0, 0
            data = r.json()
            if data.get("code") != 0:
                return True, "网关返回异常，默认放行", 0, 0
            for a in data.get("data", []):
                if a.get("agent_id") == self.agent_id:
                    enabled = a.get("enabled", False)
                    used = int(a.get("quota_used", 0))
                    daily = int(a.get("quota_daily", 0))
                    if not enabled:
                        return False, "Agent 已被禁用", used, daily
                    if daily > 0 and used >= daily:
                        return False, "日配额已用完", used, daily
                    return True, "允许", used, daily
            # 未注册 → 放行（方便调试）
            return True, "未注册，默认放行", 0, 0
        except Exception as e:
            logger.warning(f"⚠️ 查权限异常: {e}")
            return True, "网关不可用，默认放行", 0, 0

    def report(self, data: dict):
        """上报调用记录（同步，内部用）"""
        try:
            requests.post(f"{self.gateway_url}/api/report", json=data, timeout=3)
        except Exception as e:
            logger.warning(f"⚠️ 上报异常: {e}")

    def report_async(self, data: dict):
        """上报（异步，不阻塞）"""
        threading.Thread(target=self.report, args=(data,), daemon=True).start()


gateway = GatewayClient(config.GATEWAY_URL, config.AGENT_ID)


# ============================================================
# 工具函数
# ============================================================

def extract_code_blocks(text: str) -> Dict[str, List[str]]:
    """从文本中提取 ```lang ... ``` 代码块"""
    blocks: Dict[str, List[str]] = {}
    for lang, code in re.findall(r"```(\w+)?\n(.*?)\n```", text, re.DOTALL):
        lang = lang or "text"
        blocks.setdefault(lang, []).append(code.strip())
    return blocks


def call_deepseek(messages: List[Dict[str, str]], model: str,
                  max_tokens: int, temperature: float, retry: int = 3) -> Dict[str, Any]:
    """调 DeepSeek API，失败重试"""
    if not config.API_KEY:
        raise ValueError("未设置 API_KEY")

    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    url = f"{config.BASE_URL}/v1/chat/completions"

    last_err = None
    for attempt in range(retry):
        try:
            t0 = time.time()
            r = requests.post(url, headers=headers, json=payload, timeout=60)
            elapsed_ms = int((time.time() - t0) * 1000)
            r.raise_for_status()
            result = r.json()
            result["_elapsed_ms"] = elapsed_ms
            return result
        except requests.exceptions.RequestException as e:
            last_err = e
            logger.warning(f"API 调用失败 ({attempt + 1}/{retry}): {e}")
            if attempt < retry - 1:
                time.sleep(2)
    raise last_err


# ============================================================
# 脚本文件管理
# ============================================================

# file_id -> 路径
_files: Dict[str, Path] = {}


def _save_script(content: str, task_id: str, suffix: str = "") -> str:
    """
    把脚本存到 generated_code/{task_id}/{file_id}.py，返回 file_id。

    suffix 用于区分正常/错误文件，比如 suffix="error"。
    file_id 本身不带 suffix，客户端用它来拉。
    """
    file_id = f"{task_id}_{uuid.uuid4().hex[:6]}"
    name = f"{file_id}{('_' + suffix) if suffix else ''}.py"
    path = config.CODE_DIR / task_id / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _files[file_id] = path
    logger.info(f"[脚本] 已存 {path}")
    return file_id


def _restore_files():
    """启动时扫目录，恢复 file_id 映射（agent 重启后旧文件仍可拉）"""
    if not config.CODE_DIR.exists():
        return
    for p in config.CODE_DIR.rglob("*.py"):
        # 文件名：{file_id}.py 或 {file_id}_error.py
        stem = p.stem
        if stem.endswith("_error"):
            stem = stem[:-6]
        _files[stem] = p
    logger.info(f"[脚本] 恢复 {len(_files)} 个文件")


# ============================================================
# WebSocket 广播池
# ============================================================

_ws_pool: set[WebSocket] = set()


async def _broadcast(msg: dict):
    """给所有订阅者广播一条 JSON"""
    text = json.dumps(msg, ensure_ascii=False)
    dead = []
    for ws in list(_ws_pool):
        try:
            await ws.send_text(text)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_pool.discard(ws)


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(title=f"DeepSeek Agent ({config.AGENT_ID})")


@app.on_event("startup")
async def on_startup():
    config.CODE_DIR.mkdir(parents=True, exist_ok=True)
    _restore_files()

    print("=" * 60)
    print("🚀 DeepSeek Agent")
    print("=" * 60)
    print(f"  服务地址 : http://{config.HOST}:{config.PORT}")
    print(f"  网关地址 : {config.GATEWAY_URL}")
    print(f"  Agent ID : {config.AGENT_ID}")
    print(f"  模型     : {config.MODEL}")
    print(f"  Base URL : {config.BASE_URL}")
    print(f"  脚本目录 : {config.CODE_DIR}")
    print("=" * 60)

    gateway.register()


# ---------- 基本信息 ----------

@app.get("/")
async def root():
    return {
        "service": "DeepSeek Agent",
        "version": "1.0.0",
        "agent_id": config.AGENT_ID,
        "provider": config.PROVIDER,
        "gateway": config.GATEWAY_URL,
        "endpoints": ["/chat", "/chat/stream", "/files/{file_id}", "/ws/script_ready"],
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_id": config.AGENT_ID,
        "gateway_connected": gateway.registered,
    }


@app.get("/stats")
async def stats():
    return {
        "agent_id": config.AGENT_ID,
        "model": config.MODEL,
        "gateway_url": config.GATEWAY_URL,
        "files": len(_files),
        "ws_clients": len(_ws_pool),
        "timestamp": datetime.now().isoformat(),
    }


# ---------- WebSocket：订阅脚本完成 ----------

@app.websocket("/ws/script_ready")
async def ws_script_ready(ws: WebSocket):
    """
    客户端连上后，agent 每次脚本任务完成都会广播：
        {
          "type": "script_ready",
          "task_id": "...",       # agent 分配的内部 id
          "session_id": "...",    # 客户端传的，用于认领
          "file_id": "...",       # 拉文件用
          "agent": "...",
          "success": true/false,
          "error": "..."          # 失败时带
        }
    客户端按 session_id 认领自己的任务。
    """
    await ws.accept()
    _ws_pool.add(ws)
    logger.info(f"[WS] +1 订阅者，当前 {len(_ws_pool)}")
    try:
        while True:
            # 保持连接；客户端心跳可发任意文本，这里忽略
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _ws_pool.discard(ws)
        logger.info(f"[WS] -1 订阅者，当前 {len(_ws_pool)}")


# ---------- 拉文件 ----------

@app.get("/files/{file_id}")
async def get_file(file_id: str):
    """客户端拿 file_id 来拉脚本；拉到本地后自己改名"""
    p = _files.get(file_id)
    if not p or not p.exists():
        # 兜底：按 file_id 扫目录
        for f in config.CODE_DIR.rglob(f"{file_id}*.py"):
            p = f
            _files[file_id] = p
            break
    if not p or not p.exists():
        raise HTTPException(404, f"文件不存在: {file_id}")
    return FileResponse(p, media_type="text/plain")


# ---------- /chat ----------

class ChatReq(BaseModel):
    message: str
    mode: str = "chat"                  # chat | script
    session_id: str | None = None       # 客户端传，用于广播认领
    system_prompt: str | None = None
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    auto_save_code: bool = True


def _build_messages(req: ChatReq) -> List[Dict[str, str]]:
    msgs = []
    if req.system_prompt:
        msgs.append({"role": "system", "content": req.system_prompt})
    msgs.append({"role": "user", "content": req.message})
    return msgs


@app.post("/chat")
async def chat(req: ChatReq):
    """
    mode=chat   → 同步调 AI，直接返回 content
    mode=script → 立即返回，后台跑；完成后 WS 广播
    """
    allowed, reason, _, _ = gateway.check_permission()
    if not allowed:
        raise HTTPException(403, f"权限拒绝: {reason}")

    if req.mode == "chat":
        return await _handle_chat(req)
    elif req.mode == "script":
        return await _handle_script(req)
    else:
        raise HTTPException(400, f"未知 mode: {req.mode}")


async def _handle_chat(req: ChatReq) -> dict:
    """聊天模式：同步等 AI，直接返回"""
    messages = _build_messages(req)
    model = req.model or config.MODEL
    session_id = req.session_id or str(uuid.uuid4())[:8]

    try:
        t0 = time.time()
        resp = await asyncio.to_thread(
            call_deepseek, messages, model, req.max_tokens, req.temperature
        )
        elapsed_ms = int((time.time() - t0) * 1000)
    except Exception as e:
        logger.error(f"调用失败: {e}")
        gateway.report_async({
            "agent_id": config.AGENT_ID, "model": model,
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "latency_ms": 0, "status_code": 500, "error_msg": str(e),
        })
        raise HTTPException(500, f"API 调用失败: {e}")

    choice = (resp.get("choices") or [{}])[0]
    content = choice.get("message", {}).get("content", "")
    usage = resp.get("usage", {}) or {}
    pt = usage.get("prompt_tokens", 0)
    ct = usage.get("completion_tokens", 0)
    tt = usage.get("total_tokens", 0)

    gateway.report_async({
        "agent_id": config.AGENT_ID, "model": model,
        "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt,
        "latency_ms": elapsed_ms, "status_code": 200, "error_msg": "",
    })

    return {
        "success": True,
        "mode": "chat",
        "session_id": session_id,
        "content": content,
        "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt},
        "latency_ms": elapsed_ms,
        "model": model,
        "timestamp": datetime.now().isoformat(),
    }


async def _handle_script(req: ChatReq) -> dict:
    """脚本模式：立即返回，后台跑，完成后 WS 广播"""
    task_id = uuid.uuid4().hex[:8]        # agent 分配

    asyncio.create_task(_run_script_task(task_id, req))

    return {
        "success": True,
        "mode": "script",
        "task_id": task_id,               # agent 分配的
        "session_id": req.session_id,     # 原样返回，便于客户端对照
        "msg": "已接收，完成后会通过 WS 广播",
    }


async def _run_script_task(task_id: str, req: ChatReq):
    """
    后台跑脚本任务：
        调 AI → 提取 python 代码 → 存文件 → 广播

    失败也存错误文件，也广播（success=false）。
    """
    messages = _build_messages(req)
    model = req.model or config.MODEL

    try:
        t0 = time.time()
        resp = await asyncio.to_thread(
            call_deepseek, messages, model, req.max_tokens, req.temperature
        )
        elapsed_ms = int((time.time() - t0) * 1000)
    except Exception as e:
        logger.error(f"[{task_id}] 调用失败: {e}")
        gateway.report_async({
            "agent_id": config.AGENT_ID, "model": model,
            "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
            "latency_ms": 0, "status_code": 500, "error_msg": str(e),
        })
        # 把错误信息存文件
        err_text = (
            f"# task_id: {task_id}\n"
            f"# session_id: {req.session_id}\n"
            f"# 调用失败\n"
            f"# error: {e}\n"
        )
        file_id = _save_script(err_text, task_id, suffix="error")
        await _broadcast({
            "type": "script_ready",
            "task_id": task_id,
            "session_id": req.session_id,
            "file_id": file_id,
            "agent": config.AGENT_ID,
            "success": False,
            "error": str(e),
        })
        return

    choice = (resp.get("choices") or [{}])[0]
    content = choice.get("message", {}).get("content", "")
    usage = resp.get("usage", {}) or {}
    pt = usage.get("prompt_tokens", 0)
    ct = usage.get("completion_tokens", 0)
    tt = usage.get("total_tokens", 0)

    # 提取 python 代码块
    blocks = extract_code_blocks(content)
    codes = blocks.get("python", [])
    if not codes:
        # 没代码块，整个 content 当脚本
        codes = [content.strip()]
    script = "\n\n".join(codes)

    file_id = _save_script(script, task_id)

    gateway.report_async({
        "agent_id": config.AGENT_ID, "model": model,
        "prompt_tokens": pt, "completion_tokens": ct, "total_tokens": tt,
        "latency_ms": elapsed_ms, "status_code": 200, "error_msg": "",
    })

    await _broadcast({
        "type": "script_ready",
        "task_id": task_id,
        "session_id": req.session_id,
        "file_id": file_id,
        "agent": config.AGENT_ID,
        "success": True,
    })
    logger.info(f"[{task_id}] 脚本完成，file_id={file_id}")


# ---------- /chat/stream ----------

@app.post("/chat/stream")
async def chat_stream(req: ChatReq):
    allowed, reason, _, _ = gateway.check_permission()
    if not allowed:
        raise HTTPException(403, f"权限拒绝: {reason}")

    if not config.API_KEY:
        raise HTTPException(500, "未设置 API_KEY")

    messages = _build_messages(req)
    model = req.model or config.MODEL
    url = f"{config.BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {config.API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "stream": True,
    }

    def sse():
        collected = []
        try:
            r = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
            for line in r.iter_lines():
                if not line:
                    continue
                s = line.decode("utf-8")
                if not s.startswith("data: "):
                    continue
                s = s[6:]
                if s == "[DONE]":
                    break
                try:
                    chunk = json.loads(s)
                    delta = (chunk.get("choices") or [{}])[0].get("delta", {})
                    piece = delta.get("content", "")
                    if piece:
                        collected.append(piece)
                    yield f"data: {json.dumps({'content': piece, 'done': False})}\n\n"
                except json.JSONDecodeError:
                    pass

            full = "".join(collected)
            tt = len(full) // 2
            gateway.report_async({
                "agent_id": config.AGENT_ID, "model": model,
                "prompt_tokens": len(req.message) // 2,
                "completion_tokens": tt,
                "total_tokens": len(req.message) // 2 + tt,
                "latency_ms": 0, "status_code": 200, "error_msg": "",
            })
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.error(f"流式失败: {e}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"

    return StreamingResponse(
        sse(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.HOST, port=config.PORT, reload=False)