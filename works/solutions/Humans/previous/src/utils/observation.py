# dashboard.py
# -*- coding: utf-8 -*-
"""
dashboard.py - QSeek 数据观测仪表盘
启动: python dashboard.py
访问: http://localhost:5000
"""

from flask import Flask, jsonify, render_template, request
import sqlite3
import json
import os
import time
import math

app = Flask(__name__)

实例根目录 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "实例")


def _connect(数据库路径):
    """统一数据库连接，只读模式，Row工厂"""
    conn = sqlite3.connect(f"file:{数据库路径}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def 获取实例列表():
    实例列表 = []
    if not os.path.exists(实例根目录):
        return 实例列表
    for name in sorted(os.listdir(实例根目录)):
        if name.startswith("."):
            continue
        db_path = os.path.join(实例根目录, name, "世界.db")
        if os.path.exists(db_path):
            try:
                conn = _connect(db_path)
                row = conn.execute("SELECT MIN(tick) as min_tick, MAX(tick) as max_tick FROM 状态").fetchone()
                t_min = row["min_tick"] if row and row["min_tick"] is not None else 0
                t_max = row["max_tick"] if row and row["max_tick"] is not None else 0
                conn.close()
                实例列表.append({
                    "name": name,
                    "db_path": db_path,
                    "tick_min": t_min,
                    "tick_max": t_max,
                })
            except Exception as e:
                实例列表.append({
                    "name": name,
                    "db_path": db_path,
                    "tick_min": 0,
                    "tick_max": 0,
                    "error": str(e),
                })
    return sorted(实例列表, key=lambda x: x["name"])


def 获取实例元信息(数据库路径):
    info = {
        "tick_range": [0, 0],
        "tables": [],
        "entities": [],
        "entity_fields": {},
        "table_columns": {},
    }
    try:
        conn = _connect(数据库路径)

        # tick 范围
        row = conn.execute("SELECT MIN(tick) as min_tick, MAX(tick) as max_tick FROM 状态").fetchone()
        if row and row["max_tick"] is not None:
            info["tick_range"] = [row["min_tick"] or 0, row["max_tick"]]

        # 所有表
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        info["tables"] = [t["name"] for t in tables]

        # 所有实体（状态表中的字段名）
        entities = conn.execute(
            "SELECT DISTINCT 字段名 FROM 状态 ORDER BY 字段名"
        ).fetchall()
        info["entities"] = [e["字段名"] for e in entities]

        # 每个实体的可量化字段（采样前200条，提取标量字段）
        for entity in info["entities"]:
            字段集合 = set()
            rows = conn.execute(
                "SELECT 值 FROM 状态 WHERE 字段名 = ? ORDER BY tick LIMIT 200",
                (entity,)
            ).fetchall()
            for r in rows:
                try:
                    obj = json.loads(r["值"])
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if isinstance(v, (int, float)):
                                字段集合.add(k)
                            elif isinstance(v, (list, tuple)) and len(v) > 0 and isinstance(v[0], (int, float)):
                                字段集合.add(k)
                except Exception:
                    pass
            info["entity_fields"][entity] = sorted(字段集合)

        # 每张表的列
        for table in info["tables"]:
            try:
                cursor = conn.execute(f'SELECT * FROM [{table}] LIMIT 1')
                info["table_columns"][table] = [desc[0] for desc in cursor.description]
            except Exception:
                info["table_columns"][table] = []

        conn.close()
    except Exception as e:
        info["error"] = str(e)

    return info


def 提取标量值(值json_str, 字段路径=None):
    try:
        obj = json.loads(值json_str)
    except Exception:
        return None

    if 字段路径 is None:
        if isinstance(obj, (int, float)):
            return obj
        if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], (int, float)):
            return obj[0]
        return None

    if isinstance(obj, dict) and 字段路径 in obj:
        val = obj[字段路径]
        if isinstance(val, (int, float)):
            return val
        if isinstance(val, (list, tuple)) and len(val) > 0 and isinstance(val[0], (int, float)):
            return val[0]
    return None


# ==================== API ====================

@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/instances")
def api_instances():
    return jsonify(获取实例列表())


@app.route("/api/instance/<name>/info")
def api_instance_info(name):
    db_path = os.path.join(实例根目录, name, "世界.db")
    if not os.path.exists(db_path):
        return jsonify({"error": "实例不存在"}), 404
    return jsonify(获取实例元信息(db_path))


@app.route("/api/instance/<name>/timeseries")
def api_timeseries(name):
    db_path = os.path.join(实例根目录, name, "世界.db")
    if not os.path.exists(db_path):
        return jsonify({"error": "实例不存在"}), 404

    source = request.args.get("source", "entity")
    target = request.args.get("target", "")
    field = request.args.get("field", "")
    tick_min = request.args.get("tick_min", type=int)
    tick_max = request.args.get("tick_max", type=int)

    if not target:
        return jsonify({"error": "缺少 target"}), 400

    data = []
    try:
        conn = _connect(db_path)

        if source == "entity":
            where = "字段名 = ?"
            params = [target]
            if tick_min is not None:
                where += " AND tick >= ?"
                params.append(tick_min)
            if tick_max is not None:
                where += " AND tick <= ?"
                params.append(tick_max)

            rows = conn.execute(
                f"SELECT tick, 值 FROM 状态 WHERE {where} ORDER BY tick", params
            ).fetchall()

            for r in rows:
                val = 提取标量值(r["值"], field)
                if val is not None and not (math.isnan(val) or math.isinf(val)):
                    data.append({"tick": r["tick"], "value": val})

        elif source == "table":
            safe_table = target.replace('"', '""')
            safe_field = field.replace('"', '""') if field else "值"

            where_parts = []
            params = []
            if tick_min is not None:
                where_parts.append("tick >= ?")
                params.append(tick_min)
            if tick_max is not None:
                where_parts.append("tick <= ?")
                params.append(tick_max)
            where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

            try:
                rows = conn.execute(
                    f'SELECT tick, "{safe_field}" as val FROM [{safe_table}]{where_clause} ORDER BY tick',
                    params
                ).fetchall()
                for r in rows:
                    try:
                        v = float(r["val"]) if r["val"] is not None else None
                        if v is not None and not (math.isnan(v) or math.isinf(v)):
                            data.append({"tick": r["tick"], "value": v})
                    except (ValueError, TypeError):
                        pass
            except Exception:
                pass

        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "source": source,
        "target": target,
        "field": field,
        "data": data,
        "count": len(data),
    })


@app.route("/api/instance/<name>/snapshot")
def api_snapshot(name):
    db_path = os.path.join(实例根目录, name, "世界.db")
    if not os.path.exists(db_path):
        return jsonify({"error": "实例不存在"}), 404

    tick = request.args.get("tick", type=int)

    try:
        conn = _connect(db_path)

        if tick is None:
            row = conn.execute("SELECT MAX(tick) as max_tick FROM 状态").fetchone()
            tick = row["max_tick"] if row and row["max_tick"] is not None else 0

        rows = conn.execute(
            "SELECT 字段名, 值 FROM 状态 WHERE tick = ?", (tick,)
        ).fetchall()

        snapshot = {}
        for r in rows:
            try:
                snapshot[r["字段名"]] = json.loads(r["值"])
            except Exception:
                snapshot[r["字段名"]] = r["值"]

        鲁滨逊经历 = conn.execute(
            "SELECT 事件类型, 描述 FROM 鲁滨逊经历 WHERE tick = ?", (tick,)
        ).fetchall()

        荒岛经历 = conn.execute(
            "SELECT 事件类型, 描述 FROM 荒岛经历 WHERE tick = ?", (tick,)
        ).fetchall()

        conn.close()

        return jsonify({
            "tick": tick,
            "snapshot": snapshot,
            "鲁滨逊经历": [{"类型": r["事件类型"], "描述": r["描述"]} for r in 鲁滨逊经历],
            "荒岛经历": [{"类型": r["事件类型"], "描述": r["描述"]} for r in 荒岛经历],
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/instance/<name>/table_data")
def api_table_data(name):
    db_path = os.path.join(实例根目录, name, "世界.db")
    if not os.path.exists(db_path):
        return jsonify({"error": "实例不存在"}), 404

    table = request.args.get("table", "状态")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 100, type=int)
    tick_min = request.args.get("tick_min", type=int)
    tick_max = request.args.get("tick_max", type=int)

    try:
        conn = _connect(db_path)

        safe_table = table.replace('"', '""')
        where_parts = []
        params = []
        if tick_min is not None:
            where_parts.append("tick >= ?")
            params.append(tick_min)
        if tick_max is not None:
            where_parts.append("tick <= ?")
            params.append(tick_max)
        where_clause = (" WHERE " + " AND ".join(where_parts)) if where_parts else ""

        count_row = conn.execute(
            f'SELECT COUNT(*) as cnt FROM [{safe_table}]{where_clause}', params
        ).fetchone()
        total = count_row["cnt"] if count_row else 0

        sample = conn.execute(f'SELECT * FROM [{safe_table}] LIMIT 1')
        columns = [desc[0] for desc in sample.description]

        offset = (page - 1) * per_page
        rows = conn.execute(
            f'SELECT * FROM [{safe_table}]{where_clause} ORDER BY tick LIMIT ? OFFSET ?',
            params + [per_page, offset]
        ).fetchall()

        data = []
        for r in rows:
            row_dict = {}
            for col in columns:
                val = r[col]
                if isinstance(val, str):
                    try:
                        row_dict[col] = json.loads(val)
                    except Exception:
                        row_dict[col] = val
                else:
                    row_dict[col] = val
            data.append(row_dict)

        conn.close()

        return jsonify({
            "table": table,
            "columns": columns,
            "total": total,
            "page": page,
            "per_page": per_page,
            "data": data,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("QSeek 数据观测台启动")
    print(f"实例目录: {实例根目录}")
    实例列表 = 获取实例列表()
    print(f"发现 {len(实例列表)} 个实例: {[i['name'] for i in 实例列表]}")
    print("访问 http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)