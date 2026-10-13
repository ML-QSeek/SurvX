# ./Deduction/Ego.py

import sqlite3
import sys
import json
from pathlib import Path


def validate_ego(db_name):
    """
    对指定 Ego 数据库执行推演检查
    
    Args:
        db_name: 数据库文件名 (如 "ego_鲁滨逊.db")
    
    Returns:
        dict: {
            "success": bool,
            "message": str,
            "issues": [
                {"l": "e"|"w"|"i", "m": str, "loc": str}
            ]
        }
    """
    db_path = Path("../data/s_ego") / db_name
    
    if not db_path.exists():
        return {
            "success": False,
            "message": f"数据库文件不存在: {db_name}",
            "issues": []
        }
    
    issues = []
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 1. 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            issues.append({
                "l": "w",
                "m": "数据库中没有表",
                "loc": "整体"
            })
        
        # 2. 模拟检查：遍历每个表
        for table in tables:
            # 检查表是否有数据
            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cursor.fetchone()[0]
            
            if count == 0:
                issues.append({
                    "l": "i",
                    "m": f"表 '{table}' 为空",
                    "loc": table
                })
            else:
                issues.append({
                    "l": "i",
                    "m": f"表 '{table}' 有 {count} 条记录",
                    "loc": table
                })
                
                # 检查是否有 id 列
                cursor.execute(f"PRAGMA table_info([{table}])")
                columns = [col[1] for col in cursor.fetchall()]
                if 'id' not in columns:
                    issues.append({
                        "l": "w",
                        "m": f"表 '{table}' 没有 id 列，建议添加",
                        "loc": table
                    })
        
        # 3. Ego 特定检查
        if '状态' in tables:
            cursor.execute("SELECT COUNT(*) FROM 状态")
            count = cursor.fetchone()[0]
            if count == 0:
                issues.append({
                    "l": "w",
                    "m": "状态表为空，Ego 初始状态未配置",
                    "loc": "状态"
                })
        
        if '结构' in tables:
            cursor.execute("SELECT COUNT(*) FROM 结构")
            count = cursor.fetchone()[0]
            if count == 0:
                issues.append({
                    "l": "w",
                    "m": "结构表为空，Ego 身体结构未定义",
                    "loc": "结构"
                })
        
        if '约束' in tables:
            cursor.execute("SELECT COUNT(*) FROM 约束")
            count = cursor.fetchone()[0]
            if count == 0:
                issues.append({
                    "l": "i",
                    "m": "约束表为空，Ego 可能没有行为限制",
                    "loc": "约束"
                })
        
        if '模型库' in tables:
            cursor.execute("SELECT COUNT(*) FROM 模型库")
            count = cursor.fetchone()[0]
            if count == 0:
                issues.append({
                    "l": "i",
                    "m": "模型库为空，Ego 可能没有可用模型",
                    "loc": "模型库"
                })
        
        conn.close()
        
        if len(issues) == 0:
            issues.append({
                "l": "i",
                "m": "✅ 所有检查通过",
                "loc": "整体"
            })
        
        return {
            "success": True,
            "message": f"Ego 推演完成，发现 {len(issues)} 个问题",
            "issues": issues
        }
        
    except sqlite3.Error as e:
        return {
            "success": False,
            "message": f"数据库错误: {str(e)}",
            "issues": []
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"推演失败: {str(e)}",
            "issues": []
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "message": "用法: python Ego.py <db_name>",
            "issues": []
        }, ensure_ascii=False))
        sys.exit(1)
    
    db_name = sys.argv[1]
    result = validate_ego(db_name)
    print(json.dumps(result, ensure_ascii=False))