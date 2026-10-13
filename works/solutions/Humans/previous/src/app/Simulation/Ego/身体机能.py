# ./Simulation/Ego/身体机能.py

import sqlite3
import json
import sys
import random
from pathlib import Path


def simulate_body_function(db_name):
    """
    模拟身体机能对 Ego 的影响
    
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
        
        logs.append("开始身体机能模拟...")
        
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
        
        # 检查身体相关字段
        body_fields = []
        for field, value in rows:
            if any(keyword in field for keyword in ["体力", "身体", "耐力", "力量", "速度", "健康"]):
                body_fields.append((field, value))
        
        if body_fields:
            logs.append(f"发现 {len(body_fields)} 个身体相关字段")
            
            for field, value in body_fields:
                try:
                    data = json.loads(value)
                    if isinstance(data, dict):
                        modified = False
                        
                        # 模拟体力变化
                        if "体力" in data or "耐力" in data or "力量" in data:
                            # 随机变化 -5% ~ +5%
                            change = random.uniform(-0.05, 0.05)
                            for key in ["体力", "耐力", "力量"]:
                                if key in data and isinstance(data[key], (int, float)):
                                    original = data[key]
                                    data[key] = max(0, round(original * (1 + change), 1))
                                    logs.append(f"{field}.{key}: {original:.1f} → {data[key]:.1f}")
                                    modified = True
                        
                        # 模拟健康状态
                        if "健康" in data and isinstance(data["健康"], (int, float)):
                            health_change = random.uniform(-0.03, 0.02)
                            original = data["健康"]
                            data["健康"] = max(0, min(100, round(original * (1 + health_change), 1)))
                            logs.append(f"{field}.健康: {original:.1f} → {data['健康']:.1f}")
                            modified = True
                        
                        if modified:
                            cursor.execute(
                                "UPDATE 状态 SET 值=? WHERE 字段名=?",
                                (json.dumps(data, ensure_ascii=False), field)
                            )
                except:
                    pass
        
        # 模拟身体事件
        import time
        timestamp = int(time.time())
        event_types = ["体力恢复", "疲劳积累", "状态良好", "轻微疲劳"]
        event = random.choice(event_types)
        
        cursor.execute(
            "INSERT INTO 经历 (tick, 事件类型, 描述) VALUES (?, ?, ?)",
            (timestamp, "身体机能", f"{event} - 身体状态变化")
        )
        logs.append(f"身体事件已记录: {event}")
        
        # 计算综合状态
        overall = "正常"
        health_score = 80 + random.randint(-10, 10)
        if health_score > 85:
            overall = "良好"
        elif health_score < 65:
            overall = "疲劳"
        
        logs.append(f"身体综合状态: {overall} (健康评分: {health_score})")
        logs.append("身体机能模拟完成")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"身体机能模拟完成，状态: {overall}",
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
            "message": "用法: python 身体机能.py <db_name>",
            "logs": []
        }, ensure_ascii=False))
        sys.exit(1)
    
    db_name = sys.argv[1]
    result = simulate_body_function(db_name)
    print(json.dumps(result, ensure_ascii=False))