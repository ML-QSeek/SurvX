# -*- coding: utf-8 -*-
"""
CreatePlugin.py

中文：根据目录与实体名生成 hoc 插件脚本文件。
English: Generate a hoc plugin script file by directory and entity name.

版本: 20260921101000
作者: quruyi
时间: 20260921101022  # 最后修改时间

用法:
    # 默认当前目录
    python CreatePlugin.py FinDataFetcher

    # 指定目录
    python CreatePlugin.py src FinDataFetcher
"""

import os
import random
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

AUTHOR = "quruyi"


def now_version() -> str:
    """返回北京时间版本号，格式 YYYYMMDDHHMMSS"""
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y%m%d%H%M%S")


def rand_q_name() -> str:
    """生成随机 Q 函数名，格式 q + 4~8 位数字"""
    return "q" + str(random.randint(1000, 99999999))


def build_script(entity_name: str, version: str, q_name: str) -> str:
    """构建完整 hoc 插件脚本内容"""
    return f'''# -*- coding: utf-8 -*-
"""
{entity_name}_{version}.py

中文：{entity_name} hoc 插件脚本。
English: {entity_name} hoc plugin script.

版本: {version}
作者: {AUTHOR}
时间: {version}  # 最后修改时间

用法:
    python {entity_name}_{version}.py
"""

# ============================================================
# 1. 结构蓝图（Matter）
# ============================================================
{entity_name} = {{}}

# [S] 结构层
#{entity_name}["{entity_name}_s_1"] = "..."
# [F] 特征层
{entity_name}["{entity_name}_f_main"] = "q:{q_name}"
# [Ego] 看需求添加
#{entity_name}["(){entity_name}_s_1"] = "..."
# [Env] 看需求添加
#{entity_name}["[]{entity_name}_s_1"] = "..."

# ============================================================
# 2. 初始数值（Energy）
# ============================================================
{entity_name}["_parameter"] = {{}}    # _parameter 参数表
{entity_name}["_constraint"] = {{}}   # _constraint 约束表
{entity_name}["_relation"] = {{}}     # _relation 关系表
{entity_name}["_sequence"] = {{}}     # _sequence 序列表
{entity_name}["_experience"] = {{}}   # _experience 经历表
{entity_name}["_report"] = {{}}       # _report 报告总结表
{entity_name}["_llm"] = {{}}          # _llm AI 协作表

# Ego 专属认知表，看需求添加
#{entity_name}["_intent"] = {{}}     # _intent 意图表
#{entity_name}["_feedback"] = {{}}   # _feedback 反馈表
#{entity_name}["_language"] = {{}}   # _language 语言表
#{entity_name}["_train"] = {{}}      # _train 训练数据表

# ============================================================
# 3. Q 函数
# ============================================================
def {q_name}():
    # prompt: {entity_name} 主入口
    # reason: 从 main 指向此函数，作为脚本启动入口
    return

# ============================================================
# 4. 内存表 / 注册表
# ============================================================
_state = {{}}
_state["_{entity_name}_state"] = {{}}
_state["_[]{entity_name}_state"] = {{}}

_register = {{}}

# ============================================================
# 5. 启动
# ============================================================
if __name__ == "__main__":
    main_ref = {entity_name}.get("{entity_name}_f_main")
    if main_ref and main_ref.startswith("q:"):
        q_name = main_ref[2:]
        q_func = globals().get(q_name)
        if callable(q_func):
            q_func()
        else:
            print(f"未找到 Q 函数: {{q_name}}")
    else:
        print("未声明主入口: {entity_name}_f_main")
'''


def create_plugin(target_dir: str, entity_name: str) -> str:
    """在目标目录下创建 hoc 插件脚本，返回文件路径"""
    os.makedirs(target_dir, exist_ok=True)

    version = now_version()
    q_name = rand_q_name()
    file_name = f"{entity_name}_{version}.py"
    file_path = os.path.join(target_dir, file_name)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(build_script(entity_name, version, q_name))

    return file_path


def main():
    if len(sys.argv) == 2:
        target_dir = "."
        entity_name = sys.argv[1]
    elif len(sys.argv) == 3:
        target_dir = sys.argv[1]
        entity_name = sys.argv[2]
    else:
        print("用法: python CreatePlugin.py [目录] <实体名>")
        sys.exit(1)

    path = create_plugin(target_dir, entity_name)
    print(f"已生成: {path}")


if __name__ == "__main__":
    main()