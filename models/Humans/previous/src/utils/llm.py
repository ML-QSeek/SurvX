"""
llm.py - DeepSeek 大模型调用封装
用于 QSeek-Robinson 的反思归纳和目标评估
支持 JSON Mode 和多轮交互
"""

import json
import os
from datetime import datetime
from openai import OpenAI
from config import (
    LLM_MODEL,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE
)

# 确保 logs 目录存在
LOGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)


def _log_llm_call(call_type: str, messages: list, response: str, duration: float = 0):
    """记录大模型调用日志"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:17]
    filename = f"{call_type}_{timestamp}.json"
    filepath = os.path.join(LOGS_DIR, filename)
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "call_type": call_type,
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
        "duration_seconds": duration,
        "messages": [
            {k: v for k, v in msg.items() if k in ["role", "content"]}
            for msg in messages
        ],
        "response": response
    }
    
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  ⚠ 日志写入失败: {e}")


def chat(messages, temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_TOKENS):
    """普通调用，返回文本"""
    start = datetime.now()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False
    )
    duration = (datetime.now() - start).total_seconds()
    content = response.choices[0].message.content
    
    _log_llm_call("chat", messages, content, duration)
    print(f"  [LLM] chat 调用完成，耗时 {duration:.2f}s，返回 {len(content)} 字符")
    
    return content


def chat_json(messages, temperature=LLM_TEMPERATURE, max_tokens=LLM_MAX_TOKENS):
    """JSON Mode 调用，返回解析后的 dict"""
    start = datetime.now()
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
        response_format={"type": "json_object"}
    )
    duration = (datetime.now() - start).total_seconds()
    content = response.choices[0].message.content
    
    _log_llm_call("chat_json", messages, content, duration)
    
    try:
        result = json.loads(content)
        print(f"  [LLM] chat_json 调用完成，耗时 {duration:.2f}s，返回 {len(result)} 个键")
    except json.JSONDecodeError:
        print(f"  [LLM] chat_json 调用完成，耗时 {duration:.2f}s，但返回不是有效JSON")
        raise
    
    return result


# ============================================================
# 反思模块
# ============================================================

REFLECTION_SYSTEM_PROMPT = """你是 QSeek 框架中鲁滨逊的反思系统。分析Agent近期的经历和状态变化，发现行为模式，提出约束调整建议。

你可以主动要求查阅以下数据（每次请求只指定一种）：
- "查看第X天的详细经历"
- "查看近N天[饥饿度/口渴度/体力/健康度]的变化曲线"
- "查看[某个实体]的相关关系"
- "对比第X天和第Y天的状态差异"
- "查看当前约束层所有约束"
- "查看近N天的所有经历摘要"

当你认为分析足够充分时，输出JSON：

{
    "action": "done",
    "patterns_found": [
        {
            "pattern": "模式描述",
            "evidence": "支撑这个模式的具体经历",
            "confidence": 0.8
        }
    ],
    "new_constraints": [
        {
            "name": "约束名称",
            "condition": "触发条件",
            "consequence": "违反后果或执行动作",
            "priority": "hard 或 soft"
        }
    ],
    "constraint_adjustments": [
        {
            "name": "现有约束名称",
            "adjustment": "修改内容",
            "reason": "修改原因"
        }
    ]
}

如果没有值得注意的模式，patterns_found 为空数组。

注意：只输出客观分析，不要建议具体行动。约束是Agent内部的行为规则。"""


def reflect_on_day(agent_state_summary, data_query_fn, max_rounds=3):
    """
    多轮反思：大模型主动提问、查阅数据、归纳模式。
    """
    messages = [
        {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"以下是Agent当前状态摘要：\n\n{agent_state_summary}\n\n"
                "请开始分析。如需查看更多数据来辅助判断，请明确告诉我你需要什么。"
            )
        }
    ]
    
    for round_num in range(max_rounds):
        print(f"  [反思] 第{round_num+1}轮...")
        response = chat(messages)
        
        try:
            result = json.loads(response)
            if result.get("action") == "done":
                result["rounds_used"] = round_num + 1
                print(f"  [反思] 完成，共{round_num+1}轮，发现{len(result.get('patterns_found', []))}个模式")
                return result
        except json.JSONDecodeError:
            pass
        
        messages.append({"role": "assistant", "content": response})
        requested_data = data_query_fn(response)
        print(f"  [反思] 查询数据: {response[:80]}...")
        messages.append({
            "role": "user",
            "content": f"以下是你要的数据：\n\n{requested_data}\n\n请继续分析。"
        })
    
    messages.append({
        "role": "user",
        "content": "已达到最大反思轮数，请基于现有信息输出最终分析结论。"
    })
    
    try:
        result = chat_json(messages)
        result["rounds_used"] = max_rounds
        print(f"  [反思] 强制完成（达到最大轮数）")
        return result
    except (json.JSONDecodeError, Exception):
        print(f"  [反思] 失败，返回空结果")
        return {
            "patterns_found": [],
            "new_constraints": [],
            "constraint_adjustments": [],
            "rounds_used": max_rounds
        }


# ============================================================
# 目标评估模块
# ============================================================

GOAL_EVALUATION_SYSTEM_PROMPT = """你是 QSeek 框架中鲁滨逊的目标评估系统。评估Agent当前的生存阶段，判断目标层权重是否需要调整。

Agent的目标层包含多个目标，每个目标有权重（0-1），相对大小决定优先级。

生存阶段定义：
- 求生阶段：基本生存受到威胁，饥饿/口渴/健康任一项处于危险水平
- 稳定阶段：基本生存有保障，开始建立日常规律
- 舒适阶段：生存无忧，有稳定的食物和水源储备，有庇护所
- 探索阶段：在舒适基础上，开始探索岛屿未知区域
- 逃离阶段：产生离开岛屿的意愿，开始为此做准备

你可以主动要求查阅以下数据：
- "查看近N天的状态变化曲线"
- "查看当前目标层完整信息"
- "查看近期经历摘要"
- "查看当前约束层"
- "对比两个时间段的状态差异"

当你认为分析足够充分时，输出JSON：

{
    "action": "done",
    "current_stage": "当前生存阶段",
    "stage_reason": "判定依据",
    "weight_adjustments": [
        {
            "goal_name": "目标名称",
            "old_weight": 0.6,
            "new_weight": 0.8,
            "reason": "调整原因"
        }
    ],
    "new_goals": [
        {
            "name": "新目标名称",
            "description": "目标描述",
            "initial_weight": 0.5,
            "reason": "新增原因"
        }
    ],
    "remove_goals": [
        {
            "name": "要移除的目标名称",
            "reason": "移除原因"
        }
    ]
}

如果没有需要调整的内容，各数组为空。只输出客观评估，不要建议具体行动。"""


def evaluate_goals(agent_state_summary, current_goals, data_query_fn, max_rounds=3):
    """
    多轮目标评估：大模型可查阅状态历史和经历。
    """
    messages = [
        {"role": "system", "content": GOAL_EVALUATION_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Agent当前状态摘要：\n{agent_state_summary}\n\n"
                f"当前目标层：\n{current_goals}\n\n"
                "请评估当前生存阶段和目标权重是否需要调整。"
                "如需查看更多数据，请明确告诉我。"
            )
        }
    ]
    
    for round_num in range(max_rounds):
        print(f"  [目标评估] 第{round_num+1}轮...")
        response = chat(messages)
        
        try:
            result = json.loads(response)
            if result.get("action") == "done":
                result["rounds_used"] = round_num + 1
                print(f"  [目标评估] 完成，当前阶段: {result.get('current_stage', '未知')}")
                return result
        except json.JSONDecodeError:
            pass
        
        messages.append({"role": "assistant", "content": response})
        requested_data = data_query_fn(response)
        print(f"  [目标评估] 查询数据: {response[:80]}...")
        messages.append({
            "role": "user",
            "content": f"以下是你要的数据：\n\n{requested_data}\n\n请继续分析。"
        })
    
    messages.append({
        "role": "user",
        "content": "已达到最大轮数，请基于现有信息输出最终评估结论。"
    })
    
    try:
        result = chat_json(messages)
        result["rounds_used"] = max_rounds
        print(f"  [目标评估] 强制完成（达到最大轮数）")
        return result
    except (json.JSONDecodeError, Exception):
        print(f"  [目标评估] 失败，返回空结果")
        return {
            "current_stage": "未知",
            "stage_reason": "评估失败",
            "weight_adjustments": [],
            "new_goals": [],
            "remove_goals": [],
            "rounds_used": max_rounds
        }


# ============================================================
# 后果模拟模块
# ============================================================

CONSEQUENCE_SYSTEM_PROMPT = """你是 QSeek 框架中平行宇宙的规则接口。鲁滨逊是一个7岁男孩，流落在南太平洋荒岛。

你的职责：根据Agent当前状态和行动，模拟这个行动在固化的世界规则下会产生什么后果。
只给客观后果，不给建议。不告诉Agent该做什么。

输出JSON格式：
{
    "result_description": "行动结果的客观描述，1-2句话，用中文",
    "direct_changes": [
        {"variable": "hunger", "change": -25},
        {"variable": "energy", "change": -5}
    ],
    "new_relations": [
        {
            "subject": "椰子",
            "relation_type": "可食用",
            "object": "鲁滨逊",
            "source": "观测所得",
            "trust_score": 1.0,
            "verify_status": "已确认"
        }
    ],
    "new_cognitions": [
        {
            "entity_name": "掉落椰子",
            "entity_type": "食物",
            "completeness": "部分观测",
            "f_features": {"味道": "甜", "可食用部分": "椰汁和椰肉"},
            "o_constraints": ["需砸开硬壳"]
        }
    ]
}

关键规则：
1. direct_changes 中的 variable 必须从以下列表中选择：hunger, thirst, energy, health, fear, curiosity
2. 变化值可正可负：正=增加/恢复，负=减少/消耗
3. 所有变化范围在-100到+100之间
4. 如果行动失败或危险，相应添加负面后果
5. new_relations 和 new_cognitions 只有行动带来新发现时才非空
6. 不给建议，不评价Agent的选择好坏
"""


def simulate_consequence(scene: str, action: str, entity: str,
                         action_type: str, agent_state: dict) -> dict:
    """
    模拟行动后果。
    """
    state_summary = (
        f"鲁滨逊当前状态：饥饿度{agent_state.get('hunger', 60):.0f}，"
        f"口渴度{agent_state.get('thirst', 60):.0f}，"
        f"体力{agent_state.get('energy', 70):.0f}，"
        f"健康度{agent_state.get('health', 100):.0f}，"
        f"恐惧度{agent_state.get('fear', 40):.0f}，"
        f"位置{agent_state.get('position', '海滩')}。"
    )

    messages = [
        {"role": "system", "content": CONSEQUENCE_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"{state_summary}\n"
            f"场景：{scene}\n"
            f"行动：{action}\n"
            f"实体：{entity}\n"
            f"行动类型：{action_type}\n\n"
            "请模拟这个行动的后果。"
        )}
    ]

    try:
        print(f"  [LLM] 模拟后果: {action} {entity}")
        result = chat_json(messages)
        changes = result.get("direct_changes", [])
        if changes:
            changes_str = ", ".join(f"{c['variable']}:{c['change']:+.0f}" for c in changes)
            print(f"  [LLM] 后果: {changes_str}")
        return result
    except (json.JSONDecodeError, Exception) as e:
        print(f"  [LLM] 后果模拟失败: {e}")
        return {
            "result_description": f"执行了{action}，没有明显的效果。",
            "direct_changes": [],
            "new_relations": [],
            "new_cognitions": []
        }