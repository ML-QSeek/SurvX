# -*- coding: utf-8 -*-
"""
codefield.py

中文：codefield 启动器。从 Matter 表取 f_main，动态加载对应 Q 并调用。
English: codefield launcher. Read f_main from Matter table, dynamically load and call the target Q.

版本: 20261004101159
作者: quruyi
时间: 20261004101159  # 最后修改时间

用法:
    python codefield.py
"""

import importlib.util
import os
import sqlite3
import sys

APP_NAME = "codefield"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, f"{APP_NAME}.db")
Q_DIR = os.path.join(BASE_DIR, "q")


def get_main_q():
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        f"SELECT value FROM {APP_NAME} WHERE key = ?",
        (f"{APP_NAME}_f_main",),
    ).fetchone()
    conn.close()
    return row[0] if row else None


def load_q(q_name):
    q_path = os.path.join(Q_DIR, f"{q_name}.py")
    if not os.path.exists(q_path):
        print(f"Q 文件不存在: {q_path}")
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
        print(f"未找到 Q 函数: {q_name}")
        sys.exit(1)

    q_func()


if __name__ == "__main__":
    main()
