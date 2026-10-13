"""
窗口管理器
"""
import webview
import tkinter as tk
import threading
import time
import os
import sys
import requests
import json

from api import Api
from connection_pool import ConnectionPool
from credential_manager import CredentialManager


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
        
        # 获取资源路径
        if hasattr(sys, '_MEIPASS'):  # 打包后的环境
            self.base_path = sys._MEIPASS
        else:  # 开发环境
            self.base_path = os.path.abspath("../../")
        
        # 页面路径
        self.login_path = os.path.join(self.base_path, "src/ui/index.html")
        self.dash_path = os.path.join(self.base_path, "src/ui/main.html")
    
    def create_app(self):
        """创建应用窗口"""
        # 检查登录页面是否存在
        if not os.path.exists(self.login_path):
            print(f"错误: {self.login_path} 文件不存在!")
            return
        
        # 创建窗口
        self.window = webview.create_window(
            '请先登录',
            url=f'file://{self.login_path}',
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
        
        
        # 更新进程池的window引用
        from process_manager import update_process_pool_window
        update_process_pool_window(self.window)
        
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
        r = requests.post(Url, data=Sub_Field)
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
        """加载主应用页面"""
        if not self.user_data:
            print("错误：未登录用户尝试加载主页面")
            return
        
        username = self.user_data.get('username', '').strip()
        
        # 调整窗口大小
        new_width = 1800
        new_height = 900
        self.window.resize(new_width, new_height)
        
        # 获取屏幕尺寸并居中
        root = tk.Tk()
        root.withdraw()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        x = (screen_width - new_width) // 2
        y = (screen_height - new_height) // 2
        
        self.window.move(x, y)
        
        # 更新存储的窗口尺寸
        self.window_width = new_width
        self.window_height = new_height
        
        # 加载主页面
        print(f"正在加载主页面: {self.dash_path}")
        self.window.load_url(f'{self.dash_path}?par={username}')
        
        root.destroy()
        root.quit()