# -*- coding: utf-8 -*-
"""
Query.py

中文：SurvX 引擎基础查询接口层。对 Matter / Energy 表做基础查询，只读不写。
English: SurvX engine query interface. Read-only basic queries for Matter / Energy tables.

版本: 20261016130000
作者: quruyi
时间: 20261016130000  # 最后修改时间

用法:
    import Query

    cat = Query.init("/path/to/cat")

    # 按条件查询，返回全部字段
    cat._parameter_q({"id0": "Cat", "id1": "Phys_s_1"})

    # 按条件查询，只返回指定字段
    cat._parameter_q({"id0": "Cat"}, {"value", "version"})

说明:
    - 前台按表分函数，动态生成，不写一堆 def
    - 后台统一 read(table, where, select)
    - 返回值统一为 list of dict
    - 复杂查询（表达式、跨表、搜索算法）不在此层，另行封装
"""

import os
import sqlite3


# ---------- 表字段声明 ----------

SCHEMA = {
    "matter":      ["key", "value", "version"],
    "_parameter":  ["id0", "id1", "value", "idx", "version"],
    "_constraint": ["id0", "id1", "value", "idx", "version"],
    "_relation":   ["id0", "id1", "value", "idx", "version"],
    "_sequence":   ["_tick", "key", "value"],
    "_experience": ["_from", "_tick", "_type", "_value"],
    "_intent":     ["_from", "_tick", "key", "value"],
    "_feedback":   ["_from", "_tick", "value"],
    "_language":   ["key", "value"],
    "_train":      ["_target", "_tick", "key", "value"],
    "_report":     ["_type", "_tick", "key", "value"],
    "_llm":        ["id", "version", "prompt", "reason"],
    "_register":   ["key", "value"],
    "_forge":      ["id", "_tick", "_module", "_action", "_target", "_result", "_reason"],
}


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


def read(conn, table, where, select=None):
    if select:
        select_clause = ", ".join(select)
    else:
        select_clause = "*"

    if where:
        where_clause = " AND ".join([f"{c} = ?" for c in where])
        sql = f"SELECT {select_clause} FROM {table} WHERE {where_clause}"
        cur = conn.execute(sql, tuple(where.values()))
    else:
        sql = f"SELECT {select_clause} FROM {table}"
        cur = conn.execute(sql)

    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


# ---------- 后台统一查询 ----------

def query(self, table, where=None, select=None):
    conn = connect(self, table)
    real_table = resolve_table(self, table)
    try:
        return read(conn, real_table, where, select)
    finally:
        conn.close()


# ---------- Query 对象 ----------

class Query:
    def __init__(self, project_dir, app=None):
        app = app or os.path.basename(project_dir)
        self.project_dir = project_dir
        self.app = app
        self.sqlite_path = os.path.join(project_dir, f"{app}.db")
        self.forge_path = os.path.join(project_dir, "_forge.db")
        self.duckdb_path = os.path.join(project_dir, f"_{app}.duckdb")

    def __getattr__(self, name):
        # name 形如 "_parameter_q" / "matter_q"
        table, op = name.rsplit("_", 1)
        if op != "q":
            raise AttributeError(f"未知操作: {name}")
        clean = table.lstrip("_")
        fields = SCHEMA.get(clean)
        if fields is None:
            raise AttributeError(f"未知表: {name}")

        def call(where=None, select=None):
            return query(self, clean, where, select)

        return call


def init(project_dir, app=None):
    return Query(project_dir, app)