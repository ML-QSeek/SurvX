# system_monitor_daemon.py
"""
系统监控守护进程 - Socket.IO版本
简化版：随应用程序启动，出错自动重启
"""

import time
import logging
from typing import Dict, Any, Optional
import platform
import psutil
import socket
import datetime
import os
import socketio
import traceback

class ScriptMain:
    """
    系统监控守护进程 - Socket.IO版本
    遵循 ScriptMain 接口规范，简化设计
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化系统监控
        
        Args:
            config: 监控配置
        """
        self.config = config or {}
        self.running = True  # 随应用启动就运行
        
        # Socket.IO 客户端
        self.sio = None
        self.connected = False
        
        # 配置参数
        self.server_url = self.config.get("server_url", "http://localhost:3213")
        self.auth_token = self.config.get("auth_token", "")
        self.monitor_name = self.config.get("monitor_name", socket.gethostname())
        
        # 监控间隔（秒）
        self.collect_interval = self.config.get("collect_interval", 10)
        self.push_interval = self.config.get("push_interval", 180)  # 3分钟
        
        # 阈值配置
        self.thresholds = {
            'cpu_percent': self.config.get("cpu_threshold", 90.0),
            'memory_percent': self.config.get("memory_threshold", 85.0),
            'disk_percent': self.config.get("disk_threshold", 90.0),
            'temperature': self.config.get("temp_threshold", 85.0)
        }
        
        # 数据存储
        self.system_info = {}
        self.last_push_time = 0
        self.last_heartbeat = 0
        self.heartbeat_interval = 60  # 心跳间隔秒
        
        # 错误统计
        self.error_count = 0
        self.max_errors = 10
        self.last_error_time = 0
        self.error_reset_interval = 300  # 5分钟后重置错误计数
        
        # 初始化日志
        self._setup_logging()
        
        # 建立Socket.IO连接
        self._init_socketio()
        
        # 收集基本信息
        self._collect_basic_info()
        
        self.logger.info(f"系统监控初始化完成: {self.monitor_name}")
    
    def _setup_logging(self):
        """设置日志"""
        self.logger = logging.getLogger("SystemMonitor")
        
        # 避免重复配置
        if not self.logger.handlers:
            self.logger.setLevel(logging.INFO)
            
            # 控制台输出
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # 格式化
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            
            self.logger.addHandler(console_handler)
    
    def _init_socketio(self):
        """初始化Socket.IO连接"""
        try:
            self.sio = socketio.Client()
            
            @self.sio.event
            def connect():
                self.connected = True
                self.logger.info('Socket.IO连接已建立')
                self._send_register_message()
            
            @self.sio.event
            def connect_error(data):
                self.connected = False
                self.logger.error(f'Socket.IO连接失败: {data}')
            
            @self.sio.event
            def disconnect():
                self.connected = False
                self.logger.warning('Socket.IO连接已断开')
            
            # 尝试连接
            headers = {}
            if self.auth_token:
                headers['Authorization'] = f'Bearer {self.auth_token}'
            
            self.sio.connect(self.server_url, headers=headers, wait_timeout=5)
            self.connected = True
            
        except Exception as e:
            self.logger.warning(f"Socket.IO初始化失败: {e}")
            self.connected = False
    
    def _collect_basic_info(self):
        """收集基本信息"""
        try:
            self.system_info['hostname'] = socket.gethostname()
            self.system_info['platform'] = platform.system()
            self.system_info['python_version'] = platform.python_version()
            self.system_info['ip_address'] = self._get_ip_address()
            self.system_info['cpu_name'] = self._get_cpu_name()
            self.system_info['cpu_count'] = psutil.cpu_count(logical=False) or 0
            
        except Exception as e:
            self.logger.error(f"收集基本信息失败: {e}")
            self._report_error(f"收集基本信息失败: {e}")
    
    def run_iteration(self):
        """
        主循环迭代 - 每调用一次执行一次监控
        
        注意: 这个方法会被进程池循环调用
        """
        if not self.running:
            return
        
        try:
            current_time = time.time()
            
            # 错误恢复检查
            if self.error_count > 0:
                if current_time - self.last_error_time > self.error_reset_interval:
                    self.error_count = 0
                    self.logger.info("错误计数已重置")
            
            # 收集系统信息
            self._collect_system_info()
            
            # 检查异常
            anomalies = self._check_anomalies()
            
            # 发送心跳
            if current_time - self.last_heartbeat > self.heartbeat_interval:
                self._send_heartbeat()
                self.last_heartbeat = current_time
            
            # 推送数据（定期或异常时）
            should_push = anomalies or (current_time - self.last_push_time > self.push_interval)
            if should_push and self.connected:
                self._push_data(anomalies)
                self.last_push_time = current_time
            
            # 重连检查
            if not self.connected and current_time - self.last_push_time > 30:
                self._reconnect()
            
            # 休眠控制（外部进程池控制）
            
        except Exception as e:
            error_msg = f"监控迭代失败: {str(e)}"
            self.logger.error(error_msg)
            self._report_error(error_msg)
            self._handle_error(e)
    
    def handle_command(self, command):
        """
        处理控制命令
        
        Args:
            command: 命令字典
        """
        try:
            cmd = command.get("command")
            data = command.get("data", {})
            
            if cmd == "stop":
                self.running = False
            elif cmd == "start":
                self.running = True
            elif cmd == "restart":
                self._restart_monitor()
            elif cmd == "update_config":
                self._update_config(data)
            elif cmd == "get_status":
                self._send_status()
            elif cmd == "test_connection":
                self._test_connection()
            else:
                self.logger.warning(f"未知命令: {cmd}")
                
        except Exception as e:
            self.logger.error(f"处理命令失败: {e}")
            self._report_error(f"处理命令失败: {e}")
    
    def cleanup(self):
        """
        清理资源 - 应用关闭时调用
        """
        self.logger.info("清理监控资源...")
        self.running = False
        
        # 发送停止消息
        if self.connected and self.sio:
            try:
                self.sio.emit('system_event', {
                    'monitor_name': self.monitor_name,
                    'hostname': self.system_info.get('hostname'),
                    'message': '监控进程停止',
                    'event': 'shutdown',
                    'timestamp': datetime.datetime.now().isoformat()
                })
                time.sleep(0.5)
                self.sio.disconnect()
            except:
                pass
        
        self.logger.info("系统监控已停止")
    
    def _collect_system_info(self):
        """收集系统信息"""
        try:
            # CPU使用率
            self.system_info['cpu_percent'] = psutil.cpu_percent(interval=0.5)
            
            # 内存信息
            memory = psutil.virtual_memory()
            self.system_info['memory'] = {
                'total_gb': self._bytes_to_gb(memory.total),
                'used_gb': self._bytes_to_gb(memory.used),
                'percent': memory.percent
            }
            
            # 磁盘信息
            try:
                root_path = '/' if platform.system() != "Windows" else 'C:\\'
                if os.path.exists(root_path):
                    disk = psutil.disk_usage(root_path)
                    self.system_info['disk'] = {
                        'total_gb': self._bytes_to_gb(disk.total),
                        'used_gb': self._bytes_to_gb(disk.used),
                        'percent': disk.percent,
                        'mountpoint': root_path
                    }
            except:
                self.system_info['disk'] = {}
            
            # 进程计数
            self.system_info['process_count'] = len(psutil.pids())
            
            # 启动时间
            boot_time = psutil.boot_time()
            self.system_info['uptime_seconds'] = int(time.time() - boot_time)
            
            # 时间戳
            self.system_info['timestamp'] = datetime.datetime.now().isoformat()
            
        except Exception as e:
            raise Exception(f"收集系统信息失败: {e}")
    
    def _check_anomalies(self):
        """检查异常"""
        anomalies = []
        
        try:
            # CPU检查
            cpu_percent = self.system_info.get('cpu_percent')
            if cpu_percent and cpu_percent > self.thresholds['cpu_percent']:
                anomalies.append(f"CPU使用率过高: {cpu_percent:.1f}%")
            
            # 内存检查
            memory_percent = self.system_info.get('memory', {}).get('percent')
            if memory_percent and memory_percent > self.thresholds['memory_percent']:
                anomalies.append(f"内存使用率过高: {memory_percent:.1f}%")
            
            # 磁盘检查
            disk_percent = self.system_info.get('disk', {}).get('percent')
            if disk_percent and disk_percent > self.thresholds['disk_percent']:
                anomalies.append(f"磁盘使用率过高: {disk_percent:.1f}%")
                
        except Exception as e:
            self.logger.debug(f"检查异常时出错: {e}")
        
        return anomalies
    
    def _send_heartbeat(self):
        """发送心跳"""
        if self.connected and self.sio:
            try:
                self.sio.emit('heartbeat', {
                    'monitor_name': self.monitor_name,
                    'timestamp': datetime.datetime.now().isoformat()
                })
            except Exception as e:
                self.logger.debug(f"发送心跳失败: {e}")
                self.connected = False
    
    def _push_data(self, anomalies):
        """推送数据到服务器"""
        try:
            data = {
                'timestamp': self.system_info.get('timestamp'),
                'monitor_name': self.monitor_name,
                'hostname': self.system_info.get('hostname'),
                'ip_address': self.system_info.get('ip_address'),
                'has_anomalies': len(anomalies) > 0,
                'anomalies': anomalies,
                
                'metrics': {
                    'cpu': {
                        'percent': self.system_info.get('cpu_percent'),
                        'name': self.system_info.get('cpu_name'),
                        'cores': self.system_info.get('cpu_count')
                    },
                    'memory': self.system_info.get('memory', {}),
                    'disk': self.system_info.get('disk', {}),
                    'process_count': self.system_info.get('process_count', 0),
                    'uptime_hours': round(self.system_info.get('uptime_seconds', 0) / 3600, 2)
                },
                
                'thresholds': self.thresholds
            }
            
            self.sio.emit('system_metrics', data)
            
            if anomalies:
                self.logger.info(f"异常数据已推送 ({len(anomalies)}个异常)")
            else:
                self.logger.debug("周期数据已推送")
                
        except Exception as e:
            self.logger.error(f"推送数据失败: {e}")
            self.connected = False
    
    def _report_error(self, error_message):
        """报告错误到服务器"""
        try:
            if self.connected and self.sio:
                self.sio.emit('system_error', {
                    'monitor_name': self.monitor_name,
                    'hostname': self.system_info.get('hostname'),
                    'error': error_message,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'error_count': self.error_count
                })
        except:
            pass  # 如果连不上服务器，也就算了
    
    def _send_register_message(self):
        """发送注册消息"""
        try:
            if self.connected and self.sio:
                self.sio.emit('register_monitor', {
                    'monitor_name': self.monitor_name,
                    'hostname': self.system_info.get('hostname'),
                    'ip_address': self.system_info.get('ip_address'),
                    'type': 'system_monitor',
                    'timestamp': datetime.datetime.now().isoformat(),
                    'auth_token': self.auth_token if self.auth_token else None
                })
        except Exception as e:
            self.logger.debug(f"发送注册消息失败: {e}")
    
    def _reconnect(self):
        """尝试重新连接"""
        try:
            if self.sio:
                self.sio.disconnect()
                time.sleep(1)
            
            self._init_socketio()
            if self.connected:
                self.logger.info("Socket.IO重连成功")
            else:
                self.logger.warning("Socket.IO重连失败")
                
        except Exception as e:
            self.logger.error(f"重连失败: {e}")
    
    def _handle_error(self, error):
        """处理错误，自动重启逻辑"""
        self.error_count += 1
        self.last_error_time = time.time()
        
        # 如果错误太多，考虑重启
        if self.error_count >= self.max_errors:
            self.logger.error(f"错误过多({self.error_count}次)，尝试重启...")
            self._restart_monitor()
            self.error_count = 0
    
    def _restart_monitor(self):
        """重启监控"""
        self.logger.info("重启监控...")
        try:
            # 清理旧连接
            if self.sio:
                self.sio.disconnect()
            
            # 重新初始化
            self._init_socketio()
            self._collect_basic_info()
            
            self.logger.info("监控重启完成")
            
        except Exception as e:
            self.logger.error(f"重启失败: {e}")
            self._report_error(f"重启失败: {e}")
    
    def _update_config(self, new_config):
        """更新配置"""
        try:
            for key, value in new_config.items():
                if key == 'cpu_threshold':
                    self.thresholds['cpu_percent'] = float(value)
                elif key == 'memory_threshold':
                    self.thresholds['memory_percent'] = float(value)
                elif key == 'disk_threshold':
                    self.thresholds['disk_percent'] = float(value)
                elif key == 'push_interval':
                    self.push_interval = int(value)
                elif key == 'collect_interval':
                    self.collect_interval = int(value)
            
            self.logger.info(f"配置已更新: {new_config}")
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
    
    def _send_status(self):
        """发送状态信息"""
        try:
            if self.connected and self.sio:
                status_data = {
                    'monitor_name': self.monitor_name,
                    'hostname': self.system_info.get('hostname'),
                    'running': self.running,
                    'connected': self.connected,
                    'error_count': self.error_count,
                    'last_push_time': self.last_push_time,
                    'timestamp': datetime.datetime.now().isoformat()
                }
                self.sio.emit('system_status', status_data)
        except Exception as e:
            self.logger.debug(f"发送状态失败: {e}")
    
    def _test_connection(self):
        """测试连接"""
        try:
            if self.connected and self.sio:
                self.sio.emit('connection_test', {
                    'monitor_name': self.monitor_name,
                    'timestamp': datetime.datetime.now().isoformat(),
                    'result': 'success'
                })
                self.logger.info("连接测试成功")
            else:
                self.logger.warning("连接测试失败: 未连接")
        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
    
    # 工具方法
    def _get_ip_address(self):
        """获取IP地址"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _get_cpu_name(self):
        """获取CPU型号"""
        try:
            if platform.system() == "Windows":
                return platform.processor()
            elif platform.system() == "Darwin":
                import subprocess
                return subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode().strip()
            elif platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('model name'):
                            return line.split(':')[1].strip()
            return "Unknown CPU"
        except:
            return "Unknown CPU"
    
    def _bytes_to_gb(self, bytes_value):
        """字节转GB"""
        try:
            return round(bytes_value / (1024 ** 3), 2)
        except:
            return None


# 使用示例
def create_monitor_process(config=None):
    """
    创建监控进程的辅助函数
    
    Args:
        config: 监控配置
        
    Returns:
        ScriptMain实例
    """
    if config is None:
        config = {
            "server_url": "http://10.10.98.51:3213",
            "monitor_name": socket.gethostname(),
            "collect_interval": 10,
            "push_interval": 180,
        }
    
    return ScriptMain(config)


# 简化的测试代码
if __name__ == "__main__":
    # 创建监控实例
    monitor = create_monitor_process()
    
    # 模拟进程池调用
    import time
    
    try:
        for i in range(10):  # 运行10次迭代
            print(f"\n迭代 {i+1}")
            monitor.run_iteration()
            time.sleep(5)  # 模拟进程池间隔
        
        # 测试命令处理
        monitor.handle_command({"command": "get_status"})
        
        # 清理
        monitor.cleanup()
        
    except KeyboardInterrupt:
        print("\n用户中断")
        monitor.cleanup()
    except Exception as e:
        print(f"错误: {e}")
        monitor.cleanup()