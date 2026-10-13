# ./Simulation/Field/生物入侵.py

import sqlite3
import json
import sys
import random
from pathlib import Path


def simulate_biological_invasion(db_name):
    """
    模拟生物入侵对场域的影响
    
    Args:
        db_name: 数据库文件名 (如 "field_创世.db")
    
    Returns:
        dict: {
            "success": bool,
            "message": str,
            "logs": [str]  # 模拟过程日志
        }
    """
    db_path = Path("../data/s_field") / db_name
    
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
        
        logs.append("开始生物入侵模拟...")
        
        # 检查是否有状态表
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
        
        # 模拟入侵参数
        invasion_strength = random.uniform(0.3, 0.9)
        invasion_speed = random.uniform(0.1, 0.5)
        
        logs.append(f"入侵种强度: {invasion_strength:.2f}")
        logs.append(f"入侵扩散速度: {invasion_speed:.2f}")
        
        # 检查是否有现有物种数据
        cursor.execute("SELECT 字段名, 值 FROM 状态 WHERE 字段名 LIKE '%物种%' OR 字段名 LIKE '%生物%'")
        species_rows = cursor.fetchall()
        
        if species_rows:
            logs.append(f"发现 {len(species_rows)} 个生物相关字段")
            for field, value in species_rows:
                try:
                    data = json.loads(value)
                    if isinstance(data, dict):
                        # 模拟物种数量变化
                        if '数量' in data:
                            original = data['数量']
                            new_count = max(0, original * (1 - invasion_speed * 0.3))
                            data['数量'] = new_count
                            data['入侵影响'] = invasion_strength
                            data['入侵状态'] = '入侵中'
                            logs.append(f"更新 {field}: {original} → {new_count:.1f}")
                            
                            # 更新数据库
                            cursor.execute(
                                "UPDATE 状态 SET 值=? WHERE 字段名=?",
                                (json.dumps(data, ensure_ascii=False), field)
                            )
                except:
                    pass
        
        # 添加入侵记录
        import time
        timestamp = int(time.time())
        cursor.execute(
            "INSERT INTO 状态 (tick, 字段名, 值) VALUES (?, ?, ?)",
            (timestamp, "生物入侵_入侵强度", json.dumps({"强度": invasion_strength, "速度": invasion_speed}))
        )
        logs.append("入侵参数已记录到状态表")
        
        # 模拟结果
        impact_level = "低"
        if invasion_strength > 0.7:
            impact_level = "高"
        elif invasion_strength > 0.4:
            impact_level = "中"
        
        logs.append(f"入侵影响等级: {impact_level}")
        logs.append("生物入侵模拟完成")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"生物入侵模拟完成，影响等级: {impact_level}",
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
    # 命令行调用: python 生物入侵.py <db_name>
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "用法: python 生物入侵.py <db_name>",
            "logs": []
        }, ensure_ascii=False))
        sys.exit(1)
    
    db_name = sys.argv[1]
    result = simulate_biological_invasion(db_name)
    print(json.dumps(result, ensure_ascii=False))