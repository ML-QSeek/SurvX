# -*- coding: utf-8 -*-
"""
publish.py

中文：脚本发布工具。注册发布映射，按映射同步单个脚本文件，只做文件复制，不碰数据库。
English: Script publish tool. Register publish mappings, sync a single script file by mapping, file copy only, no database.

版本: 20260921101000
作者: quruyi
时间: 20260921101022  # 最后修改时间

用法:
    # 注册发布映射：源目录 -> 目标目录
    python publish.py reg pubw models works
    python publish.py reg pubi works instances

    # 按注册命令同步单个脚本
    python publish.py pubw tools/xx/yy.py

说明:
    - 源目录和目标目录在注册时指定，执行时只补脚本子路径
    - 子路径原样拼到源和目标后面：<source>/<子路径> -> <target>/<子路径>
    - 一个目标目录只允许对应一个源目录，重复注册目标目录会提示是否覆盖
    - 只做正向发布，不反向回流
    - 只同步单个文件，不支持目录同步
    - 不碰 .db / .duckdb / 数据库文件
    - 同名文件直接覆盖
"""

import os
import shutil
import sqlite3
import sys

DB_FILE = ".registry.db"
TABLE = "_publish"

SKIP_EXTS = (".db", ".duckdb", ".sqlite", ".sqlite3")


def connect():
    return sqlite3.connect(DB_FILE)


def init_table(conn):
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            key     TEXT PRIMARY KEY,
            source  TEXT,
            target  TEXT
        )
    """)
    conn.commit()


def is_db_file(file_name: str) -> bool:
    return file_name.lower().endswith(SKIP_EXTS)


def register(conn, cmd_name: str, source: str, target: str):
    row = conn.execute(
        f"SELECT key, source FROM {TABLE} WHERE target = ?",
        (target,),
    ).fetchone()

    if row:
        old_key, old_source = row
        print(f"目标目录已被注册: {target}")
        print(f"  当前映射: {old_key}: {old_source} -> {target}")
        answer = input("是否覆盖？(y/n): ").strip().lower()
        if answer != "y":
            print("已取消")
            return
        conn.execute(
            f"UPDATE {TABLE} SET source = ? WHERE key = ?",
            (source, old_key),
        )
        conn.commit()
        print(f"已更新: {old_key}: {source} -> {target}")
        return

    conn.execute(
        f"INSERT INTO {TABLE} (key, source, target) VALUES (?, ?, ?)",
        (cmd_name, source, target),
    )
    conn.commit()
    print(f"已注册: {cmd_name}: {source} -> {target}")


def sync_file(conn, cmd_name: str, sub_path: str):
    row = conn.execute(
        f"SELECT source, target FROM {TABLE} WHERE key = ?",
        (cmd_name,),
    ).fetchone()

    if not row:
        print(f"未注册的命令: {cmd_name}")
        sys.exit(1)

    source, target = row
    src = os.path.join(source, sub_path)
    dst = os.path.join(target, sub_path)

    if not os.path.exists(src):
        print(f"源路径不存在: {src}")
        sys.exit(1)

    if not os.path.isfile(src):
        print(f"只支持单文件同步，不支持目录: {src}")
        sys.exit(1)

    file_name = os.path.basename(src)

    if is_db_file(file_name):
        print(f"不允许发布数据库文件: {file_name}")
        sys.exit(1)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    print(f"已发布: {src} -> {dst}")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  注册: python publish.py reg <命令> <源目录> <目标目录>")
        print("  发布: python publish.py <命令> <脚本子路径>")
        sys.exit(1)

    conn = connect()
    init_table(conn)

    first = sys.argv[1]

    # 注册
    if first == "reg":
        if len(sys.argv) != 5:
            print("用法: python publish.py reg <命令> <源目录> <目标目录>")
            sys.exit(1)
        register(conn, sys.argv[2], sys.argv[3], sys.argv[4])
        conn.close()
        return

    # 按注册命令发布单个脚本
    if len(sys.argv) == 3:
        sync_file(conn, first, sys.argv[2])
        conn.close()
        return

    print("参数不正确")
    sys.exit(1)


if __name__ == "__main__":
    main()