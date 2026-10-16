# -*- coding: utf-8 -*-
"""
Store.py

中文：SurvX 引擎存储接口层。对 Matter / Energy 表做写入，只写不读。
English: SurvX engine store interface. Write-only access to Matter / Energy tables.

版本: 20261016120000
作者: quruyi
时间: 20261016120000  # 最后修改时间

用法:
    import Store

    cat = Store.init("/path/to/cat")

    # insert
    cat._parameter_i("Cat", "Phys_s_1", "35")
    cat._sequence_i("20261016120000", "Cat_c_1", "0.05")
    cat._experience_i("Cat", "20260918224523", "_state", "{}")
    cat.matter_i("FinancialMarkets_s_1", "Markets")

    # update
    cat._parameter_u({"id0": "Cat", "id1": "Phys_s_1"}, {"value": "35"})
    cat._register_u({"key": "Cat"}, {"value": "猫"})

    # upsert 表：_i 和 _u 走同一逻辑
    cat._register_i("Cat", "猫")

说明:
    - 前台按表分函数，动态生成，不写一堆 def
    - 后台统一 write(table, op, row, values)
    - 有 version 的表，op="i" 时 store 内部生成 version
    - upsert 表：_register / _language，有则 update，无则 insert
    - update 用 where + values，支持复合条件、部分更新
    - idx 自增由引擎建表时用 sequence 处理，store 不关心
"""

import os
import sqlite3
import time


# ---------- 表字段声明 ----------

SCHEMA = {
    "matter":      ["key", "value"],
    "_parameter":  ["id0", "id1", "value"],
    "_constraint": ["id0", "id1", "value"],
    "_relation":   ["id0", "id1", "value"],
    "_sequence":   ["_tick", "key", "value"],
    "_experience": ["_from", "_tick", "_type", "_value"],
    "_intent":     ["_from", "_tick", "key", "value"],
    "_feedback":   ["_from", "_tick", "value"],
    "_language":   ["key", "value"],
    "_train":      ["_target", "_tick", "key", "value"],
    "_report":     ["_type", "_tick", "key", "value"],
    "_llm":        ["id", "prompt", "reason"],
    "_register":   ["key", "value"],
    "_forge":      ["id", "_tick", "_module", "_action", "_target", "_result", "_reason"],
}

# 有 version 的表，insert 时 store 内部生成 version
VERSIONED = {"matter", "_parameter", "_constraint", "_relation", "_llm"}

# upsert 的表：有则 update，无则 insert
UPSERT = {"_register", "_language"}


def now_version() -> str:
    return time.strftime("%Y%m%d%H%M%S")


def connect_sqlite(path):
    try:
        return sqlite3.connect(path)
    except sqlite3.Error as e:
        raise RuntimeError(f"SQLite 打开失败: {path} -> {e}")


def connect_duckdb(path):
    try:
        import duckdb
    except ImportError:
        raise RuntimeError("缺少 duckdb 依赖，请先安装: pip install duckdb")
    try:
        return duckdb.connect(path)
    except Exception as e:
        raise RuntimeError(f"DuckDB 打开失败: {path} -> {e}")


def connect(self, table):
    if table == "matter":
        return connect_sqlite(self.sqlite_path)
    if table == "_forge":
        return connect_sqlite(self.forge_path)
    return connect_duckdb(self.duckdb_path)


def resolve_table(self, table):
    # matter 表名映射到实际表名
    if table == "matter":
        return self.app
    return table


def insert(conn, table, row):
    cols = list(row.keys())
    placeholders = ", ".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders})"
    conn.execute(sql, tuple(row[c] for c in cols))


def update(conn, table, where, values):
    set_clause = ", ".join([f"{c} = ?" for c in values])
    where_clause = " AND ".join([f"{c} = ?" for c in where])
    sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
    data = tuple(values.values()) + tuple(where.values())
    conn.execute(sql, data)


def exists(conn, table, where):
    where_clause = " AND ".join([f"{c} = ?" for c in where])
    sql = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
    cur = conn.execute(sql, tuple(where.values()))
    return cur.fetchone() is not None


# ---------- 后台统一写入 ----------

def write(self, table, op, row=None, values=None):
    conn = connect(self, table)
    real_table = resolve_table(self, table)
    try:
        if table in UPSERT:
            # upsert：有则 update，无则 insert
            where = {"key": row["key"]}
            if exists(conn, real_table, where):
                if op == "u" and values is not None:
                    update(conn, real_table, where, values)
                else:
                    update_values = {k: v for k, v in row.items() if k != "key"}
                    update(conn, real_table, where, update_values)
            else:
                insert(conn, real_table, row)
        elif op == "i":
            if table in VERSIONED:
                row["version"] = now_version()
            insert(conn, real_table, row)
        elif op == "u":
            if values is None:
                values = row
            update(conn, real_table, row, values)
        conn.commit()
    finally:
        conn.close()


# ---------- Store 对象 ----------

class Store:
    def __init__(self, project_dir, app=None):
        app = app or os.path.basename(project_dir)
        self.project_dir = project_dir
        self.app = app
        self.sqlite_path = os.path.join(project_dir, f"{app}.db")
        self.forge_path = os.path.join(project_dir, "_forge.db")
        self.duckdb_path = os.path.join(project_dir, f"_{app}.duckdb")

    def __getattr__(self, name):
        # name 形如 "_parameter_i" / "_register_u" / "matter_i"
        table, op = name.rsplit("_", 1)
        if op not in ("i", "u"):
            raise AttributeError(f"未知操作: {name}")
        clean = table.lstrip("_")
        fields = SCHEMA.get(clean)
        if fields is None:
            raise AttributeError(f"未知表: {name}")

        def call(*args, **kwargs):
            if op == "u":
                where, values = args
                return write(self, clean, op, where, values)
            row = dict(zip(fields, args))
            row.update(kwargs)
            return write(self, clean, op, row)

        return call


def init(project_dir, app=None):
    return Store(project_dir, app)