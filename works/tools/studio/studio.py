# -*- coding: utf-8 -*-
"""
studio.py

中文：SQL / Python 本地工作台后端（FastAPI 版）
      通过系统对话框打开本地目录，浏览文件树，操作 SQLite / DuckDB，运行 Python 脚本。

用法:
    pip install fastapi uvicorn jinja2 duckdb
    python studio.py

HTTP 路由（页面）:
    GET  /                            主页（渲染 index.html）

HTTP 路由（API - 工作目录）:
    POST /api/workspace/pick          弹系统文件夹选择框，返回选中的路径
    POST /api/workspace/open          直接打开指定路径  body: {"path": "D:/myproj"}
    GET  /api/workspace               获取当前工作目录和文件树

HTTP 路由（API - 项目清单）:
    GET  /api/projects                读取 projects.json，返回分类项目清单

HTTP 路由（API - 文件）:
    GET  /api/file?name=app.py        读取文件内容（name 支持相对路径 sub/a.py）
    POST /api/file/save               保存文件  body: {"name": "app.py", "content": "..."}
    POST /api/file/create             新建空文件 body: {"name": "sub/test.py"}
    POST /api/file/delete             删除文件  body: {"name": "test.py"}

HTTP 路由（API - 数据库）:
    POST /api/db/tables               列出数据库所有表  body: {"db": "data.db"}
    POST /api/db/preview              预览表前 N 条   body: {"db": "data.db", "table": "users", "limit": 10}
    POST /api/sql                     执行 SQL        body: {"db": "data.db", "sql": "SELECT ..."}

HTTP 路由（API - Python）:
    POST /api/run                     运行 Python 文件 body: {"file": "app.py"}

HTTP 路由（API - 日志）:
    GET  /api/log                     获取日志
    POST /api/log/clear               清空日志

配置（环境变量）:
    STUDIO_HOST           默认 0.0.0.0
    STUDIO_PORT           默认 8090
    RUN_TIMEOUT           默认 180 秒
    PYTHON_BIN            默认 python
    STUDIO_MODELS_ROOT    项目根目录，默认 <studio.py 所在目录>/../../models
    STUDIO_PROJECTS_FILE  项目清单 JSON，默认 <studio.py 所在目录>/projects.json
"""

import os
import json
import time
import sqlite3
import subprocess
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

# ============================================================
# 配置
# ============================================================

BASE_DIR = Path(__file__).parent.resolve()


class Config:
    HOST = os.environ.get("STUDIO_HOST", "0.0.0.0")
    PORT = int(os.environ.get("STUDIO_PORT", "8090"))
    RUN_TIMEOUT = int(os.environ.get("RUN_TIMEOUT", "180"))
    PYTHON_BIN = os.environ.get("PYTHON_BIN", "python")

    BASE_DIR = BASE_DIR

    MODELS_ROOT = Path(
        os.environ.get("STUDIO_MODELS_ROOT", str(BASE_DIR / "../../models"))
    ).resolve()

    PROJECTS_FILE = Path(
        os.environ.get("STUDIO_PROJECTS_FILE", str(BASE_DIR / "projects.json"))
    ).resolve()


config = Config()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("studio")

# ============================================================
# 全局状态
# ============================================================

class State:
    workspace: Optional[Path] = None
    log: List[str] = []


state = State()

TYPE_MAP = {
    ".db": "sqlite", ".sqlite": "sqlite", ".sqlite3": "sqlite", ".db3": "sqlite",
    ".duckdb": "duckdb", ".ddb": "duckdb",
    ".py": "python",
}

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "env",
             "node_modules", ".idea", ".vscode", ".mypy_cache",
             ".pytest_cache", ".ruff_cache", "dist", "build", ".tox"}


def get_file_type(name: str) -> str:
    return TYPE_MAP.get(Path(name).suffix.lower(), "text")


def log_line(msg: str) -> None:
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    state.log.append(line)
    if len(state.log) > 500:
        state.log = state.log[-500:]


def require_workspace() -> Path:
    if state.workspace is None:
        raise HTTPException(status_code=400, detail="尚未打开工作目录")
    return state.workspace


def safe_join(name: str) -> Path:
    """把相对路径解析到工作目录内，禁止越界。"""
    ws = require_workspace()
    if not name:
        raise HTTPException(status_code=400, detail="非法文件名")
    if "\x00" in name:
        raise HTTPException(status_code=400, detail="非法文件名")
    name = name.replace("\\", "/").lstrip("/")
    target = (ws / name).resolve()
    try:
        target.relative_to(ws.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="非法文件名")
    return target


def build_tree(base: Path, rel: str = "") -> List[Dict[str, Any]]:
    nodes: List[Dict[str, Any]] = []
    try:
        entries = sorted(base.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    except Exception:
        return nodes

    dirs: List[Dict[str, Any]] = []
    files: List[Dict[str, Any]] = []

    for f in entries:
        if f.name.startswith("."):
            continue
        rel_path = f"{rel}/{f.name}" if rel else f.name

        if f.is_dir():
            if f.name in SKIP_DIRS:
                continue
            children = build_tree(f, rel_path)
            dirs.append({
                "type": "dir",
                "name": f.name,
                "path": rel_path,
                "children": children,
            })
        elif f.is_file():
            try:
                size = f.stat().st_size
            except Exception:
                size = 0
            files.append({
                "type": get_file_type(f.name),
                "name": f.name,
                "path": rel_path,
                "size": size,
            })

    return dirs + files


def list_tree() -> List[Dict[str, Any]]:
    ws = state.workspace
    if ws is None or not ws.exists():
        return []
    return build_tree(ws, "")


# ============================================================
# 项目清单加载
# ============================================================

def load_projects_catalog() -> Dict[str, Any]:
    path = config.PROJECTS_FILE
    if not path.exists():
        logger.warning(f"项目清单不存在: {path}")
        return {"groups": []}
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        logger.warning(f"项目清单解析失败: {e}")
        return {"groups": []}

    if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
        logger.warning("项目清单格式不对：顶层应为 {'groups': [...]}")
        return {"groups": []}
    return data


def _project_path(name: str) -> Path:
    root = config.MODELS_ROOT
    target = (root / name).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        raise HTTPException(status_code=400, detail="非法项目名")
    return target


# ============================================================
# FastAPI 应用
# ============================================================

app = FastAPI(title="SQL/Python Studio", version="1.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(config.BASE_DIR))

FILES_DIR = config.BASE_DIR / "files"
FILES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(FILES_DIR)), name="files")


# ============================================================
# 请求模型
# ============================================================

class WorkspaceOpenRequest(BaseModel):
    path: str = Field(..., min_length=1)


class FileSaveRequest(BaseModel):
    name: str = Field(..., min_length=1)
    content: str = ""


class FileCreateRequest(BaseModel):
    name: str = Field(..., min_length=1)


class FileDeleteRequest(BaseModel):
    name: str = Field(..., min_length=1)


class DbTablesRequest(BaseModel):
    db: str = Field(..., min_length=1)


class DbPreviewRequest(BaseModel):
    db: str = Field(..., min_length=1)
    table: str = Field(..., min_length=1)
    limit: int = 10


class SqlRequest(BaseModel):
    db: str = Field(..., min_length=1)
    sql: str = Field(..., min_length=1)


class RunRequest(BaseModel):
    file: str = Field(..., min_length=1)


# ============================================================
# 页面路由
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# ============================================================
# API - 项目清单
# ============================================================

@app.get("/api/projects")
async def api_projects():
    catalog = load_projects_catalog()
    root = config.MODELS_ROOT
    root_exists = root.is_dir()

    groups = []
    for g in catalog.get("groups", []):
        items = []
        for p in g.get("projects", []):
            name = p.get("name", "")
            if not name:
                continue
            try:
                path = _project_path(name)
            except HTTPException:
                continue
            items.append({
                "name": name,
                "title": p.get("title", name),
                "path": str(path),
                "exists": path.is_dir(),
            })
        groups.append({
            "id": g.get("id", ""),
            "name": g.get("name", ""),
            "desc": g.get("desc", ""),
            "icon": g.get("icon", "📦"),
            "projects": items,
        })

    return {
        "success": True,
        "models_root": str(root),
        "models_root_exists": root_exists,
        "projects_file": str(config.PROJECTS_FILE),
        "groups": groups,
    }


# ============================================================
# API - 工作目录
# ============================================================

@app.post("/api/workspace/pick")
def api_workspace_pick():
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        return {"success": False, "error": "当前 Python 环境缺少 tkinter，无法弹出对话框"}

    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        initial = str(state.workspace) if state.workspace else str(Path.home())
        path = filedialog.askdirectory(title="选择工作目录", initialdir=initial)
        root.destroy()
    except Exception as e:
        return {"success": False, "error": f"弹窗失败: {e}"}

    if not path:
        return {"success": False, "error": "未选择目录"}

    p = Path(path).resolve()
    if not p.is_dir():
        return {"success": False, "error": "不是有效目录"}

    state.workspace = p
    state.log = []
    log_line(f"📂 打开工作目录: {p}")
    logger.info(f"打开工作目录: {p}")

    return {
        "success": True,
        "workspace": str(p),
        "tree": list_tree(),
    }


@app.post("/api/workspace/open")
async def api_workspace_open(req: WorkspaceOpenRequest):
    raw = req.path.strip().strip('"').strip("'")
    if not raw:
        return {"success": False, "error": "路径不能为空"}

    p = Path(raw).expanduser()
    try:
        p = p.resolve()
    except Exception as e:
        return {"success": False, "error": f"路径解析失败: {e}"}

    if not p.exists():
        return {"success": False, "error": f"路径不存在: {p}"}
    if not p.is_dir():
        return {"success": False, "error": f"不是目录: {p}"}

    state.workspace = p
    state.log = []
    log_line(f"📂 打开工作目录: {p}")
    logger.info(f"打开工作目录: {p}")

    return {
        "success": True,
        "workspace": str(p),
        "tree": list_tree(),
    }


@app.get("/api/workspace")
async def api_workspace_get():
    if state.workspace is None:
        return {"success": True, "workspace": None, "tree": []}
    return {
        "success": True,
        "workspace": str(state.workspace),
        "tree": list_tree(),
    }


# ============================================================
# API - 文件
# ============================================================

@app.get("/api/file")
async def api_file_get(name: str = Query(..., min_length=1)):
    path = safe_join(name)
    if not path.exists() or not path.is_file():
        return {"success": False, "error": "文件不存在"}
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return {"success": False, "error": "文件不是 UTF-8 文本，无法编辑"}
    except Exception as e:
        return {"success": False, "error": f"读取失败: {e}"}

    log_line(f"📄 打开文件: {name}")
    return {
        "success": True,
        "name": name,
        "type": get_file_type(name),
        "content": content,
    }


@app.post("/api/file/save")
async def api_file_save(req: FileSaveRequest):
    path = safe_join(req.name)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(req.content, encoding="utf-8")
    except Exception as e:
        log_line(f"❌ 保存失败 {req.name}: {e}")
        return {"success": False, "error": f"保存失败: {e}"}

    log_line(f"💾 保存文件: {req.name} ({len(req.content)} 字符)")
    logger.info(f"保存文件: {path}")
    return {"success": True, "tree": list_tree()}


@app.post("/api/file/create")
async def api_file_create(req: FileCreateRequest):
    name = req.name.strip().replace("\\", "/").lstrip("/")
    if not name:
        return {"success": False, "error": "文件名不能为空"}

    path = safe_join(name)
    if path.exists():
        return {"success": False, "error": f"文件已存在: {name}"}
    if path.is_dir():
        return {"success": False, "error": f"同名目录已存在: {name}"}

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("", encoding="utf-8")
    except Exception as e:
        return {"success": False, "error": f"创建失败: {e}"}

    log_line(f"🆕 新建文件: {name}")
    return {"success": True, "name": name, "tree": list_tree()}


@app.post("/api/file/delete")
async def api_file_delete(req: FileDeleteRequest):
    path = safe_join(req.name)
    if not path.exists():
        return {"success": False, "error": "文件不存在"}
    if not path.is_file():
        return {"success": False, "error": "不是文件"}

    try:
        path.unlink()
    except Exception as e:
        return {"success": False, "error": f"删除失败: {e}"}

    log_line(f"🗑 删除文件: {req.name}")
    return {"success": True, "tree": list_tree()}


# ============================================================
# API - 数据库
# ============================================================

def _open_db(db_name: str):
    path = safe_join(db_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"数据库不存在: {db_name}")

    kind = get_file_type(db_name)
    if kind == "sqlite":
        conn = sqlite3.connect(str(path))
        return conn, "sqlite"
    elif kind == "duckdb":
        try:
            import duckdb
        except ImportError:
            raise HTTPException(status_code=500, detail="未安装 duckdb：pip install duckdb")
        conn = duckdb.connect(str(path), read_only=False)
        return conn, "duckdb"
    else:
        raise HTTPException(status_code=400, detail=f"不是数据库文件: {db_name}")


def _query_tables(conn, kind: str) -> List[Dict[str, Any]]:
    tables = []
    cur = conn.cursor()
    if kind == "sqlite":
        cur.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
    else:
        try:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema='main'
                ORDER BY table_name
            """)
        except Exception:
            cur.execute("SHOW TABLES")
    for (name,) in cur.fetchall():
        try:
            cur.execute(f'SELECT COUNT(*) FROM "{name}"')
            rows = cur.fetchone()[0]
        except Exception:
            rows = -1
        tables.append({"name": name, "rows": rows})
    return tables


@app.post("/api/db/tables")
async def api_db_tables(req: DbTablesRequest):
    try:
        conn, kind = _open_db(req.db)
    except HTTPException as e:
        log_line(f"❌ 打开数据库失败 {req.db}: {e.detail}")
        return {"success": False, "error": e.detail}

    try:
        tables = _query_tables(conn, kind)
        log_line(f"🗄️ 列出表 {req.db}: {len(tables)} 张")
        return {"success": True, "db": req.db, "kind": kind, "tables": tables}
    except Exception as e:
        log_line(f"❌ 查询表失败 {req.db}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


@app.post("/api/db/preview")
async def api_db_preview(req: DbPreviewRequest):
    try:
        conn, kind = _open_db(req.db)
    except HTTPException as e:
        log_line(f"❌ 打开数据库失败 {req.db}: {e.detail}")
        return {"success": False, "error": e.detail}

    try:
        limit = max(1, min(req.limit, 1000))
        cur = conn.cursor()
        cur.execute(f'SELECT * FROM "{req.table}" LIMIT {limit}')
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = [list(r) for r in cur.fetchall()]
        log_line(f"👁️ 预览 {req.db}.{req.table} 前 {len(rows)} 条")
        return {"success": True, "db": req.db, "table": req.table,
                "columns": columns, "rows": rows}
    except Exception as e:
        log_line(f"❌ 预览失败 {req.db}.{req.table}: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()


@app.post("/api/sql")
async def api_sql(req: SqlRequest):
    try:
        conn, kind = _open_db(req.db)
    except HTTPException as e:
        log_line(f"❌ 打开数据库失败 {req.db}: {e.detail}")
        return {"success": False, "error": e.detail}

    t0 = time.time()
    try:
        cur = conn.cursor()
        cur.execute(req.sql)

        if cur.description:
            columns = [d[0] for d in cur.description]
            rows = [list(r) for r in cur.fetchall()]
            elapsed = int((time.time() - t0) * 1000)
            log_line(f"▶ SQL [{req.db}] {elapsed}ms → {len(rows)} 行")
            return {"success": True, "db": req.db, "columns": columns,
                    "rows": rows, "elapsed_ms": elapsed}
        else:
            conn.commit()
            elapsed = int((time.time() - t0) * 1000)
            affected = cur.rowcount if cur.rowcount is not None else -1
            log_line(f"▶ SQL [{req.db}] {elapsed}ms → 影响 {affected} 行")
            return {"success": True, "db": req.db, "columns": [], "rows": [],
                    "affected": affected, "elapsed_ms": elapsed}
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        log_line(f"❌ SQL 错误 [{req.db}] {elapsed}ms: {e}")
        return {"success": False, "error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ============================================================
# API - Python 运行
# ============================================================

# ★ 改动 1：用 Popen 逐行读 stdout/stderr，实时写入 state.log
#    - 前端轮询 /api/log 就能看到输出一行一行冒出来
#    - 超时逻辑保留，超时后 kill 进程
#    - 返回值结构与原来一致（success/status/output/elapsed_ms/returncode）

@app.post("/api/run")
async def api_run(req: RunRequest):
    ws = require_workspace()
    path = safe_join(req.file)
    if not path.exists():
        log_line(f"❌ 运行失败: 文件不存在 {req.file}")
        return {"success": False, "error": "文件不存在"}
    if path.suffix.lower() != ".py":
        log_line(f"❌ 运行失败: 不是 .py 文件 {req.file}")
        return {"success": False, "error": "只能运行 .py 文件"}

    log_line(f"▶ 运行 {req.file}")
    logger.info(f"运行: {path}")
    t0 = time.time()

    proc = None
    try:
        proc = subprocess.Popen(
            [config.PYTHON_BIN, str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,      # 合并 stderr 到 stdout，保持原始顺序
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=str(ws),
            bufsize=1,                     # 行缓冲
        )
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        log_line(f"❌ 启动失败: {e}")
        return {"success": False, "error": str(e), "elapsed_ms": elapsed}

    output_lines: List[str] = []
    timed_out = False

    try:
        # 逐行读，边读边写日志（前端轮询 /api/log 就能看到）
        for line in proc.stdout:
            line = line.rstrip("\r\n")
            output_lines.append(line)
            log_line(f"  {line}")
            # 超时检查：每读一行检查一次
            if time.time() - t0 > config.RUN_TIMEOUT:
                timed_out = True
                proc.kill()
                break
    except Exception as e:
        log_line(f"❌ 读取输出异常: {e}")

    try:
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

    elapsed = int((time.time() - t0) * 1000)
    combined = "\n".join(output_lines)

    if timed_out:
        log_line(f"⏰ 运行超时（>{config.RUN_TIMEOUT}s）")
        return {
            "success": True,
            "status": "timeout",
            "output": combined + f"\n\n运行超时（超过 {config.RUN_TIMEOUT} 秒）",
            "elapsed_ms": elapsed,
        }

    rc = proc.returncode if proc.returncode is not None else -1
    status = "success" if rc == 0 else "error"
    log_line(f"✓ 运行结束 ({status}) {elapsed}ms")

    return {
        "success": True,
        "status": status,
        "output": combined,
        "elapsed_ms": elapsed,
        "returncode": rc,
    }


# ============================================================
# API - 日志
# ============================================================

@app.get("/api/log")
async def api_log_get():
    return {"success": True, "content": "\n".join(state.log)}


@app.post("/api/log/clear")
async def api_log_clear():
    state.log = []
    return {"success": True}


# ============================================================
# 启动入口
# ============================================================

def main():
    import uvicorn
    print("=" * 60)
    print("🛠  SQL/Python Studio")
    print("=" * 60)
    print(f"📡 服务地址: http://{config.HOST}:{config.PORT}")
    print(f"⏰ 运行超时: {config.RUN_TIMEOUT} 秒")
    print(f"🐍 Python:   {config.PYTHON_BIN}")
    print(f"📦 项目根:   {config.MODELS_ROOT}")
    print(f"📋 清单文件: {config.PROJECTS_FILE}")
    print("=" * 60)
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()