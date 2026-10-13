"""
凭证管理器，负责用户凭证和交易配置的存储管理
"""
import sqlite3
import os
import sys
import hashlib
import base64
from cryptography.fernet import Fernet

class CredentialManager:
    """凭证管理器"""
    def __init__(self):
        """获取资源路径（兼容开发和打包环境）"""
        if hasattr(sys, '_MEIPASS'):  # 打包后的环境
            base_path = sys._MEIPASS
        else:  # 开发环境
            base_path = os.path.abspath("../../")
        # 在当前目录下创建数据子目录
        data_dir = os.path.join(base_path, "data")
        
        # 数据库文件路径
        self.db_path = os.path.join(data_dir, "q_invest_credentials.db")
        # 密钥文件路径
        self.key_file = os.path.join(data_dir, ".q_invest_key.dat")
        
        self.cipher_suite = None
        
        # 初始化加密
        self._init_encryption()
        
        # 初始化数据库
        self._init_database()
    
    def _init_encryption(self):
        """初始化加密"""
        try:
            # 尝试加载现有的密钥
            if os.path.exists(self.key_file):
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # 生成新密钥
                key = Fernet.generate_key()
                with open(self.key_file, 'wb') as f:
                    f.write(key)
            
            # 设置文件权限（仅限Unix系统）
            if sys.platform != 'win32':
                os.chmod(self.key_file, 0o600)
            
            self.cipher_suite = Fernet(key)
        except Exception as e:
            print(f"加密初始化失败: {e}")
            # 使用简化的加密作为后备
            self.cipher_suite = None
    
    def _init_database(self):
        """初始化数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建凭证表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    encrypted_password TEXT,
                    remember_password INTEGER DEFAULT 0,
                    auto_login INTEGER DEFAULT 0,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 创建交易配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trading_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_name TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    api_name TEXT NOT NULL,
                    target_dir TEXT,
                    strategy_name TEXT,
                    username TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(username, config_name)
                )
            ''')
            
            # 创建索引以提高查询效率
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trading_configs_username ON trading_configs(username)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trading_configs_active ON trading_configs(username, is_active)')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"数据库初始化失败: {e}")
    
    def _simple_encrypt(self, text, key="q_invest_2023"):
        """简化的加密方法（如果Fernet不可用）"""
        # 使用base64编码进行简单混淆
        encoded = base64.b64encode(text.encode()).decode()
        return f"simple:{encoded}"
    
    def _simple_decrypt(self, text, key="q_invest_2023"):
        """简化解密方法"""
        if text.startswith("simple:"):
            encoded = text[7:]
            try:
                decoded = base64.b64decode(encoded.encode()).decode()
                return decoded
            except:
                return ""
        return text
    
    def encrypt_password(self, password):
        """加密密码"""
        if not password:
            return ""
        
        try:
            if self.cipher_suite:
                encrypted = self.cipher_suite.encrypt(password.encode())
                return encrypted.decode()
            else:
                return self._simple_encrypt(password)
        except Exception as e:
            print(f"密码加密失败: {e}")
            return password
    
    def decrypt_password(self, encrypted_password):
        """解密密码"""
        if not encrypted_password:
            return ""
        
        try:
            if self.cipher_suite and not encrypted_password.startswith("simple:"):
                decrypted = self.cipher_suite.decrypt(encrypted_password.encode())
                return decrypted.decode()
            else:
                return self._simple_decrypt(encrypted_password)
        except Exception as e:
            print(f"密码解密失败: {e}")
            return ""
    
    def save_credentials(self, username, password, remember_password=False, auto_login=False):
        """保存登录凭证"""
        try:
            encrypted_password = self.encrypt_password(password) if password else ""
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 删除旧的凭证
            cursor.execute('DELETE FROM credentials WHERE username = ?', (username,))
            
            # 插入新的凭证
            cursor.execute('''
                INSERT INTO credentials (username, encrypted_password, remember_password, auto_login, last_login)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (username, encrypted_password, 1 if remember_password else 0, 1 if auto_login else 0))
            
            conn.commit()
            conn.close()
            
            # 设置文件权限（仅限Unix系统）
            if sys.platform != 'win32':
                os.chmod(self.db_path, 0o600)
            
            return True
        except Exception as e:
            print(f"保存凭证失败: {e}")
            return False
    
    def get_credentials(self):
        """获取保存的凭证"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取最近使用的凭证
            cursor.execute('''
                SELECT username, encrypted_password, remember_password, auto_login
                FROM credentials 
                ORDER BY last_login DESC 
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                username, encrypted_password, remember_password, auto_login = row
                decrypted_password = self.decrypt_password(encrypted_password) if encrypted_password else ""
                
                return {
                    'has_saved': True,
                    'username': username,
                    'password': decrypted_password,
                    'rememberPassword': bool(remember_password),
                    'autoLogin': bool(auto_login)
                }
            else:
                return {
                    'has_saved': False,
                    'username': "",
                    'password': "",
                    'rememberPassword': False,
                    'autoLogin': False
                }
        except Exception as e:
            print(f"获取凭证失败: {e}")
            return {
                'has_saved': False,
                'username': "",
                'password': "",
                'rememberPassword': False,
                'autoLogin': False
            }
    
    def clear_credentials(self, username=None):
        """清除凭证"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if username:
                cursor.execute('DELETE FROM credentials WHERE username = ?', (username,))
            else:
                cursor.execute('DELETE FROM credentials')
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"清除凭证失败: {e}")
            return False
    
    def save_trading_config(self, username, config_name, account_name, api_name, target_dir=None, strategy_name=None):
        """保存或更新交易配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查是否已存在同名配置
            cursor.execute(
                'SELECT id FROM trading_configs WHERE username = ? AND config_name = ?',
                (username, config_name)
            )
            
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有配置
                cursor.execute('''
                    UPDATE trading_configs 
                    SET account_name = ?, api_name = ?, target_dir = ?, strategy_name = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (account_name, api_name, target_dir, strategy_name, existing[0]))
            else:
                # 插入新配置
                cursor.execute('''
                    INSERT INTO trading_configs 
                    (config_name, account_name, api_name, target_dir, strategy_name, username)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (config_name, account_name, api_name, target_dir, strategy_name, username))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "配置保存成功"}
        except Exception as e:
            print(f"保存交易配置失败: {e}")
            return {"success": False, "message": f"保存失败: {str(e)}"}
    
    def get_trading_configs(self, username):
        """获取用户的所有交易配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # 使返回字典格式
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, config_name, account_name, api_name, target_dir, strategy_name, 
                       is_active, created_at, updated_at
                FROM trading_configs 
                WHERE username = ? AND is_active = 1
                ORDER BY updated_at DESC
            ''', (username,))
            
            rows = cursor.fetchall()
            conn.close()
            
            configs = []
            for row in rows:
                configs.append({
                    'id': row['id'],
                    'config_name': row['config_name'],
                    'account_name': row['account_name'],
                    'api_name': row['api_name'],
                    'target_dir': row['target_dir'],
                    'strategy_name': row['strategy_name'],
                    'is_active': bool(row['is_active']),
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                })
            
            return {
                "success": True,
                "configs": configs,
                "count": len(configs)
            }
        except Exception as e:
            print(f"获取交易配置失败: {e}")
            return {
                "success": False,
                "message": f"获取配置失败: {str(e)}",
                "configs": [],
                "count": 0
            }
    
    def get_trading_config_by_name(self, username, config_name):
        """根据配置名称获取特定配置"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, config_name, account_name, api_name, target_dir, strategy_name, 
                       is_active, created_at, updated_at
                FROM trading_configs 
                WHERE username = ? AND config_name = ? AND is_active = 1
            ''', (username, config_name))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    "success": True,
                    "config": {
                        'id': row['id'],
                        'config_name': row['config_name'],
                        'account_name': row['account_name'],
                        'api_name': row['api_name'],
                        'target_dir': row['target_dir'],
                        'strategy_name': row['strategy_name'],
                        'is_active': bool(row['is_active']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "配置不存在"
                }
        except Exception as e:
            print(f"获取特定配置失败: {e}")
            return {
                "success": False,
                "message": f"获取配置失败: {str(e)}"
            }
    
    def update_trading_config(self, config_id, **kwargs):
        """更新交易配置（部分字段）"""
        try:
            allowed_fields = ['config_name', 'account_name', 'api_name', 'target_dir', 'strategy_name']
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in allowed_fields and value is not None:
                    update_fields.append(f"{key} = ?")
                    values.append(value)
            
            if not update_fields:
                return {"success": False, "message": "没有可更新的字段"}
            
            values.append(config_id)
            update_sql = f'''
                UPDATE trading_configs 
                SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            '''
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(update_sql, values)
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return {"success": True, "message": "配置更新成功"}
            else:
                conn.close()
                return {"success": False, "message": "配置不存在"}
                
        except sqlite3.IntegrityError:
            return {"success": False, "message": "配置名称已存在"}
        except Exception as e:
            print(f"更新配置失败: {e}")
            return {"success": False, "message": f"更新失败: {str(e)}"}
    
    def delete_trading_config(self, username, config_name=None, config_id=None):
        """删除交易配置（软删除）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if config_id:
                cursor.execute(
                    'UPDATE trading_configs SET is_active = 0 WHERE id = ? AND username = ?',
                    (config_id, username)
                )
            elif config_name:
                cursor.execute(
                    'UPDATE trading_configs SET is_active = 0 WHERE config_name = ? AND username = ?',
                    (config_name, username)
                )
            else:
                conn.close()
                return {"success": False, "message": "请指定配置ID或名称"}
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return {"success": True, "message": "配置删除成功"}
            else:
                conn.close()
                return {"success": False, "message": "配置不存在"}
                
        except Exception as e:
            print(f"删除配置失败: {e}")
            return {"success": False, "message": f"删除失败: {str(e)}"}
    
    def hard_delete_trading_config(self, username, config_id):
        """永久删除交易配置（谨慎使用）"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'DELETE FROM trading_configs WHERE id = ? AND username = ?',
                (config_id, username)
            )
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return {"success": True, "message": "配置永久删除成功"}
            else:
                conn.close()
                return {"success": False, "message": "配置不存在"}
                
        except Exception as e:
            print(f"永久删除配置失败: {e}")
            return {"success": False, "message": f"删除失败: {str(e)}"}
    
    def get_active_config_count(self, username):
        """获取用户的有效配置数量"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT COUNT(*) FROM trading_configs WHERE username = ? AND is_active = 1',
                (username,)
            )
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
        except Exception as e:
            print(f"获取配置数量失败: {e}")
            return 0