# -*- coding: utf-8 -*-
"""
register.py

中文：命令注册与转发脚本。使用 SQLite 存储命令到脚本版本的映射，并作为统一入口转发执行。
English: Command registry and dispatcher. Store command-to-script version mappings in SQLite and forward execution.

版本: 20260921101000
作者: quruyi
时间: 20260921101022  # 最后修改时间

用法:
    # 注册（当前目录，浮动最新版本）
    python register.py reg cplugin CreatePlugin

    # 注册（指定目录，浮动最新版本）
    python register.py reg cplugin src CreatePlugin

    # 注册（当前目录，锁定指定版本）
    python register.py reg cplugin CreatePlugin_20260921101000

    # 注册（指定目录，锁定指定版本）
    python register.py reg cplugin src CreatePlugin_20260921101000

    # 执行
    python register.py run cplugin src FinDataFetcher

说明:
    - 注册时必须给出脚本名，版本可选。
    - 不带版本：执行时在该目录下取该脚本的最新版本。
    - 带版本：执行时固定使用该版本，找不到则报错。
    - 只在注册时记录的目录内查找，不跨目录扩大搜索。
    - 同一个命令名重复注册时覆盖原记录，不追加历史。
"""

import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

DB_FILE = ".registry.db"
TABLE = "_register"

SCRIPT_PATTERN = re.compile(r"^(?P<name>.+)_(?P<version>\d{14})\.py$")


def connect():
    return sqlite3.connect(DB_FILE)


def init_table(conn):
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            key     TEXT PRIMARY KEY,
            value   TEXT,
            version TEXT
        )
    """)
    conn.commit()


def now_version() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d%H%M%S")


def register_command(conn, cmd_name, target_dir, script_name):
    value = os.path.join(target_dir, script_name)
    version = now_version()

    row = conn.execute(
        f"SELECT key FROM {TABLE} WHERE key = ?",
        (cmd_name,),
    ).fetchone()

    if row:
        conn.execute(
            f"UPDATE {TABLE} SET value = ?, version = ? WHERE key = ?",
            (value, version, cmd_name),
        )
        action = "已更新"
    else:
        conn.execute(
            f"INSERT INTO {TABLE} (key, value, version) VALUES (?, ?, ?)",
            (cmd_name, value, version),
        )
        action = "已注册"

    conn.commit()
    print(f"{action}: {cmd_name} -> {value}  version={version}")


def get_active_value(conn, cmd_name):
    row = conn.execute(
        f"SELECT value FROM {TABLE} WHERE key = ?",
        (cmd_name,),
    ).fetchone()
    return row[0] if row else None


def find_latest_script(target_dir, script_name):
    """在指定目录下查找 <script_name>_<14位版本>.py，取版本最大者"""
    if not os.path.isdir(target_dir):
        return None

    candidates = []
    for file_name in os.listdir(target_dir):
        m = SCRIPT_PATTERN.match(file_name)
        if not m:
            continue
        if m.group("name") == script_name:
            candidates.append((m.group("version"), file_name))

    if not candidates:
        return None

    candidates.sort()
    return os.path.join(target_dir, candidates[-1][1])


def resolve_script(value):
    """解析注册值，返回实际脚本路径。只在注册时记录的目录内查找。"""
    target_dir = os.path.dirname(value) or "."
    script_name = os.path.basename(value)

    m = SCRIPT_PATTERN.match(script_name)
    if m:
        # 已带版本，锁定该版本
        path = os.path.join(target_dir, script_name)
        return path if os.path.exists(path) else None

    # 不带版本，取该目录下最新版本
    return find_latest_script(target_dir, script_name)


def dispatch_command(conn, cmd_name, args):
    value = get_active_value(conn, cmd_name)
    if value is None:
        print(f"未注册的命令: {cmd_name}")
        sys.exit(1)

    script_path = resolve_script(value)
    if not script_path:
        print(f"未找到可用脚本: {value}")
        sys.exit(1)

    cmd = [sys.executable, script_path] + args
    subprocess.run(cmd)


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("reg", "run"):
        print("用法:")
        print("  注册: python register.py reg <命令名> [目录] <脚本名>")
        print("  执行: python register.py run <命令名> <参数...>")
        sys.exit(1)

    mode = sys.argv[1]
    conn = connect()
    init_table(conn)

    if mode == "reg":
        # python register.py reg cplugin CreatePlugin
        if len(sys.argv) == 4:
            cmd_name = sys.argv[2]
            target_dir = "."
            script_name = sys.argv[3]
        # python register.py reg cplugin src CreatePlugin
        elif len(sys.argv) == 5:
            cmd_name = sys.argv[2]
            target_dir = sys.argv[3]
            script_name = sys.argv[4]
        else:
            print("用法: python register.py reg <命令名> [目录] <脚本名>")
            sys.exit(1)

        register_command(conn, cmd_name, target_dir, script_name)

    else:  # run
        # python register.py run cplugin src FinDataFetcher
        if len(sys.argv) < 3:
            print("用法: python register.py run <命令名> <参数...>")
            sys.exit(1)

        cmd_name = sys.argv[2]
        args = sys.argv[3:]
        dispatch_command(conn, cmd_name, args)

    conn.close()


if __name__ == "__main__":
    main()