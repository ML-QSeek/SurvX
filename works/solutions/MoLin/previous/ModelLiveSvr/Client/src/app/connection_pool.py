import time
import socket
import urllib.request
from urllib.parse import urlparse

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