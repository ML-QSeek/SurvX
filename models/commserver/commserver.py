# -*- coding: utf-8 -*-
"""
commserver.py

中文：动态路由服务。启动时从 routes.json 动态加载同目录 py 文件并注册 HTTP 路由，运行时支持注册、热重载、注销 HTTP 路由；同时提供 WebSocket 广播频道的动态注册与注销。
English: Dynamic route service. On startup loads py files next to routes.json and registers HTTP routes; supports registering, hot-reloading and unregistering HTTP routes at runtime; also provides dynamic register/unregister for WebSocket broadcast channels.

版本: 20260929150000
作者: quruyi
时间: 20260929150000 # 最后修改时间

用法:
    # 启动服务（默认监听 0.0.0.0:8000）
    python commserver.py

    # 启动前准备好同目录的 routes.json 和业务 py 文件
    # routes.json 内容示例（名字 = 模块名 = 函数名 = 路径）:
    # ["hello", "user", "calc"]

    # HTTP 路由管理
    /_register?name=hello         注册新的 HTTP 路由
    /_reload?name=hello           完全热重载某个 HTTP 路由
    /_unregister?name=hello       注销某个 HTTP 路由
    /_routes                      查看所有 HTTP 路由

    # WebSocket 频道管理
    /_register_ws?name=news       注册 WS 广播频道 /ws/news
    /_unregister_ws?name=news     注销 WS 广播频道 /ws/news
    /_ws_channels                 查看所有 WS 频道及连接数

说明:
    - HTTP：一个名字同时作为模块名、函数名和路径，模块文件放在 commserver.py 同目录
    - HTTP：routes.json 里 method 统一为 "*"，即支持 GET/POST/PUT/DELETE/PATCH
    - HTTP：注册用 /_register，更新用 /_reload，删除用 /_unregister，均为 GET/POST，只传 name
    - HTTP：/_reload 会先彻底移除旧路由，再强制重新加载模块，保证完全覆盖
    - HTTP：/_unregister 会同时清掉路由、_registered 记录与模块缓存，等于彻底卸载
    - HTTP：删除或新增路由后会清空 openapi_schema，使 /docs 重新生成
    - WS：一个名字对应一个 /ws/{name} 广播频道，所有频道共用同一个 handler，按 path 隔离连接池
    - WS：每个连接有独立发送队列与发送协程，广播时只入队不等待网络，队列满则丢弃该条消息
    - WS：单条消息上限 64KB，每连接每秒最多 50 条，单条发送超时 3 秒
    - WS：注销频道时会踢掉该频道的所有连接并停止其发送协程
    - 管理接口 /_* 不做鉴权，生产环境请自行加 token 校验
    - 可选依赖 uvloop，安装后在 __main__ 中自动启用
    - 管理接口均可通过 GET 直接传参，例如 /_register?name=hello
"""

import json
import sys
import importlib
import inspect
import asyncio
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Callable

from fastapi import (
    FastAPI,
    Request,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.routing import APIRoute, APIWebSocketRoute
from pydantic import BaseModel


# ============================================================
# 生命周期（lifespan）
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期钩子。

    - 启动时：加载 routes.json 并注册 http 路由
    - 关闭时：打印一条日志（可按需扩展清理逻辑）
    """
    register_routes()
    print("\n✅ 所有动态路由已加载完成\n")
    yield
    print("\n🛑 commserver 正在关闭\n")


# ============================================================
# 基础配置
# ============================================================

# 所有文件都在同一目录
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "routes.json"

app = FastAPI(title="Dynamic Routes API", lifespan=lifespan)

# 模块缓存：module_name -> module 对象
_module_cache: dict[str, Any] = {}

# 已注册的 http 路由：key = "METHOD path"，value = APIRoute
_registered: dict[str, APIRoute] = {}

# http 路由支持的全部方法（routes.json 里 method 写 "*" 时使用）
ALL_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]


# ============================================================
# 模块动态加载
# ============================================================

def load_module(module_name: str, force_reload: bool = False):
    """
    动态加载同目录下的 py 文件。

    参数
    ----
    module_name : str
        模块名（不含 .py），比如 "hello" 对应 hello.py
    force_reload : bool
        True 时强制重新读取文件、重新执行，用于热重载

    返回
    ----
    module 对象
    """
    # 非强制重载时，命中缓存直接返回
    if not force_reload and module_name in _module_cache:
        return _module_cache[module_name]

    module_path = BASE_DIR / f"{module_name}.py"
    if not module_path.exists():
        raise FileNotFoundError(f"模块文件不存在: {module_path}")

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法加载模块: {module_name}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # 覆盖 sys.modules 与本地缓存，保证下次拿到的是新版本
    sys.modules[module_name] = module
    _module_cache[module_name] = module
    return module


def unload_module(module_name: str):
    """
    从内存中卸载模块。

    - 从 _module_cache 删除
    - 从 sys.modules 删除
    - 不物理删除文件

    用于 /_unregister 时彻底卸载，保证下次 /_register 是全新加载。
    """
    _module_cache.pop(module_name, None)
    sys.modules.pop(module_name, None)


# ============================================================
# HTTP endpoint 构建
# ============================================================

def build_endpoint(func: Callable):
    """
    根据业务函数自动构建 FastAPI endpoint。

    支持的函数形态：
    1. 无参：                  def hello()
    2. 单参数且是 Pydantic：    def add(req: AddReq)
    3. 普通参数（路径/查询）：   def calc(a: float, b: float)
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.values())

    # --- 情况 1：无参 ---
    if not params:
        async def endpoint_no_args():
            return _wrap_result(func())
        return endpoint_no_args

    # --- 情况 2：单参数且是 Pydantic Model -> 作为请求体 ---
    if len(params) == 1 and isinstance(params[0].annotation, type) \
            and issubclass(params[0].annotation, BaseModel):
        model_cls = params[0].annotation

        async def endpoint_body(body: model_cls):  # type: ignore
            return _wrap_result(func(body))
        return endpoint_body

    # --- 情况 3：普通参数 -> 路径参数优先，否则当查询参数 ---
    async def endpoint_with_params(request: Request):
        kwargs = {}
        path_params = request.path_params
        for p in params:
            if p.name in path_params:
                # 路径参数：从 url path 取，做类型转换
                value = path_params[p.name]
                if p.annotation in (int, float, str, bool):
                    value = p.annotation(value)
                kwargs[p.name] = value
            else:
                # 查询参数：从 ?a=1 取
                q = request.query_params.get(p.name)
                if q is None:
                    if p.default is inspect.Parameter.empty:
                        raise HTTPException(422, f"缺少参数: {p.name}")
                    kwargs[p.name] = p.default
                else:
                    if p.annotation in (int, float):
                        q = p.annotation(q)
                    elif p.annotation is bool:
                        q = q.lower() in ("1", "true", "yes")
                    kwargs[p.name] = q
        return _wrap_result(func(**kwargs))
    return endpoint_with_params


def _wrap_result(result):
    """
    统一包装业务函数的返回值。

    - dict / list / str / int / float / bool / None：原样返回
    - Response 子类（FileResponse / JSONResponse / StreamingResponse 等）：原样返回
    - Pydantic Model：转 dict
    - 其他：转 str
    """
    if isinstance(result, (dict, list, str, int, float, bool)) or result is None:
        return result
    if isinstance(result, Response):        # 放行 Response，保证文件下载等能用
        return result
    if isinstance(result, BaseModel):
        return result.model_dump()
    return str(result)


# ============================================================
# HTTP 路由工具
# ============================================================

def _key(method: str, path: str) -> str:
    """_registered 的 key：'GET /hello'"""
    return f"{method.upper()} {path}"


def _exists(path: str) -> bool:
    """该 path 是否已有 http 路由"""
    return any(isinstance(r, APIRoute) and r.path == path for r in app.router.routes)


def _remove_by_path(path: str) -> int:
    """
    按 path 彻底移除 http 路由。

    - 从 app.router.routes 移除所有 path 匹配的 APIRoute
    - 清掉 _registered 里该 path 的所有 key
    - 清 app.openapi_schema，让 /docs 重新生成
    - 返回移除的路由条数

    注意：模块缓存的清理由调用方决定（/_reload 不清，/_unregister 清），
          因为 /_reload 需要紧接着重新加载同一模块。
    """
    removed = 0
    # list() 复制一份再遍历，避免边遍历边删除出问题
    for r in list(app.router.routes):
        if isinstance(r, APIRoute) and r.path == path:
            app.router.routes.remove(r)
            removed += 1

    # 清 _registered 中所有该 path 的 key
    for k in [k for k in _registered if k.endswith(" " + path)]:
        _registered.pop(k)

    if removed:
        app.openapi_schema = None
    return removed


def register_one(path, method, module_name, func_name, force_reload=False):
    """
    注册单个 http 路由。

    参数
    ----
    path : str            路由路径，如 "/hello"
    method : str | list    "*" / "GET" / ["GET","POST"]
    module_name : str     模块名
    func_name : str       函数名
    force_reload : bool   是否强制重新加载模块

    注意：本函数不负责删旧，删旧由调用方处理。
    """
    # 解析 methods
    if method == "*":
        methods = ALL_METHODS
    elif isinstance(method, str):
        methods = [method.upper()]
    else:
        methods = [m.upper() for m in method]

    # 加载模块 + 取函数
    module = load_module(module_name, force_reload=force_reload)
    func = getattr(module, func_name, None)
    if func is None:
        raise AttributeError(f"{module_name}.py 中不存在函数 {func_name}")

    # 构建 endpoint
    endpoint = build_endpoint(func)
    endpoint.__name__ = f"{module_name}_{func_name}"

    # 构造 APIRoute
    route = APIRoute(
        path=path,
        endpoint=endpoint,
        methods=methods,
        name=f"{module_name}.{func_name}",
        summary=f"动态路由 {'/'.join(methods)} {path}",
    )
    # 插到最前面，避免被内置路由（/docs、/openapi.json 等）影响
    app.router.routes.insert(0, route)
    # 新增路由后清缓存
    app.openapi_schema = None

    # 记录
    for m in methods:
        _registered[_key(m, path)] = route

    print(f"[注册] {'/'.join(methods):30s} {path:20s} -> {module_name}.{func_name}")
    return {
        "name": func_name,
        "path": path,
        "methods": methods,
        "module": module_name,
        "func": func_name,
        "reloaded": force_reload,
    }


def _resolve(name: str):
    """
    一个名字同时是模块名、函数名、路径。

    name="hello" -> ("/hello", "hello", "hello")
    name="/hello" 也会归一化成 ("/hello", "hello", "hello")
    """
    name = name.lstrip("/")
    return f"/{name}", name, name


# ============================================================
# 启动时加载 http 路由
# ============================================================

def register_routes():
    """
    读取 routes.json 并注册 http 路由。

    支持的格式：
    1. 纯列表：["hello", "user", "calc"]        （method 固定 "*"）
    2. 对象：  {"routes": ["hello"], "method": "*"}
    """
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    if isinstance(config, list):
        names = config
        global_method = "*"
    else:
        names = config.get("routes", [])
        global_method = config.get("method", "*")

    for name in names:
        try:
            path, module_name, func_name = _resolve(name)
            register_one(
                path=path,
                method=global_method,
                module_name=module_name,
                func_name=func_name,
            )
        except Exception as e:
            # 单个失败不影响其他
            print(f"[跳过] {name}: {e}")


# ============================================================
# WebSocket 广播频道
# ============================================================
#
# 设计要点
# --------
# 1. 一个频道 = 一个 path = /ws/{name}
# 2. 所有频道共用一个 broadcast_handler，靠 websocket.url.path 隔离
# 3. 每个连接有：
#       - 一个 asyncio.Queue（发送队列）
#       - 一个发送协程（从队列取消息，实际 send_text）
#    广播时只往队列 put_nowait，不等待网络 -> 慢客户端不拖累别人
# 4. 队列满 -> 丢消息（类似 ZMQ HWM 满丢消息）
# 5. 单条发送有超时，超时断开该连接
# 6. 单条消息有大小限制，单连接有频率限制
# ============================================================

# 每个频道的连接池：path -> set[WebSocket]
_ws_pools: dict[str, set[WebSocket]] = {}

# 每个连接的发送队列：WebSocket -> asyncio.Queue
_ws_queues: dict[WebSocket, asyncio.Queue] = {}

# 每个连接的发送协程：WebSocket -> asyncio.Task
_ws_senders: dict[WebSocket, asyncio.Task] = {}

# 限制参数
WS_MAX_MSG = 64 * 1024        # 单条消息最大 64KB
WS_QUEUE_MAX = 200            # 每连接发送队列长度上限，满了丢消息
WS_SEND_TIMEOUT = 3.0         # 单条发送超时（秒）
WS_RATE_PER_SEC = 50          # 每连接每秒最多接收多少条


async def _sender_loop(ws: WebSocket, queue: asyncio.Queue):
    """
    每个连接一个发送协程。

    从队列里取消息，通过 ws.send_text 发出。
    - 单条发送超时 WS_SEND_TIMEOUT 秒
    - 出错或超时 -> 退出循环（连接会被 handler 的 finally 清理）
    """
    try:
        while True:
            text = await queue.get()
            try:
                await asyncio.wait_for(
                    ws.send_text(text), timeout=WS_SEND_TIMEOUT
                )
            except Exception:
                # 发送失败或超时，退出（该连接基本废了）
                break
    except asyncio.CancelledError:
        # 主动取消（注销频道、连接断开等），正常退出
        pass


def _push(ws: WebSocket, text: str):
    """
    往某连接的发送队列塞消息，不等待网络。

    队列满了就直接丢消息（等价 ZMQ HWM 满丢消息）。
    这是广播快的关键：调用方永远不阻塞。
    """
    q = _ws_queues.get(ws)
    if q is None:
        return
    try:
        q.put_nowait(text)
    except asyncio.QueueFull:
        # 对方消费不过来，丢弃这条
        pass


async def broadcast_handler(websocket: WebSocket):
    """
    所有 ws 频道共用的处理函数。

    流程：
    1. accept 连接
    2. 加入该 path 的连接池
    3. 为这个连接创建发送队列 + 发送协程
    4. 循环接收消息，做大小/频率校验，然后广播给同频道所有人
    5. 断开时清理：移出池、取消发送协程、删队列
    """
    path = websocket.url.path

    await websocket.accept()

    pool = _ws_pools.setdefault(path, set())
    pool.add(websocket)

    # 为这个连接创建发送队列和发送协程
    queue: asyncio.Queue = asyncio.Queue(maxsize=WS_QUEUE_MAX)
    _ws_queues[websocket] = queue
    _ws_senders[websocket] = asyncio.create_task(_sender_loop(websocket, queue))

    # 频率限制用
    last_sec = int(time.time())
    count = 0

    try:
        while True:
            msg = await websocket.receive_text()

            # --- 消息大小限制 ---
            if len(msg) > WS_MAX_MSG:
                await websocket.close(code=1009)   # 1009: message too big
                break

            # --- 频率限制：每连接每秒最多 WS_RATE_PER_SEC 条 ---
            sec = int(time.time())
            if sec != last_sec:
                last_sec = sec
                count = 0
            count += 1
            if count > WS_RATE_PER_SEC:
                await websocket.close(code=1008)   # 1008: policy violation
                break

            # --- 广播：只 push 到同频道每个人的队列，不等待网络 ---
            for peer in list(pool):
                _push(peer, msg)

    except WebSocketDisconnect:
        # 客户端主动断开，正常
        pass
    except Exception:
        # 其他异常兜底，避免影响别的连接
        pass
    finally:
        # 从频道池移除
        pool.discard(websocket)

        # 停掉发送协程
        task = _ws_senders.pop(websocket, None)
        if task:
            task.cancel()
        _ws_queues.pop(websocket, None)

        # 频道空了就移除，避免 _ws_pools 无限增长
        if not pool:
            _ws_pools.pop(path, None)


def _ws_exists(name: str) -> bool:
    """判断某个 ws 频道是否已注册"""
    path = f"/ws/{name}"
    return any(
        isinstance(r, APIWebSocketRoute) and r.path == path
        for r in app.router.routes
    )


def _normalize_ws_name(name: str) -> str:
    """
    归一化频道名：
    - 去掉开头的 /
    - 允许传 "ws/chat"，也允许 "chat"
    """
    name = name.lstrip("/")
    if name.startswith("ws/"):
        name = name[3:]
    return name


def register_ws(name: str):
    """
    动态注册一个 ws 广播频道。

    - name="news" -> 注册 /ws/news
    - 所有频道共用 broadcast_handler
    """
    name = _normalize_ws_name(name)
    path = f"/ws/{name}"

    if _ws_exists(name):
        raise ValueError(f"WS 已存在: {path}")

    route = APIWebSocketRoute(
        path=path,
        endpoint=broadcast_handler,
        name=f"ws.{name}",
    )
    app.router.routes.insert(0, route)
    app.openapi_schema = None

    print(f"[注册WS] {path}")
    return {"name": name, "path": path, "type": "ws"}


async def unregister_ws(name: str) -> int:
    """
    注销一个 ws 频道。

    做的事：
    1. 从 app.router.routes 移除该 APIWebSocketRoute
    2. 踢掉该频道的所有连接（await ws.close()）
    3. 停掉这些连接的发送协程、清队列
    4. 从 _ws_pools 移除该频道
    """
    name = _normalize_ws_name(name)
    path = f"/ws/{name}"

    # 1. 移除路由
    removed = 0
    for r in list(app.router.routes):
        if isinstance(r, APIWebSocketRoute) and r.path == path:
            app.router.routes.remove(r)
            removed += 1

    # 2. 踢连接 + 清理
    pool = _ws_pools.pop(path, None)
    kicked = 0
    if pool:
        for ws in list(pool):
            kicked += 1
            # 先停发送协程，再关连接
            task = _ws_senders.pop(ws, None)
            if task:
                task.cancel()
            _ws_queues.pop(ws, None)
            # 直接在 async 函数里 await 关闭，异常不吞
            try:
                await ws.close(code=1001)          # 1001: going away
            except Exception:
                pass

    if removed:
        app.openapi_schema = None

    print(f"[注销WS] {path}（移除 {removed} 条路由，踢掉 {kicked} 个连接）")
    return removed


# ============================================================
# 动态管理接口
# ============================================================

class NameReq(BaseModel):
    """管理接口统一请求体：只需要一个 name"""
    name: str


async def _read_name(request: Request) -> str:
    """
    从请求里读 name 参数。

    - GET：从 query 取
    - POST：优先从 JSON body 取，其次从 query 取
    """
    if request.method == "POST":
        try:
            body = await request.json()
        except Exception:
            body = {}
        name = body.get("name") or request.query_params.get("name")
    else:
        name = request.query_params.get("name")

    if not name:
        raise HTTPException(400, "缺少参数: name")
    return name


# ---------------- HTTP 路由管理 ----------------

@app.api_route("/_register", methods=["GET", "POST"], summary="注册新函数（只传 name）")
async def api_register(request: Request):
    """注册一个新的 http 路由；已存在则报错，请用 /_reload。"""
    name = await _read_name(request)
    path, module_name, func_name = _resolve(name)

    if _exists(path):
        raise HTTPException(400, f"路由已存在: {path}，请用 /_reload 更新")
    try:
        return register_one(path, "*", module_name, func_name, force_reload=False)
    except Exception as e:
        raise HTTPException(400, f"注册失败: {e}")


@app.api_route("/_reload", methods=["GET", "POST"], summary="完全热重载某个函数（只传 name）")
async def api_reload(request: Request):
    """
    完全热重载：先移除旧路由，再强制重新加载模块并注册。

    注意：这里只清路由，不清模块缓存；紧接着的 register_one 会用
    force_reload=True 重新执行文件，把 _module_cache / sys.modules 覆盖掉。
    """
    name = await _read_name(request)
    path, module_name, func_name = _resolve(name)

    if not _exists(path):
        raise HTTPException(400, f"路由不存在: {path}，请用 /_register 注册")
    try:
        _remove_by_path(path)
        return register_one(path, "*", module_name, func_name, force_reload=True)
    except Exception as e:
        raise HTTPException(400, f"重载失败: {e}")


@app.api_route("/_unregister", methods=["GET", "POST"], summary="删除指定路由（只传 name）")
async def api_unregister(request: Request):
    """
    删除一个 http 路由，并卸载对应模块缓存。

    - 路由从 app.router.routes 移除
    - _registered 记录清掉
    - 模块从 _module_cache / sys.modules 移除
    这样下次 /_register 会是全新加载，不会命中旧缓存。
    """
    name = await _read_name(request)
    path, module_name, _ = _resolve(name)

    if not _exists(path):
        raise HTTPException(400, f"路由不存在: {path}")
    removed = _remove_by_path(path)
    unload_module(module_name)
    print(f"[删除] {path}（移除 {removed} 条，已卸载模块 {module_name}）")
    return {"name": name, "path": path, "removed": removed}


@app.get("/_routes", summary="查看已注册的所有 http 路由")
async def list_routes():
    """列出所有 http 路由（不含 ws）。"""
    return [
        {"path": r.path, "methods": list(r.methods), "name": r.name}
        for r in app.router.routes
        if isinstance(r, APIRoute)
    ]


# ---------------- WebSocket 频道管理 ----------------

@app.api_route("/_register_ws", methods=["GET", "POST"], summary="注册 ws 广播频道（只传 name）")
async def api_register_ws(request: Request):
    """
    注册一个 ws 广播频道，例如：
        /_register_ws?name=news   -> /ws/news
    连接 /ws/news 的客户端之间互相广播，与其他频道隔离。
    """
    name = await _read_name(request)
    try:
        return register_ws(name)
    except Exception as e:
        raise HTTPException(400, f"注册WS失败: {e}")


@app.api_route("/_unregister_ws", methods=["GET", "POST"], summary="注销 ws 广播频道（只传 name）")
async def api_unregister_ws(request: Request):
    """
    注销一个 ws 广播频道，会同时踢掉该频道的所有连接。
    """
    name = await _read_name(request)
    if not _ws_exists(_normalize_ws_name(name)):
        raise HTTPException(400, f"WS 不存在: /ws/{_normalize_ws_name(name)}")
    removed = await unregister_ws(name)
    return {"name": _normalize_ws_name(name), "removed": removed}


@app.get("/_ws_channels", summary="查看所有 ws 频道")
async def list_ws_channels():
    """
    列出当前所有 ws 频道以及各自的连接数。
    """
    channels = []
    for r in app.router.routes:
        if isinstance(r, APIWebSocketRoute):
            pool = _ws_pools.get(r.path, set())
            channels.append({
                "path": r.path,
                "name": r.name,
                "clients": len(pool),
            })
    return channels


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    import uvicorn

    # 优先使用 uvloop：基于 libuv 的事件循环，性能接近 Node
    try:
        import uvloop
        uvloop.install()
        print("[uvloop] 已启用")
    except ImportError:
        print("[uvloop] 未安装，使用默认事件循环（pip install uvloop 可提速）")

    # 直接传 app 对象，避免文件名与 "xxx:app" 写死绑定的问题
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)