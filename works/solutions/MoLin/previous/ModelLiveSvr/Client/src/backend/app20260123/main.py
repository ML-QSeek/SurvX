import webview
import json
import threading
import time
import requests
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import sys
import os
import socket
import urllib.request
import urllib.error
from urllib.parse import urlparse
import sqlite3
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime
from updater import ClientUpdater

class Api:
    def __init__(self):
        self._window_manager = None
    
    def set_window_manager(self, manager):
        """设置WindowManager引用"""
        self._window_manager = manager
    
    def get_window(self):
        """安全获取窗口对象"""
        try:
            if self._window_manager and hasattr(self._window_manager, 'window'):
                return self._window_manager.window
            
            if webview.windows:
                return webview.windows[0]
            
            return None
        except Exception as e:
            print(f"获取窗口失败: {e}")
            return None
    
    def minimize_window(self):
        """最小化窗口"""
        window = self.get_window()
        if window:
            try:
                window.minimize()
            except Exception as e:
                print(f"最小化窗口失败: {e}")
    
    def maximize_window(self):
        """最大化窗口"""
        window = self.get_window()
        if window:
            try:
                window.maximize()
            except Exception as e:
                print(f"最大化窗口失败: {e}")
    
    def restore_window(self):
        """恢复窗口"""
        window = self.get_window()
        if window:
            try:
                window.restore()
            except Exception as e:
                print(f"恢复窗口失败: {e}")
    
    def close_window(self):
        """关闭窗口"""
        window = self.get_window()
        if window:
            try:
                window.destroy()
            except Exception as e:
                print(f"关闭窗口失败: {e}")
    
    def login(self, user_data):
        """处理登录请求"""
        if self._window_manager:
            return self._window_manager.handle_login(user_data)
        return {"success": False, "message": "系统错误"}
    
    def get_saved_credentials(self):
        """获取保存的登录凭证"""
        if self._window_manager:
            return self._window_manager.get_saved_credentials()
        return {"has_saved": False, "username": "", "rememberPassword": False, "autoLogin": False}
    
    def clear_saved_credentials(self):
        """清除保存的登录凭证"""
        if self._window_manager:
            return self._window_manager.clear_saved_credentials()
        return {"success": False}
    
    def load_main_page(self):
        """加载主页面（供JavaScript调用）"""
        # 直接返回简单值，避免调用窗口方法
        if self._window_manager:
            # 在新线程中执行实际的操作
            threading.Thread(target=self._window_manager.load_main_page, daemon=True).start()
            return {"success": True, "message": "正在加载主页面..."}
        return {"success": False, "message": "系统错误"}
    
    def center_window(self):
        """居中窗口（供JavaScript调用）"""
        if self._window_manager:
            threading.Thread(target=self._window_manager.center_window, daemon=True).start()
            return {"success": True, "message": "正在居中窗口..."}
        return {"success": False, "message": "系统错误"}

    def download_image(self, base64_data):
        try:
            # 解析 base64 数据
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            # 解码 base64
            image_data = base64.b64decode(base64_data)
            # 生成文件名
            filename = f"{int(datetime.now().timestamp())}.png"
            # 保存文件
            save_path = os.path.join(os.path.expanduser('~'), 'Downloads', filename)
            #print(save_path )
            safe_path = json.dumps(save_path)
            with open(save_path, 'wb') as f:
                f.write(image_data)
            # 显示成功消息
            webview.windows[0].evaluate_js(f'WarnMessage("图片已保存到：" + {safe_path})')
            return {"status": "success", "path": save_path}
        except Exception as e:
            return {"status": "error", "message": str(e)}


class ConnectionPool:
    """服务器连接池"""
    def __init__(self):
        # 定义服务器列表（按优先级排序）
        self.servers = [
            # 主服务器
            {
                'name': '主服务器',
                'url': 'http://10.10.98.51/test/sys/index.php',
                'timeout': 5,
                'priority': 1
            },
            # 备用服务器1
            {
                'name': '备用服务器1',
                'url': 'http://10.10.98.51/test/sys/index.php',
                'timeout': 5,
                'priority': 2
            },
            # 备用服务器2（本地测试服务器）
            {
                'name': '本地服务器',
                'url': 'http://10.10.98.51/test/sys/index.php',
                'timeout': 3,
                'priority': 3
            }
        ]
        
        # 当前选中的服务器
        self.current_server = None
        # 连接状态
        self.connection_status = {}
    
    def test_connection(self, server):
        """测试服务器连接"""
        try:
            # 解析URL
            parsed_url = urlparse(server['url'])
            
            # 先测试TCP连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(server['timeout'])
            
            # 获取主机名和端口
            hostname = parsed_url.hostname
            port = parsed_url.port or (80 if parsed_url.scheme == 'http' else 443)
            
            # 尝试连接
            result = sock.connect_ex((hostname, port))
            sock.close()
            
            if result == 0:
                # TCP连接成功，尝试HTTP请求
                req = urllib.request.Request(server['url'], method='HEAD')
                try:
                    response = urllib.request.urlopen(req, timeout=server['timeout'])
                    if response.status < 400:
                        return True
                except:
                    # 即使HTTP失败，TCP连接成功也算可用
                    return True
            
            return False
        except Exception as e:
            print(f"连接测试失败 {server['name']}: {e}")
            return False
    
    def get_available_server(self):
        """获取可用的服务器"""
        # 按优先级排序
        sorted_servers = sorted(self.servers, key=lambda x: x['priority'])
        
        for server in sorted_servers:
            print(f"正在测试服务器: {server['name']} ({server['url']})")
            
            if self.test_connection(server):
                print(f"服务器 {server['name']} 连接成功")
                self.current_server = server
                self.connection_status[server['url']] = {
                    'status': 'connected',
                    'last_check': time.time()
                }
                return server
        
        print("所有服务器连接失败")
        return None
    
    def get_current_server_url(self):
        """获取当前服务器的URL"""
        if self.current_server:
            return self.current_server['url']
        return None


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


class WindowManager:
    def __init__(self):
        self.window = None
        self.user_data = None
        self.window_width = 800
        self.window_height = 480
        self.is_hidden = False
        
        # 创建连接池
        self.connection_pool = ConnectionPool()
        
        # 创建凭证管理器
        self.credential_manager = CredentialManager()
        
        # 创建Api实例
        self.api = Api()
        self.api.set_window_manager(self)
    
    def create_app(self):
        """创建应用窗口"""
        
        """获取资源路径（兼容开发和打包环境）"""
        if hasattr(sys, '_MEIPASS'):  # 打包后的环境
            base_path = sys._MEIPASS
        else:  # 开发环境
            base_path = os.path.abspath("../../")
        # 在当前目录下创建数据子目录
        login_path = os.path.join(base_path, "src/ui/index.html")
        dash_path = os.path.join(base_path, "src/ui/main.html")
        self.dash_path = dash_path
        
        # 检查登录页面是否存在
        if not os.path.exists(login_path):
            print("错误: {login_path} 文件不存在!")
            return
        
        # 创建窗口
        self.window = webview.create_window(
            '请先登录',
            url=f'file://{login_path}',
            width=self.window_width,
            height=self.window_height,
            x=-2000,
            y=-2000,
            resizable=False,
            frameless=True,
            min_size=(800, 480),
            easy_drag=True,
            on_top=False,
            js_api=self.api
            
        )
        
        webview.start(debug=True, func=self.after_start)
    
    def after_start(self):
        """webview启动后的回调"""
        if self.window:
            threading.Timer(3, self.show_visible_window).start()
            
            # 自动测试服务器连接
            threading.Thread(target=self.test_server_connections, daemon=True).start()
    
    def test_server_connections(self):
        """测试服务器连接"""
        print("正在测试服务器连接...")
        server = self.connection_pool.get_available_server()
        if server:
            print(f"已选择服务器: {server['name']} ({server['url']})")
        else:
            print("警告：没有可用的服务器，登录后可能会无法加载主页面")
    
    def show_visible_window(self):
        """显示窗口到屏幕中央"""
        try:
            root = tk.Tk()
            root.withdraw()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            current_width = self.window_width
            current_height = self.window_height
            x = (screen_width - current_width) // 2
            y = (screen_height - current_height) // 2
            
            self.window.move(x, y)
            
            root.destroy()
            root.quit()
        except Exception as e:
            print(f"显示窗口失败: {e}")
    
    def center_window(self):
        """供JavaScript调用的居中方法"""
        try:
            root = tk.Tk()
            root.withdraw()
            
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            
            current_width = self.window_width
            current_height = self.window_height
            
            x = (screen_width - current_width) // 2
            y = (screen_height - current_height) // 2
            
            self.window.move(x, y)
            print(f"JavaScript调用：窗口已居中 ({x}, {y})")
            
            root.destroy()
            root.quit()
            return True
        except Exception as e:
            print(f"JavaScript调用居中失败: {e}")
            return False
    
    def handle_login(self, user_data):
        """处理登录请求"""
        print(f"收到登录请求: 用户名={user_data.get('username', '')}")
        
        # 验证用户数据
        success = self.validate_login(user_data)
        
        if success:
            self.user_data = user_data
            
            # 保存凭证（如果需要）
            remember_password = user_data.get('rememberPassword', False)
            auto_login = user_data.get('autoLogin', False)
            password = user_data.get('password', '')
            
            if remember_password:
                self.credential_manager.save_credentials(
                    username=user_data['username'],
                    password=password,
                    remember_password=remember_password,
                    auto_login=auto_login
                )
            elif auto_login:
                # 如果选择了自动登录但没有选择记住密码，只保存用户名和标志
                self.credential_manager.save_credentials(
                    username=user_data['username'],
                    password="",  # 不保存密码
                    remember_password=False,
                    auto_login=True
                )
            
            return {"success": True, "message": "登录成功"}
        else:
            return {"success": False, "message": "用户名或密码错误"}
    
    def validate_login(self, user_data):
        """验证用户名和密码"""
        username = user_data.get('username', '').strip()
        password = user_data.get('password', '').strip()
        
        Url = 'http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php'
        Sub_Field= {
        'sflag':'login',
        'sid':'_04',
        'username':username,
        'password':password,
        } 
        r = requests.post(Url,data = Sub_Field)
        rtext = r.text.strip()[1:]
        rtext = json.loads(rtext)
        if type(rtext)==list :
            print(rtext[0]['Q14123103']+'：登录成功！')
            return True
        return False
    
    
    def get_saved_credentials(self):
        """获取保存的登录凭证（供JavaScript调用）"""
        try:
            credentials = self.credential_manager.get_credentials()
            print(f"获取保存的凭证: {credentials.get('username', '')}")
            return credentials
        except Exception as e:
            print(f"获取保存凭证失败: {e}")
            return {
                'has_saved': False,
                'username': "",
                'password': "",
                'rememberPassword': False,
                'autoLogin': False
            }
    
    def clear_saved_credentials(self):
        """清除保存的登录凭证（供JavaScript调用）"""
        try:
            success = self.credential_manager.clear_credentials()
            return {"success": success}
        except Exception as e:
            print(f"清除保存凭证失败: {e}")
            return {"success": False}
    
    def load_main_page(self):
        username = self.user_data.get('username', '').strip()
        """加载主应用页面"""
        # 调整窗口大小
        new_width = 1800
        new_height = 900
        self.window.resize(new_width, new_height)
        
        # 获取屏幕尺寸
        root = tk.Tk()
        root.withdraw()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
        
        # 调整窗口
        self.window.move(x, y)
        
        '''
        # 更新标题
        if self.user_data:
            self.window.set_title(f'主应用 - {self.user_data["username"]}')
        else:
            self.window.set_title('主应用')
        '''
        
        # 更新存储的窗口尺寸
        self.window_width = new_width
        self.window_height = new_height
        
        # 获取可用的服务器URL
        #server_url = self.connection_pool.get_current_server_url()
        server_url = self.dash_path    
        
        # 加载主页面
        print(f"正在加载主页面: {server_url}")
        self.window.load_url(server_url+'?par='+username)
        root.destroy()
        root.quit()


def restart_application():
    """重启当前应用"""
    python = sys.executable
    os.execl(python, python, *sys.argv)


if __name__ == '__main__':
    # 设置DPI感知（Windows）
    if sys.platform == 'win32':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    # 第一步：先检查更新（在创建窗口之前）
    try:
        updater = ClientUpdater("http://10.10.98.51/update", "../../")
        
        if updater.check_for_updates():
            # 显示正在更新的对话框（只有一个，置顶显示）
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            
            # 询问是否自动更新
            result = messagebox.askyesno(
                "发现新版本",
                "检测到新版本可用，是否立即自动更新？\n\n"
                "点击'是'：自动下载更新并重启\n"
                "点击'否'：跳过更新，直接启动应用",
                parent=root
            )
            
            if result:
                # 显示更新进度对话框
                update_window = tk.Toplevel(root)
                update_window.title("正在更新")
                update_window.attributes('-topmost', True)
                
                # 设置窗口大小和位置
                update_window.geometry("400x150")
                screen_width = update_window.winfo_screenwidth()
                screen_height = update_window.winfo_screenheight()
                x = (screen_width - 400) // 2
                y = (screen_height - 150) // 2
                update_window.geometry(f"400x150+{x}+{y}")
                
                # 禁止调整大小和关闭
                update_window.resizable(False, False)
                update_window.protocol("WM_DELETE_WINDOW", lambda: None)  # 禁用关闭按钮
                
                # 添加更新提示
                tk.Label(
                    update_window,
                    text="正在更新应用，请稍候...",
                    font=("微软雅黑", 12)
                ).pack(pady=20)
                
                # 添加进度条
                progress_bar = ttk.Progressbar(
                    update_window,
                    mode='indeterminate',
                    length=300
                )
                progress_bar.pack(pady=10)
                progress_bar.start()  # 开始动画
                
                update_window.update()
                
                # 执行更新操作
                def perform_update():
                    try:
                        print("开始自动下载更新...")
                        success = updater.perform_update()
                        
                        if success:
                            # 更新成功
                            progress_bar.stop()
                            
                            # 更新提示文本
                            for widget in update_window.winfo_children():
                                widget.destroy()
                            
                            tk.Label(
                                update_window,
                                text="✅ 更新完成！\n应用即将重启...",
                                font=("微软雅黑", 12),
                                justify="center"
                            ).pack(expand=True, fill="both", padx=20, pady=40)
                            
                            update_window.update()
                            time.sleep(2)  # 显示2秒完成提示
                            
                            # 关闭所有窗口
                            update_window.destroy()
                            root.destroy()
                            
                            # 重启应用
                            print("更新完成，正在重启应用...")
                            restart_application()
                            sys.exit(0)
                        else:
                            # 更新失败
                            progress_bar.stop()
                            
                            for widget in update_window.winfo_children():
                                widget.destroy()
                            
                            tk.Label(
                                update_window,
                                text="❌ 更新失败！\n将使用当前版本启动应用",
                                font=("微软雅黑", 12),
                                justify="center",
                                fg="red"
                            ).pack(expand=True, fill="both", padx=20, pady=40)
                            
                            tk.Button(
                                update_window,
                                text="确定",
                                command=lambda: [update_window.destroy(), root.destroy()],
                                width=10
                            ).pack(pady=10)
                            
                            update_window.update()
                            print("更新失败，继续启动应用")
                            
                    except Exception as e:
                        print(f"更新过程中出错: {e}")
                        
                        # 显示错误提示
                        progress_bar.stop()
                        
                        for widget in update_window.winfo_children():
                            widget.destroy()
                        
                        tk.Label(
                            update_window,
                            text=f"更新错误：{str(e)[:50]}\n将使用当前版本启动应用",
                            font=("微软雅黑", 11),
                            justify="center",
                            fg="red",
                            wraplength=350
                        ).pack(expand=True, fill="both", padx=20, pady=20)
                        
                        tk.Button(
                            update_window,
                            text="确定",
                            command=lambda: [update_window.destroy(), root.destroy()],
                            width=10
                        ).pack(pady=10)
                        
                        update_window.update()
                
                # 在新线程中执行更新，避免阻塞UI
                threading.Thread(target=perform_update, daemon=True).start()
                
                # 运行主循环
                root.mainloop()
            else:
                print("用户选择跳过更新，直接启动应用")
                root.destroy()
                root.quit()
        else:
            print("没有发现新版本")
            
    except Exception as e:
        print(f"检查更新时发生错误，将直接启动应用: {e}")
        # 如果检查更新本身失败，也要继续启动应用
    
    # 第二步：启动应用（无论是否更新成功）
    print("正在启动应用...")
    manager = WindowManager()
    manager.create_app()