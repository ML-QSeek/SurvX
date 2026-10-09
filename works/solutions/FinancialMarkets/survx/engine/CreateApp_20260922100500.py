# -*- coding: utf-8 -*-
"""
CreateApp.py

中文：根据目录与 app 名生成 dbfs 应用实例，包含 SQLite 结构库、DuckDB 能量库、Q 目录与启动器。
English: Generate a dbfs app instance by directory and app name, including SQLite structure db, DuckDB energy db, Q directory and launcher.

版本: 20260922100500
作者: quruyi
时间: 20260922100500  # 最后修改时间

用法:
    # 默认当前目录
    python CreateApp.py myapp

    # 指定目录
    python CreateApp.py src myapp

产物:
    <目录>/myapp/
    ├── myapp.db          # SQLite，Matter 结构，表名 myapp
    ├── _forge.db         # SQLite，质量控制表 _forge
    ├── _myapp.duckdb     # DuckDB，Energy 所有表
    ├── myapp.py          # 启动器
    └── q/
        └── qxxxxxx.py    # 主入口 Q

说明:
    - app 名即目录名，先创建 <目录>/<app名>/
    - myapp.db 只放本体结构：Matter 表
    - _forge.db 单独文件，放质量控制表 _forge
    - _myapp.duckdb 放所有 Energy 表
    - 启动器从 Matter 表取 f_main，动态 import 对应 Q 并调用
    - Q 名随机生成，格式 q + 随机数，暂不查重
"""

import os
import random
import sqlite3
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    import duckdb
except ImportError:
    duckdb = None

AUTHOR = "quruyi"


def now_version() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d%H%M%S")


def rand_q_name() -> str:
    return "q" + str(random.randint(1000, 99999999))


def create_sqlite_matter(db_path: str, app_name: str, q_ref: str, version: str):
    conn = sqlite3.connect(db_path)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {app_name} (
            key     TEXT,
            value   TEXT,
            version TEXT
        )
    """)
    conn.execute(
        f"INSERT INTO {app_name} (key, value, version) VALUES (?, ?, ?)",
        (f"{app_name}_f_main", q_ref, version),
    )
    conn.commit()
    conn.close()


def create_sqlite_forge(db_path: str):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _forge (
            id       TEXT,
            _tick    TEXT,
            _module  TEXT,
            _action  TEXT,
            _target  TEXT,
            _result  TEXT,
            _reason  TEXT
        )
    """)
    conn.commit()
    conn.close()


def create_duckdb_energy(db_path: str):
    if duckdb is None:
        print("错误: 未安装 duckdb，无法创建 Energy 库")
        sys.exit(1)

    conn = duckdb.connect(db_path)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _parameter (
            id0      TEXT,
            id1      TEXT,
            value    TEXT,
            idx      INTEGER,
            version  TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _constraint (
            id0      TEXT,
            id1      TEXT,
            value    TEXT,
            idx      INTEGER,
            version  TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _relation (
            id0      TEXT,
            id1      TEXT,
            value    TEXT,
            idx      INTEGER,
            version  TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _sequence (
            _tick    TEXT,
            key      TEXT,
            value    TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _experience (
            _from    TEXT,
            _tick    TEXT,
            _type    TEXT,
            _value   TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _intent (
            _from    TEXT,
            _tick    TEXT,
            key      TEXT,
            value    TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _feedback (
            _from    TEXT,
            _tick    TEXT,
            value    TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _language (
            key      TEXT,
            value    TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _train (
            _target  TEXT,
            _tick    TEXT,
            key      TEXT,
            value    TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _report (
            _type    TEXT,
            _tick    TEXT,
            key      TEXT,
            value    TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _llm (
            id       TEXT,
            version  TEXT,
            prompt   TEXT,
            reason   TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS _register (
            key      TEXT,
            value    TEXT
        )
    """)

    conn.close()


def write_q_file(q_dir: str, q_name: str, app_name: str, version: str):
    os.makedirs(q_dir, exist_ok=True)
    q_path = os.path.join(q_dir, f"{q_name}.py")
    content = f'''# -*- coding: utf-8 -*-
"""
{q_name}.py

中文：{app_name} 主入口 Q。
English: {app_name} main entry Q.

版本: {version}
作者: {AUTHOR}
时间: {version}  # 最后修改时间
"""


def {q_name}():
    # prompt: {app_name} 主入口
    # reason: 从 f_main 指向此函数，作为启动入口
    print("hello world")
    return
'''
    with open(q_path, "w", encoding="utf-8") as f:
        f.write(content)


def write_launcher(app_dir: str, app_name: str, version: str):
    launcher_path = os.path.join(app_dir, f"{app_name}.py")
    content = f'''# -*- coding: utf-8 -*-
"""
{app_name}.py

中文：{app_name} 启动器。从 Matter 表取 f_main，动态加载对应 Q 并调用。
English: {app_name} launcher. Read f_main from Matter table, dynamically load and call the target Q.

版本: {version}
作者: {AUTHOR}
时间: {version}  # 最后修改时间

用法:
    python {app_name}.py
"""

import importlib.util
import os
import sqlite3
import sys

APP_NAME = "{app_name}"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, f"{{APP_NAME}}.db")
Q_DIR = os.path.join(BASE_DIR, "q")


def get_main_q():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        f"SELECT value FROM {{APP_NAME}} WHERE key = ?",
        (f"{{APP_NAME}}_f_main",),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def load_q(q_name):
    q_path = os.path.join(Q_DIR, f"{{q_name}}.py")
    if not os.path.exists(q_path):
        print(f"Q 文件不存在: {{q_path}}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location(q_name, q_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, q_name, None)


def main():
    main_ref = get_main_q()
    if not main_ref or not main_ref.startswith("q:"):
        print("未声明主入口 f_main")
        sys.exit(1)

    q_name = main_ref[2:]
    q_func = load_q(q_name)
    if not callable(q_func):
        print(f"未找到 Q 函数: {{q_name}}")
        sys.exit(1)

    q_func()


if __name__ == "__main__":
    main()
'''
    with open(launcher_path, "w", encoding="utf-8") as f:
        f.write(content)


def create_app(target_dir: str, app_name: str):
    app_dir = os.path.join(target_dir, app_name)
    os.makedirs(app_dir, exist_ok=True)

    version = now_version()
    q_name = rand_q_name()
    q_ref = f"q:{q_name}"

    create_sqlite_matter(
        os.path.join(app_dir, f"{app_name}.db"),
        app_name, q_ref, version,
    )
    create_sqlite_forge(os.path.join(app_dir, "_forge.db"))
    create_duckdb_energy(os.path.join(app_dir, f"_{app_name}.duckdb"))
    write_q_file(os.path.join(app_dir, "q"), q_name, app_name, version)
    write_launcher(app_dir, app_name, version)

    return app_dir


def main():
    if len(sys.argv) == 2:
        target_dir = "."
        app_name = sys.argv[1]
    elif len(sys.argv) == 3:
        target_dir = sys.argv[1]
        app_name = sys.argv[2]
    else:
        print("用法: python CreateApp.py [目录] <app名>")
        sys.exit(1)

    app_dir = create_app(target_dir, app_name)
    print(f"已生成: {app_dir}")


if __name__ == "__main__":
    main()