# -*- coding: utf-8 -*-
"""
HelloWorld_20261008093825.py

中文：HelloWorld hoc 插件脚本。
English: HelloWorld hoc plugin script.

版本: 20261008093825
作者: quruyi
时间: 20261008093825  # 最后修改时间

用法:
    python HelloWorld_20261008093825.py
"""

# ============================================================
# 1. 结构蓝图（Matter）
# ============================================================
HelloWorld = {}

# [F] 特征层
HelloWorld["HelloWorld_f_main"] = "q:q44905478"

# ============================================================
# 2. Q 函数
# ============================================================
def q44905478():
    # prompt: HelloWorld 主入口
    # reason: 从 main 指向此函数，作为脚本启动入口
    print("hello world")
    return

# ============================================================
# 3. 启动
# ============================================================
if __name__ == "__main__":
    main_ref = HelloWorld.get("HelloWorld_f_main")
    if main_ref and main_ref.startswith("q:"):
        q_name = main_ref[2:]
        q_func = globals().get(q_name)
        if callable(q_func):
            q_func()
        else:
            print(f"未找到 Q 函数: {q_name}")
    else:
        print("未声明主入口: HelloWorld_f_main")
