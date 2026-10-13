import sqlite3
import os
import sys
import json

def create_field_db(db_path, db_name):
    """创建 field 类型数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 状态 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 结构 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 约束 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 参数 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            函数名 TEXT,
            模型参数 TEXT,
            先验参数 TEXT,
            学习率 REAL DEFAULT 0.01,
            样本数 INTEGER DEFAULT 0,
            版本 INTEGER DEFAULT 0,
            最后更新tick INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 关系 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
        
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 空间注册 (
            id TEXT PRIMARY KEY,
            实体类型 TEXT,
            名称 TEXT,
            图标 TEXT,
            颜色 TEXT,
            坐标_x REAL,
            坐标_y REAL,
            坐标_z REAL DEFAULT 0,
            几何点集 TEXT,
            tick INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 经历 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            事件类型 TEXT,
            描述 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 序列 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def create_ego_db(db_path, db_name):
    """创建 ego 类型数据库"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 状态 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 结构 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 约束 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 模型库 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            函数名 TEXT,
            tick INTEGER,
            模型参数 TEXT,
            先验参数 TEXT,
            学习率 REAL DEFAULT 0.01,
            样本数 INTEGER DEFAULT 0,
            版本 INTEGER DEFAULT 0,
            最后更新tick INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 关系 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 语言模型 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            模型参数 TEXT,
            词表 TEXT,
            维度 INTEGER,
            样本数 INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 经历 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            事件类型 TEXT,
            描述 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 序列 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 训练数据 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            函数名 TEXT,
            tick INTEGER,
            输入值 REAL,
            输出值 REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 意图 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS 反馈 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tick INTEGER,
            字段名 TEXT,
            值 TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def create_db(db_path, db_name, db_type='field'):
    """
    创建数据库
    
    Args:
        db_path: 数据库存放路径
        db_name: 数据库文件名（如: field_荒岛.db）
        db_type: 数据库类型，'field' 或 'ego'
    
    Returns:
        dict: {'success': bool, 'message': str, 'path': str}
    """
    try:
        # 确保路径存在
        if not os.path.exists(db_path):
            os.makedirs(db_path)
        
        # 完整的数据库文件路径
        full_path = os.path.join(db_path, db_name)
        
        # 如果文件已存在
        if os.path.exists(full_path):
            return {
                'success': False,
                'message': f'数据库文件已存在: {full_path}',
                'path': full_path
            }
        
        # 根据类型创建
        if db_type == 'field':
            create_field_db(full_path, db_name)
        elif db_type == 'ego':
            create_ego_db(full_path, db_name)
        else:
            return {
                'success': False,
                'message': f'不支持的数据库类型: {db_type}，请使用 field 或 ego',
                'path': None
            }
        
        return {
            'success': True,
            'message': f'{db_type} 数据库创建成功: {db_name}',
            'path': full_path
        }
        
    except sqlite3.Error as e:
        return {
            'success': False,
            'message': f'SQLite 错误: {str(e)}',
            'path': None
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'创建失败: {str(e)}',
            'path': None
        }


# 命令行调用
if __name__ == '__main__':
    # 用法: python create_db.py <db_path> <db_name> <db_type>
    # 示例: python create_db.py ./data field_荒岛.db field
    #       python create_db.py ./data ego_鲁滨逊.db ego
    
    if len(sys.argv) < 4:
        print(json.dumps({
            'success': False,
            'message': '用法: python create_db.py <db_path> <db_name> <db_type>\ndb_type: field 或 ego'
        }, ensure_ascii=False))
        sys.exit(1)
    
    db_path = sys.argv[1]
    db_name = sys.argv[2]
    db_type = sys.argv[3]
    
    result = create_db(db_path, db_name, db_type)
    print(json.dumps(result, ensure_ascii=False))