# -*- coding: utf-8 -*-
"""
server.py —— SurvX Studio 通讯中枢

职责：
    1. 服务注册：子页面加载时注册 app_id / title / menu
    2. 消息总线：任何一方 POST /messages 写入消息，服务器按 to 字段分发
    3. WebSocket：/ws?as=<自己>，实时推送给自己
    4. 脚本仓库：/scripts/<id>，AI 或服务器生成的脚本存在这里
    5. LLM 占位：/llm 接收 prompt，按关键词生成假脚本
    6. 页面/静态：/ 返回父页面，/files/* 返回子页面

用法：
    pip install fastapi uvicorn jinja2
    python server.py
"""

import os
import time
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ============================================================
# 配置 & 日志
# ============================================================

HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "3050"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("survx")

BASE_DIR = Path(__file__).parent
FILES_DIR = BASE_DIR / "files"
FILES_DIR.mkdir(exist_ok=True)

# ============================================================
# 内存状态
# ============================================================

class Store:
    # 已注册的 app: app_id -> {title, menu, ts}
    apps: Dict[str, Dict[str, Any]] = {}
    # 消息列表（环形，保留最近 1000 条）
    messages: List[Dict[str, Any]] = []
    # 消息自增 id
    msg_seq: int = 0
    # 脚本仓库: script_id -> {lang, code, summary, ts}
    scripts: Dict[str, Dict[str, Any]] = {}
    # 当前活跃 app（父页面 ☰ 从这里拉菜单）
    active_app: Optional[str] = None
    # WebSocket 连接: who -> set[WebSocket]
    sockets: Dict[str, set] = {}
    # 简单锁
    lock = asyncio.Lock()

store = Store()


def next_msg_id() -> str:
    store.msg_seq += 1
    return f"m{store.msg_seq}"


def log_line(msg: str) -> None:
    logger.info(msg)


# ============================================================
# 消息模型
# ============================================================

class RegisterRequest(BaseModel):
    app_id: str = Field(..., min_length=1)
    title: str = ""
    menu: List[Dict[str, Any]] = []


class MessageRequest(BaseModel):
    """写入一条消息。

    from_  谁发的：parent | child:<app_id> | system | llm
    to     谁该收：parent | child:<app_id> | broadcast | llm
    kind   menu | state | script | chat | log | notify
    payload 任意 JSON
    """
    from_: str = Field(..., alias="from")
    to: str = Field(...)
    kind: str = Field(...)
    payload: Dict[str, Any] = {}

    class Config:
        populate_by_name = True


class LlmRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    # 上下文：来自父页面或子页面
    context: Dict[str, Any] = {}


class ScriptCreateRequest(BaseModel):
    lang: str = "js"
    code: str = Field(..., min_length=1)
    summary: str = ""


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(title="SurvX Studio", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(BASE_DIR))
app.mount("/files", StaticFiles(directory=str(FILES_DIR)), name="files")


# ============================================================
# WebSocket 管理
# ============================================================

async def ws_send(who: str, data: Dict[str, Any]):
    """给某个订阅者推送消息（who 可以是 parent / child:xxx）。"""
    conns = store.sockets.get(who, set())
    dead = []
    for ws in conns:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        conns.discard(ws)


async def dispatch_message(msg: Dict[str, Any]):
    """按 to 分发消息到 WebSocket。"""
    to = msg["to"]
    if to == "broadcast":
        for who in list(store.sockets.keys()):
            await ws_send(who, {"type": "message", "message": msg})
    else:
        await ws_send(to, {"type": "message", "message": msg})


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket, as_: str = ""):
    """订阅地址：/ws?as=parent 或 /ws?as=child:editor"""
    who = as_ or "anon"
    await ws.accept()
    store.sockets.setdefault(who, set()).add(ws)
    log_line(f"🔌 WS 连接: {who}")

    try:
        # 连接后先发一批最近的消息（补漏）
        await ws.send_json({"type": "hello", "who": who, "ts": time.time()})
        for m in store.messages[-50:]:
            if m["to"] in (who, "broadcast"):
                await ws.send_json({"type": "message", "message": m})

        while True:
            data = await ws.receive_json()
            # 客户端也可以从 ws 写消息
            if data.get("type") == "message":
                await handle_incoming_message(data["message"])

    except WebSocketDisconnect:
        pass
    except Exception as e:
        log_line(f"WS 错误 {who}: {e}")
    finally:
        store.sockets.get(who, set()).discard(ws)
        log_line(f"🔌 WS 断开: {who}")


# ============================================================
# 核心：写入一条消息 + 分发
# ============================================================

async def handle_incoming_message(raw: Dict[str, Any]) -> Dict[str, Any]:
    msg = {
        "id": next_msg_id(),
        "from": raw.get("from", "anon"),
        "to": raw.get("to", "broadcast"),
        "kind": raw.get("kind", "notify"),
        "payload": raw.get("payload", {}),
        "ts": time.time(),
    }
    store.messages.append(msg)
    if len(store.messages) > 1000:
        store.messages = store.messages[-1000:]

    log_line(f"✉ [{msg['from']} → {msg['to']}] {msg['kind']} {str(msg['payload'])[:80]}")

    # 自动处理 menu 消息：更新 active_app
    if msg["kind"] == "menu" and msg["from"].startswith("child:"):
        app_id = msg["from"].split(":", 1)[1]
        store.active_app = app_id
        if app_id in store.apps:
            store.apps[app_id]["menu"] = msg["payload"].get("menu", [])
        log_line(f"📋 active_app = {app_id}")

    await dispatch_message(msg)
    return msg


# ============================================================
# API - 服务注册
# ============================================================

@app.post("/register")
async def api_register(req: RegisterRequest):
    store.apps[req.app_id] = {
        "app_id": req.app_id,
        "title": req.title or req.app_id,
        "menu": req.menu,
        "ts": time.time(),
    }
    log_line(f"📦 注册 app: {req.app_id} ({req.title})")
    return {"success": True, "app": store.apps[req.app_id]}


@app.get("/apps")
async def api_apps():
    return {"success": True, "apps": list(store.apps.values()), "active": store.active_app}


@app.post("/active")
async def api_set_active(app_id: str):
    if app_id not in store.apps:
        raise HTTPException(status_code=404, detail=f"app 不存在: {app_id}")
    store.active_app = app_id
    log_line(f"🎯 切换 active_app = {app_id}")
    return {"success": True, "active": app_id}


@app.get("/menu/active")
async def api_active_menu():
    """父页面 ☰ 从这里拉当前菜单。"""
    if not store.active_app or store.active_app not in store.apps:
        return {"success": True, "app_id": None, "title": "", "menu": []}
    a = store.apps[store.active_app]
    return {"success": True, "app_id": a["app_id"], "title": a["title"], "menu": a["menu"]}


# ============================================================
# API - 消息
# ============================================================

@app.post("/messages")
async def api_post_message(req: MessageRequest):
    msg = await handle_incoming_message({
        "from": req.from_, "to": req.to, "kind": req.kind, "payload": req.payload,
    })
    return {"success": True, "message": msg}


@app.get("/messages")
async def api_get_messages(since: str = "", for_: str = ""):
    """轮询兜底（通常用 WS）。"""
    msgs = store.messages
    if since:
        try:
            idx = next(i for i, m in enumerate(msgs) if m["id"] == since)
            msgs = msgs[idx + 1:]
        except StopIteration:
            pass
    if for_:
        msgs = [m for m in msgs if m["to"] in (for_, "broadcast")]
    return {"success": True, "messages": msgs}


# ============================================================
# API - 脚本仓库
# ============================================================

@app.post("/scripts")
async def api_create_script(req: ScriptCreateRequest):
    sid = uuid.uuid4().hex[:12]
    store.scripts[sid] = {
        "id": sid, "lang": req.lang, "code": req.code,
        "summary": req.summary, "ts": time.time(),
    }
    log_line(f"📜 创建脚本 {sid} ({req.lang}) {req.summary}")
    return {"success": True, "script_id": sid, "url": f"/scripts/{sid}"}


@app.get("/scripts/{sid}", response_class=PlainTextResponse)
async def api_get_script(sid: str):
    s = store.scripts.get(sid)
    if not s:
        raise HTTPException(status_code=404, detail="脚本不存在")
    return s["code"]


@app.get("/scripts")
async def api_list_scripts():
    return {"success": True, "scripts": [
        {k: v for k, v in s.items() if k != "code"} for s in store.scripts.values()
    ]}


# ============================================================
# API - LLM 占位
# ============================================================

# 模拟 AI 回复：根据关键词返回不同的"给子页面的脚本"
def fake_llm(prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
    p = prompt.lower()

    # 返回一个"给子页面的脚本"或一条"聊天回复"
    if any(k in p for k in ["标题", "title", "改标题"]):
        return {
            "reply": "好的，我把当前页面标题改了。",
            "target": context.get("app_id") and f"child:{context['app_id']}" or "parent",
            "script": {
                "lang": "js",
                "summary": "修改页面标题",
                "code": """
(function(){
  document.title = 'SurvX · 已被 AI 修改';
  var h = document.querySelector('h1');
  if (h) h.textContent = '✨ ' + h.textContent;
  // 通知父页面/服务器
  if (window.parent !== window) {
    window.parent.postMessage({type:'svx:toast', text:'标题已修改'}, '*');
  }
})();
""",
            },
        }

    if any(k in p for k in ["背景", "颜色", "background", "color"]):
        return {
            "reply": "给页面加了一个渐变背景。",
            "target": context.get("app_id") and f"child:{context['app_id']}" or "parent",
            "script": {
                "lang": "js",
                "summary": "修改页面背景",
                "code": """
(function(){
  document.body.style.background = 'linear-gradient(135deg,#eaf2fe,#f5f9ff)';
  document.body.style.transition = 'background .3s';
})();
""",
            },
        }

    if any(k in p for k in ["按钮", "button", "加一个"]):
        return {
            "reply": "给你加了一个演示按钮。",
            "target": context.get("app_id") and f"child:{context['app_id']}" or "parent",
            "script": {
                "lang": "js",
                "summary": "添加演示按钮",
                "code": """
(function(){
  var b = document.createElement('button');
  b.textContent = 'AI 加的按钮';
  b.style.cssText = 'position:fixed;left:20px;bottom:20px;padding:8px 16px;background:#1a7cff;color:#fff;border:none;border-radius:8px;cursor:pointer;z-index:9999;';
  b.onclick = function(){ alert('你好，我是 AI 加的按钮 👋'); };
  document.body.appendChild(b);
})();
""",
            },
        }

    if any(k in p for k in ["表格", "table", "数据"]):
        return {
            "reply": "生成一个示例表格。",
            "target": context.get("app_id") and f"child:{context['app_id']}" or "parent",
            "script": {
                "lang": "js",
                "summary": "插入示例表格",
                "code": """
(function(){
  var d = document.createElement('div');
  d.style.cssText = 'position:fixed;left:50%;top:50%;transform:translate(-50%,-50%);background:#fff;border:1px solid #d4e2fc;border-radius:10px;padding:16px;z-index:9999;box-shadow:0 6px 24px rgba(26,124,255,.15);';
  d.innerHTML = '<table style="border-collapse:collapse;font-size:13px;"><thead><tr>' +
    '<th style="padding:6px 12px;border-bottom:1px solid #d4e2fc;">ID</th>' +
    '<th style="padding:6px 12px;border-bottom:1px solid #d4e2fc;">名称</th>' +
    '<th style="padding:6px 12px;border-bottom:1px solid #d4e2fc;">值</th>' +
    '</tr></thead><tbody>' +
    ['A','B','C'].map(function(k,i){
      return '<tr><td style="padding:6px 12px;">'+(i+1)+'</td><td style="padding:6px 12px;">'+k+'</td><td style="padding:6px 12px;">'+(Math.random()*100|0)+'</td></tr>';
    }).join('') + '</tbody></table>' +
    '<div style="text-align:right;margin-top:8px;"><button onclick="this.parentNode.remove()" style="background:none;border:none;color:#1a7cff;cursor:pointer;">关闭</button></div>';
  document.body.appendChild(d);
})();
""",
            },
        }

    # 默认：只回一条聊天消息
    return {
        "reply": f"收到你的消息：{prompt}（模拟回复）",
        "target": None,
        "script": None,
    }


@app.post("/llm")
async def api_llm(req: LlmRequest):
    """父页面/子页面把 prompt 提交给 AI。

    流程：
        1. 调 LLM（这里用 fake_llm 模拟）
        2. 如果返回了脚本，先存到 /scripts
        3. 写一条 kind=script 的消息给目标（通常是子页面）
        4. 再写一条 kind=chat 的回复给父页面
    """
    log_line(f"🤖 LLM prompt: {req.prompt[:60]}")
    result = fake_llm(req.prompt, req.context or {})

    # 先回一条 chat 消息给父页面（回复气泡）
    await handle_incoming_message({
        "from": "llm", "to": "parent", "kind": "chat",
        "payload": {"text": result["reply"]},
    })

    # 如果有脚本，存起来 + 推给子页面
    if result.get("script"):
        sid = uuid.uuid4().hex[:12]
        store.scripts[sid] = {
            "id": sid,
            "lang": result["script"]["lang"],
            "code": result["script"]["code"],
            "summary": result["script"]["summary"],
            "ts": time.time(),
        }
        target = result["target"] or "broadcast"
        await handle_incoming_message({
            "from": "llm", "to": target, "kind": "script",
            "payload": {
                "script_id": sid,
                "url": f"/scripts/{sid}",
                "lang": result["script"]["lang"],
                "summary": result["script"]["summary"],
            },
        })
        return {"success": True, "reply": result["reply"], "script_id": sid}

    return {"success": True, "reply": result["reply"]}


# ============================================================
# API - 日志
# ============================================================

@app.get("/log")
async def api_log():
    return {"success": True, "content": "\n".join(
        f"[{time.strftime('%H:%M:%S', time.localtime(m['ts']))}] "
        f"{m['from']} → {m['to']} · {m['kind']} · {str(m['payload'])[:120]}"
        for m in store.messages[-200:]
    )}


# ============================================================
# 页面
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.get("/health")
async def health():
    return {"ok": True, "apps": len(store.apps), "messages": len(store.messages),
            "scripts": len(store.scripts), "ws": {k: len(v) for k, v in store.sockets.items()}}


# ============================================================
# 启动
# ============================================================

def main():
    import uvicorn
    print("=" * 60)
    print("🛠  SurvX Studio")
    print("=" * 60)
    print(f"📡 http://{HOST}:{PORT}")
    print("=" * 60)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main()