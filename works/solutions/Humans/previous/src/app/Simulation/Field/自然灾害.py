# ./Simulation/Field/自然灾害.py

import sqlite3
import json
import sys
import random
from pathlib import Path


def simulate_natural_disaster(db_name):
    """
    模拟自然灾害对场域的影响
    
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
        
        logs.append("开始自然灾害模拟...")
        
        # 随机选择灾害类型
        disaster_types = ["洪水", "干旱", "风暴", "地震", "山火"]
        disaster = random.choice(disaster_types)
        logs.append(f"灾害类型: {disaster}")
        
        # 灾害强度
        intensity = random.uniform(0.3, 0.95)
        logs.append(f"灾害强度: {intensity:.2f}")
        
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
        
        # 检查环境相关字段
        env_fields = []
        for field, value in rows:
            if any(keyword in field for keyword in ["环境", "气候", "水位", "风力", "温度", "湿度", "地形"]):
                env_fields.append((field, value))
        
        if env_fields:
            logs.append(f"发现 {len(env_fields)} 个环境相关字段")
            
            for field, value in env_fields:
                try:
                    data = json.loads(value)
                    if isinstance(data, dict):
                        modified = False
                        
                        # 根据灾害类型修改环境参数
                        if disaster == "洪水" and "水位" in data:
                            original = data["水位"]
                            data["水位"] = original * (1 + intensity * 0.5)
                            logs.append(f"{field}: 水位 {original:.1f} → {data['水位']:.1f}")
                            modified = True
                        
                        if disaster == "干旱" and "湿度" in data:
                            original = data["湿度"]
                            data["湿度"] = max(0, original * (1 - intensity * 0.6))
                            logs.append(f"{field}: 湿度 {original:.1f}% → {data['湿度']:.1f}%")
                            modified = True
                        
                        if disaster == "风暴" and "风力" in data:
                            original = data["风力"]
                            data["风力"] = original * (1 + intensity * 0.8)
                            logs.append(f"{field}: 风力 {original:.1f} → {data['风力']:.1f}")
                            modified = True
                        
                        if disaster == "地震" and "地形" in data:
                            data["地形"] = f"{data.get('地形', '')}_震后"
                            logs.append(f"{field}: 地形已标记为震后状态")
                            modified = True
                        
                        if disaster == "山火" and "植被" in data:
                            original = data.get("植被", 100)
                            data["植被"] = max(0, original * (1 - intensity * 0.7))
                            logs.append(f"{field}: 植被覆盖率 {original:.1f}% → {data['植被']:.1f}%")
                            modified = True
                        
                        # 记录灾害影响
                        if modified:
                            data["灾害类型"] = disaster
                            data["灾害强度"] = intensity
                            cursor.execute(
                                "UPDATE 状态 SET 值=? WHERE 字段名=?",
                                (json.dumps(data, ensure_ascii=False), field)
                            )
                except:
                    pass
        
        # 新增灾害记录
        import time
        timestamp = int(time.time())
        cursor.execute(
            "INSERT INTO 经历 (tick, 事件类型, 描述) VALUES (?, ?, ?)",
            (timestamp, disaster, f"{disaster}发生，强度{intensity:.2f}")
        )
        logs.append(f"灾害事件已记录: {disaster}")
        
        # 计算影响结果
        impact_level = "低"
        if intensity > 0.7:
            impact_level = "严重"
        elif intensity > 0.4:
            impact_level = "中度"
        
        logs.append(f"灾害影响等级: {impact_level}")
        logs.append("自然灾害模拟完成")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"{disaster}模拟完成，影响等级: {impact_level}",
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
    # 命令行调用: python 自然灾害.py <db_name>
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "用法: python 自然灾害.py <db_name>",
            "logs": []
        }, ensure_ascii=False))
        sys.exit(1)
    
    db_name = sys.argv[1]
    result = simulate_natural_disaster(db_name)
    print(json.dumps(result, ensure_ascii=False))