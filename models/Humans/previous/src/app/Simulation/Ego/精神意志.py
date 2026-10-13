# ./Simulation/Ego/精神意志.py

import sqlite3
import json
import sys
import random
from pathlib import Path


def simulate_mental_will(db_name):
    """
    模拟精神意志对 Ego 的影响
    
    Args:
        db_name: 数据库文件名 (如 "ego_鲁滨逊.db")
    
    Returns:
        dict: {
            "success": bool,
            "message": str,
            "logs": [str]
        }
    """
    db_path = Path("../data/s_ego") / db_name
    
    if not db_path.exists():
        return {
            "success": False,
            "message": f"数据库文件不存在: {db_name}",
            "logs": []
        }
    
    logs = []
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        logs.append("开始精神意志模拟...")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='状态'")
        if not cursor.fetchone():
            logs.append("状态表不存在，模拟终止")
            conn.close()
            return {
                "success": False,
                "message": "状态表不存在",
                "logs": logs
            }
        
        # 获取当前状态
        cursor.execute("SELECT 字段名, 值 FROM 状态")
        rows = cursor.fetchall()
        logs.append(f"当前状态: {len(rows)} 个字段")
        
        # 检查精神相关字段
        mental_fields = []
        for field, value in rows:
            if any(keyword in field for keyword in ["精神", "意志", "情绪", "专注", "信念", "希望"]):
                mental_fields.append((field, value))
        
        if mental_fields:
            logs.append(f"发现 {len(mental_fields)} 个精神相关字段")
            
            for field, value in mental_fields:
                try:
                    data = json.loads(value)
                    if isinstance(data, dict):
                        modified = False
                        
                        # 模拟情绪波动
                        if "情绪" in data and isinstance(data["情绪"], (int, float)):
                            change = random.uniform(-0.08, 0.08)
                            original = data["情绪"]
                            data["情绪"] = max(0, min(100, round(original * (1 + change), 1)))
                            logs.append(f"{field}.情绪: {original:.1f} → {data['情绪']:.1f}")
                            modified = True
                        
                        # 模拟意志力变化
                        if "意志" in data and isinstance(data["意志"], (int, float)):
                            will_change = random.uniform(-0.04, 0.06)
                            original = data["意志"]
                            data["意志"] = max(0, min(100, round(original * (1 + will_change), 1)))
                            logs.append(f"{field}.意志: {original:.1f} → {data['意志']:.1f}")
                            modified = True
                        
                        # 模拟专注力
                        if "专注" in data and isinstance(data["专注"], (int, float)):
                            focus_change = random.uniform(-0.05, 0.05)
                            original = data["专注"]
                            data["专注"] = max(0, min(100, round(original * (1 + focus_change), 1)))
                            logs.append(f"{field}.专注: {original:.1f} → {data['专注']:.1f}")
                            modified = True
                        
                        # 模拟信念/希望
                        if "信念" in data and isinstance(data["信念"], (int, float)):
                            belief_change = random.uniform(-0.02, 0.04)
                            original = data["信念"]
                            data["信念"] = max(0, min(100, round(original * (1 + belief_change), 1)))
                            logs.append(f"{field}.信念: {original:.1f} → {data['信念']:.1f}")
                            modified = True
                        if "希望" in data and isinstance(data["希望"], (int, float)):
                            hope_change = random.uniform(-0.02, 0.04)
                            original = data["希望"]
                            data["希望"] = max(0, min(100, round(original * (1 + hope_change), 1)))
                            logs.append(f"{field}.希望: {original:.1f} → {data['希望']:.1f}")
                            modified = True
                        
                        if modified:
                            cursor.execute(
                                "UPDATE 状态 SET 值=? WHERE 字段名=?",
                                (json.dumps(data, ensure_ascii=False), field)
                            )
                except:
                    pass
        
        # 模拟精神事件
        import time
        timestamp = int(time.time())
        event_types = ["情绪稳定", "意志坚定", "专注力提升", "轻度焦虑", "希望增强"]
        event = random.choice(event_types)
        
        cursor.execute(
            "INSERT INTO 经历 (tick, 事件类型, 描述) VALUES (?, ?, ?)",
            (timestamp, "精神意志", f"{event} - 精神状态变化")
        )
        logs.append(f"精神事件已记录: {event}")
        
        # 计算综合状态
        overall = "稳定"
        mental_score = 75 + random.randint(-15, 20)
        if mental_score > 85:
            overall = "坚定"
        elif mental_score < 60:
            overall = "波动"
        
        logs.append(f"精神综合状态: {overall} (精神评分: {mental_score})")
        logs.append("精神意志模拟完成")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"精神意志模拟完成，状态: {overall}",
            "logs": logs
        }
        
    except sqlite3.Error as e:
        return {
            "success": False,
            "message": f"数据库错误: {str(e)}",
            "logs": logs
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"模拟失败: {str(e)}",
            "logs": logs
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "用法: python 精神意志.py <db_name>",
            "logs": []
        }, ensure_ascii=False))
        sys.exit(1)
    
    db_name = sys.argv[1]
    result = simulate_mental_will(db_name)
    print(json.dumps(result, ensure_ascii=False))