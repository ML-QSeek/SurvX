# -*- coding: utf-8 -*-
"""
SimpleCounter_20261009100424.py

中文：SimpleCounter hoc 插件脚本。最小生命体：体力自然流失，耗尽即死亡。
English: SimpleCounter hoc plugin script. Minimal life entity: stamina depletes
         naturally, death occurs when it reaches zero.

版本: 20261009100424
作者: quruyi
时间: 20261009100424  # 最后修改时间

用法:
    python SimpleCounter_20261009100424.py

说明:
    最小生命体示例。模拟荒岛上的体力自然流失：不进食的情况下，体力每个 tick
    按变动表达式递减，直到体力降到 0，主体死亡。

    结构：
        SimpleCounter_s_1  body   身体结构
        stamina            独立主体，体力，无额外结构
        Ratio              独立主体，变动规则，无额外结构
        SimpleCounter_f_main  主入口，指向 q64203993

    数据：
        _parameter   SimpleCounter_s_1-stamina  初始体力 10（idx=1）
                     param_1-Ratio              体力的变动表达式 val - 1（idx=2）
        _constraint  SimpleCounter_s_1-stamina  存续约束 val >= 0
        _sequence    每个 tick 的体力快照
        _experience  死亡事件归档 _type = _death

    执行逻辑：
        每 tick 先扫参数表中的 Ratio 变动规则，再通过 param_N 解析到目标参数
        （idx=N），顺链找到约束。不硬编码任何字段名。
        顺序：扫 Ratio → 解析 param_N → 找值 → 找约束 → 处理。

    验证能力：
        结构蓝图声明、独立主体引入、参数表/约束表读写、内联 Q 表达式求值、
        tick 循环推进、存续约束校验、死亡语义、tick 间隔与过程留痕、
        变动规则自动发现（不硬编码）、param_N 派生 ID 解析。

    备注：
        eval 为 hoc 阶段临时求值手段，迁 dbfs 时替换为引擎受限求值器。
        param_N 为引用层派生 ID，落库时展开为真实 key（id0=真实参数 key，id1=指标名）。
"""

import datetime
import time

# ============================================================
# 1. 结构蓝图（Matter）
# ============================================================
SimpleCounter = {}
SimpleCounter["SimpleCounter_s_1"] = "body"
SimpleCounter["stamina"] = ""
SimpleCounter["Ratio"] = ""
SimpleCounter["SimpleCounter_f_main"] = "q:q64203993"

# ============================================================
# 2. 初始数值（Energy）
# ============================================================
_parameter = {
    "SimpleCounter_s_1-stamina": [["10", 1, "20261009100424"]],
    "param_1-Ratio": [["q:```val - 1```", 2, "20261009100424"]],
}
_constraint = {
    "SimpleCounter_s_1-stamina": [["q:```val >= 0```", 1, "20261009100424"]],
}
_relation = {}
_sequence = []
_experience = {}
_report = {}
_llm = {}

# ============================================================
# 3. Q 函数
# ============================================================
def _now():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def _eval_inline(expr, val):
    # 内联 Q 求值：去掉 "q:```" 和 "```"，替换 val，求值
    if expr.startswith("q:```") and expr.endswith("```"):
        body = expr[5:-3]
    else:
        body = expr
    return eval(body.replace("val", str(val)))

def _resolve_param_ref(id0):
    # 解析派生 ID：param_N → idx=N 的参数记录真实 key
    if id0.startswith("param_"):
        try:
            n = int(id0[6:])
        except ValueError:
            return None
        for key, records in _parameter.items():
            for rec in records:
                if len(rec) >= 2 and rec[1] == n:
                    return key
        return None
    return id0

def _latest_value(key):
    # 取该 key 下 version 最大的那条记录的值
    records = _parameter.get(key)
    if not records:
        return None
    latest = max(records, key=lambda r: r[2])
    return latest[0]

def _find_ratio_rules():
    # 扫参数表，返回所有 Ratio 规则：[(目标参数真实 key, 变动表达式), ...]
    rules = []
    for key, records in _parameter.items():
        id0, _, id1 = key.partition("-")
        if id1 == "Ratio":
            target_key = _resolve_param_ref(id0)
            if target_key:
                latest = max(records, key=lambda r: r[2])
                rules.append((target_key, latest[0]))
    return rules

def _find_constraint(value_key):
    # 用参数真实 key 找对应约束表达式
    records = _constraint.get(value_key)
    if not records:
        return None
    latest = max(records, key=lambda r: r[2])
    return latest[0]

def q64203993():
    # prompt: 体力从 10 递减到 0，到 0 死亡
    # reason: 扫 Ratio 规则，经 param_N 解析到目标参数，顺链找约束；不硬编码
    rules = _find_ratio_rules()
    if not rules:
        print("未找到任何 Ratio 变动规则")
        return

    # 初始：把当前值落 _state
    _state["_tick"] = _now()
    for value_key, _expr in rules:
        _state[value_key] = int(_latest_value(value_key))
    init_view = {k: v for k, v in _state.items() if k != "_tick"}
    print(f"[{_state['_tick']}] [init] {init_view}")

    while True:
        time.sleep(1)  # 每 tick 间隔 1 秒

        for value_key, ratio_expr in rules:
            cons_expr = _find_constraint(value_key)
            if not cons_expr:
                continue

            cur = _state[value_key]
            new = _eval_inline(ratio_expr, cur)
            ok = _eval_inline(cons_expr, new)

            if not ok:
                tick = _now()
                _experience.setdefault("SimpleCounter", {})[tick] = {
                    "_type": "_death",
                    "_value": f"{value_key} 体力耗尽",
                }
                print(f"[{tick}] 候选 {new} 违反约束 → 死亡，停在 {cur}")
                return

            tick = _now()
            _state["_tick"] = tick
            _state[value_key] = new
            _sequence.append({"_tick": tick, value_key: new})
            print(f"[{tick}] {value_key}: {cur} -> {new}")

# ============================================================
# 4. 内存表 / 注册表
# ============================================================
_state = {}
_register = {
    "SimpleCounter": "最小生命体",
    "SimpleCounter_s_1": "body",
    "stamina": "体力",
    "Ratio": "变动规则",
    "q64203993": "SimpleCounter 主入口",
}

# ============================================================
# 5. 启动
# ============================================================
if __name__ == "__main__":
    main_ref = SimpleCounter.get("SimpleCounter_f_main")
    if main_ref and main_ref.startswith("q:"):
        q_name = main_ref[2:]
        q_func = globals().get(q_name)
        if callable(q_func):
            q_func()
        else:
            print(f"未找到 Q 函数: {q_name}")
    else:
        print("未声明主入口: SimpleCounter_f_main")