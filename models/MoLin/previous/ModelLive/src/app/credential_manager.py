import os
import sys
import sqlite3
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