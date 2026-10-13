import subprocess
import ctypes
from ctypes import wintypes
import sys
import os
import time

class WindowsCredentialManager:
    """Windows凭据管理器操作"""
    
    def __init__(self):
        self.advapi32 = ctypes.windll.advapi32
        self.kernel32 = ctypes.windll.kernel32
        
    def store_credential(self, target, username, password):
        """
        将凭据存储到Windows凭据管理器
        target: 目标名称，如"TERMSRV/192.168.1.100"
        """
        try:
            # 使用cmdkey命令存储凭据
            command = f'cmdkey /generic:{target} /user:{username} /pass:{password}'
            subprocess.run(command, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"存储凭据失败: {e}")
            return False
    
    def delete_credential(self, target):
        """删除存储的凭据"""
        command = f'cmdkey /delete:{target}'
        subprocess.run(command, shell=True)

def create_rdp_with_windows_credentials(host, username, password=None):
    """
    使用Windows凭据管理器的安全方式
    """
    if password:
        # 存储到Windows凭据管理器
        cm = WindowsCredentialManager()
        target = f"TERMSRV/{host}"
        cm.store_credential(target, username, password)
    
    # 创建不包含密码的RDP文件
    rdp_content = f"""
full address:s:{host}
prompt for credentials:i:0
authentication level:i:2
"""
    
    filename = f'temp_connection.rdp'
    with open(filename, 'w') as f:
        f.write(rdp_content)
    
    # 启动连接
    subprocess.Popen(['mstsc', filename])
    
    # 可选：连接后删除临时文件
    time.sleep(5)
    try:
        os.remove(filename)
    except:
        pass