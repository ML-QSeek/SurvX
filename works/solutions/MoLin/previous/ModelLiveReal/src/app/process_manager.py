# process_manager.py
import multiprocessing as mp
import os
import sys
import json
import time
import signal
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
import traceback
import threading
import importlib.util
import hashlib


class ScriptProcess:
    """通用脚本进程的包装器"""
    
    def __init__(self, config: Dict, process_id: str):
        """
        初始化脚本进程
        
        Args:
            config: 脚本配置
            process_id: 进程ID
        """
        self.config = config
        self.process_id = process_id
        
        # 脚本信息
        self.script_path = config.get("script_path", "")
        self.script_name = config.get("script_name", "")
        self.script_module = config.get("script_module", None)  # 已导入的模块（可选）
        
        # 进程状态
        self.process = None
        self.status = "stopped"  # stopped, starting, running, error, stopping
        self.start_time = None
        self.error_message = ""
        self.last_heartbeat = time.time()
        
        # 进程间通信
        self.control_queue = mp.Queue()
        self.status_queue = mp.Queue()
        self.data_queue = mp.Queue()  # 用于数据传输（从前端脚本接收的消息）
        
        # 前端消息队列（专门用于向前端发送的消息）
        self.frontend_queue = mp.Queue()
        
    def start(self) -> bool:
        """启动脚本进程"""
        if self.status in ["starting", "running"]:
            return False
        
        self.status = "starting"
        
        try:
            # 准备进程参数
            process_args = {
                'config': self.config,
                'process_id': self.process_id,
                'control_queue': self.control_queue,
                'status_queue': self.status_queue,
                'data_queue': self.data_queue,
                'frontend_queue': self.frontend_queue,  # 传递给子进程的前端消息队列
            }
            
            # 创建并启动进程
            self.process = mp.Process(
                target=self._run_script,
                args=(process_args,),
                name=f"Script-{self.process_id}",
                daemon=False
            )
            
            self.process.start()
            self.start_time = time.time()
            
            # 等待进程初始化
            timeout = self.config.get("start_timeout", 10)
            start_wait = time.time()
            
            while time.time() - start_wait < timeout:
                if not self.status_queue.empty():
                    status_msg = self.status_queue.get()
                    if status_msg.get('status') == 'ready':
                        self.status = "running"
                        return True
                    elif status_msg.get('status') == 'error':
                        self.status = "error"
                        self.error_message = status_msg.get('message', '启动失败')
                        return False
                
                if not self.process.is_alive():
                    self.status = "error"
                    self.error_message = "进程启动失败"
                    return False
                
                time.sleep(0.1)
            
            # 超时
            self.status = "error"
            self.error_message = "进程启动超时"
            return False
            
        except Exception as e:
            self.status = "error"
            self.error_message = str(e)
            print(f"启动进程 {self.process_id} 失败: {e}")
            return False
    
    def stop(self, timeout: int = 30) -> bool:
        """停止脚本进程"""
        if self.status in ["stopped", "stopping"]:
            return True
        
        self.status = "stopping"
        
        try:
            # 发送停止信号
            if not self.control_queue.empty():
                # 清空队列
                while not self.control_queue.empty():
                    self.control_queue.get_nowait()
            self.control_queue.put({"command": "stop"})
            
            # 等待进程结束
            if self.process and self.process.is_alive():
                self.process.join(timeout=timeout)
                
                if self.process.is_alive():
                    # 强制终止
                    self.process.terminate()
                    self.process.join(timeout=5)
            
            self.status = "stopped"
            return True
            
        except Exception as e:
            print(f"停止进程 {self.process_id} 失败: {e}")
            self.status = "error"
            self.error_message = str(e)
            return False
    
    def restart(self) -> bool:
        """重启脚本进程"""
        if self.status in ["starting", "running"]:
            self.stop()
        
        time.sleep(1)
        return self.start()
    
    def send_command(self, command: str, data: Optional[Dict] = None) -> bool:
        """向脚本进程发送命令"""
        try:
            if self.status != "running" or not self.process.is_alive():
                return False
            
            self.control_queue.put({
                "command": command,
                "data": data or {}
            })
            return True
        except Exception:
            return False
    
    def get_status_info(self) -> Dict[str, Any]:
        """获取进程状态信息"""
        # 尝试从状态队列获取最新状态
        latest_status = None
        while not self.status_queue.empty():
            latest_status = self.status_queue.get()
        
        info = {
            "process_id": self.process_id,
            "status": self.status,
            "config_name": self.config.get("config_name", ""),
            "script_name": self.script_name or os.path.basename(self.script_path),
            "pid": self.process.pid if self.process else None,
            "start_time": self.start_time,
            "uptime": time.time() - self.start_time if self.start_time else 0,
            "error_message": self.error_message,
            "latest_status": latest_status,
            "config": {k: v for k, v in self.config.items() if k not in ['password', 'api_key']}  # 过滤敏感信息
        }
        
        return info
    
    def has_frontend_messages(self) -> bool:
        """检查是否有前端消息"""
        try:
            return not self.frontend_queue.empty()
        except:
            return False
    
    def get_frontend_messages(self) -> List[Dict]:
        """获取前端消息"""
        messages = []
        try:
            while not self.frontend_queue.empty():
                msg = self.frontend_queue.get_nowait()
                if isinstance(msg, dict):
                    # 添加进程信息
                    msg['process_id'] = self.process_id
                    msg['config_name'] = self.config.get("config_name", "")
                    messages.append(msg)
        except:
            pass
        return messages
    
    @staticmethod
    def _run_script(process_args: Dict):
        """
        进程目标函数 - 在独立进程中运行脚本
        
        注意：这个函数运行在子进程中！
        """
        config = process_args['config']
        process_id = process_args['process_id']
        control_queue = process_args['control_queue']
        status_queue = process_args['status_queue']
        data_queue = process_args['data_queue']
        frontend_queue = process_args['frontend_queue']  # 前端消息队列
        
        # 设置进程标题
        try:
            import setproctitle
            setproctitle.setproctitle(f"Script-{process_id}")
        except ImportError:
            pass
        
        # 获取脚本信息
        script_path = config.get("script_path", "")
        script_name = config.get("script_name", "")
        script_module = config.get("script_module", None)
        
        # 如果提供了已导入的模块，直接使用
        if script_module:
            # 这里需要特殊处理模块传递，通常推荐使用路径
            pass
        
        # 检查脚本路径
        if not script_path:
            status_queue.put({
                "status": "error",
                "message": "脚本路径未指定",
                "timestamp": time.time()
            })
            return
        
        # 检查脚本是否存在
        if not os.path.exists(script_path):
            status_queue.put({
                "status": "error",
                "message": f"脚本不存在: {script_path}",
                "timestamp": time.time()
            })
            return
        
        try:
            # 动态导入脚本模块
            script_dir = os.path.dirname(os.path.abspath(script_path))
            sys.path.insert(0, script_dir)
            
            # 生成唯一模块名
            module_hash = hashlib.md5(script_path.encode()).hexdigest()[:8]
            module_name = f"script_{module_hash}_{process_id.replace('-', '_')}"
            
            spec = importlib.util.spec_from_file_location(
                module_name,
                script_path
            )
            script_module = importlib.util.module_from_spec(spec)
            
            # 设置全局变量
            script_module.CONFIG = config
            script_module.PROCESS_ID = process_id
            script_module.CONTROL_QUEUE = control_queue
            script_module.STATUS_QUEUE = status_queue
            script_module.DATA_QUEUE = data_queue
            script_module.FRONTEND_QUEUE = frontend_queue  # 前端消息队列
            
            # 执行模块
            spec.loader.exec_module(script_module)
            
            # 检查脚本是否有必要的接口
            if not hasattr(script_module, 'ScriptMain'):
                status_queue.put({
                    "status": "error",
                    "message": "脚本没有 ScriptMain 类",
                    "timestamp": time.time()
                })
                return
            
            # 创建脚本实例
            script_config = config.copy()
            # 传递前端消息队列给脚本配置
            script_config['data_queue'] = frontend_queue
            script_instance = script_module.ScriptMain(script_config)
            
            # 通知父进程脚本已准备好
            status_queue.put({
                "status": "ready",
                "message": "脚本已加载",
                "timestamp": time.time(),
                "process_id": process_id
            })
            
            # 脚本主循环
            running = True
            last_heartbeat = time.time()
            
            while running:
                try:
                    # 检查控制命令
                    try:
                        if not control_queue.empty():
                            command = control_queue.get_nowait()
                            
                            if command.get("command") == "stop":
                                print(f"进程 {process_id} 收到停止命令")
                                running = False
                                break
                            elif hasattr(script_instance, 'handle_command'):
                                script_instance.handle_command(command)
                    
                    except Exception:
                        pass  # 队列为空
                    
                    # 运行脚本的主循环
                    if hasattr(script_instance, 'run_iteration'):
                        try:
                            script_instance.run_iteration()
                        except Exception as e:
                            print(f"脚本运行迭代失败: {e}")
                            traceback.print_exc()
                    
                    # 发送心跳
                    current_time = time.time()
                    if current_time - last_heartbeat > 5:
                        status_queue.put({
                            "status": "heartbeat",
                            "timestamp": current_time,
                            "process_id": process_id
                        })
                        last_heartbeat = current_time
                    
                    # 短暂休眠
                    sleep_time = config.get("sleep_time", 0.1)
                    time.sleep(sleep_time)
                    
                except KeyboardInterrupt:
                    print(f"进程 {process_id} 收到键盘中断")
                    running = False
                except Exception as e:
                    print(f"进程 {process_id} 主循环异常: {e}")
                    traceback.print_exc()
            
            # 清理资源
            if hasattr(script_instance, 'cleanup'):
                try:
                    script_instance.cleanup()
                except Exception as e:
                    print(f"脚本清理失败: {e}")
            
            # 发送停止状态
            status_queue.put({
                "status": "stopped",
                "timestamp": time.time(),
                "process_id": process_id
            })
            
        except Exception as e:
            print(f"进程 {process_id} 初始化失败: {e}")
            traceback.print_exc()
            status_queue.put({
                "status": "error",
                "message": str(e),
                "timestamp": time.time(),
                "process_id": process_id
            })


class ProcessPool:
    """通用进程池管理器"""
    
    def __init__(self, max_processes: int = 20, window=None):
        """
        初始化进程池
        
        Args:
            max_processes: 最大进程数
            window: pywebview窗口对象，用于向前端发送消息
        """
        self.max_processes = max_processes
        self.processes: Dict[str, ScriptProcess] = {}
        self.process_counter = 0
        
        # pywebview窗口引用
        self.window = window
        
        # 状态监控线程
        self.monitor_thread = None
        self.running = False
        
        # 进程状态变化回调
        self.status_callbacks: List[Callable] = []
        
        # 前端消息回调
        self.frontend_callbacks: List[Callable] = []
        
        # 前端消息转发线程
        self.frontend_message_thread = None
        self.frontend_message_queue = queue.Queue()
        
        # 锁用于线程安全
        self._lock = threading.RLock()
    
    def start(self) -> None:
        """启动进程池"""
        if self.running:
            return
        
        self.running = True
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="ProcessPoolMonitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        # 启动前端消息转发线程
        self.frontend_message_thread = threading.Thread(
            target=self._frontend_message_worker,
            name="FrontendMessageWorker",
            daemon=True
        )
        self.frontend_message_thread.start()
        
        print(f"进程池已启动，最大进程数: {self.max_processes}")
    
    def stop(self) -> None:
        """停止进程池和所有进程"""
        self.running = False
        
        # 发送退出信号给前端消息线程
        try:
            self.frontend_message_queue.put({
                "type": "system",
                "level": "info",
                "message": "进程池正在停止",
                "action": "exit"
            })
        except:
            pass
        
        # 停止所有进程
        with self._lock:
            for process_id, process in list(self.processes.items()):
                try:
                    process.stop()
                except Exception as e:
                    print(f"停止进程 {process_id} 失败: {e}")
        
        # 等待监控线程结束
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        # 等待前端消息线程结束
        if self.frontend_message_thread and self.frontend_message_thread.is_alive():
            self.frontend_message_thread.join(timeout=5)
        
        print("进程池已停止")
    
    def create_process(self, config: Dict) -> Optional[str]:
        """
        创建新的脚本进程
        
        Args:
            config: 配置字典，必须包含:
                - script_path: 脚本文件路径
                - config_name: 配置名称
                可选:
                - script_name: 脚本名称
                - start_timeout: 启动超时时间
                - sleep_time: 循环休眠时间
        
        Returns:
            进程ID或None
        """
        with self._lock:
            if len(self.processes) >= self.max_processes:
                print(f"错误: 已达到最大进程数限制 ({self.max_processes})")
                return None
            
            # 验证必要参数
            if "script_path" not in config:
                print("错误: 配置缺少 script_path")
                return None
            
            # 生成进程ID
            self.process_counter += 1
            config_name = config.get("config_name", f"config_{self.process_counter}")
            timestamp = int(time.time())
            process_id = f"{config_name}_{timestamp}"
            
            # 创建进程包装器
            process = ScriptProcess(config, process_id)
            
            # 尝试启动进程
            if process.start():
                self.processes[process_id] = process
                
                # 通知状态变化
                self._notify_status_change(process_id, "started")
                
                # 发送前端通知
                self._send_frontend_message({
                    "type": "system",
                    "level": "success",
                    "message": f"进程已启动: {config_name}",
                    "process_id": process_id,
                    "config_name": config_name,
                    "timestamp": time.time()
                })
                
                print(f"已创建进程: {process_id} - {os.path.basename(config['script_path'])}")
                return process_id
            else:
                print(f"创建进程失败: {process_id}")
                
                # 发送前端错误通知
                self._send_frontend_message({
                    "type": "system",
                    "level": "error",
                    "message": f"进程启动失败: {process.error_message}",
                    "process_id": process_id,
                    "config_name": config_name,
                    "timestamp": time.time()
                })
                
                return None
    
    def start_user_scripts(self, user_configs: List[Dict]) -> Dict[str, List[str]]:
        """
        批量启动用户脚本
        
        Args:
            user_configs: 用户配置列表，每个配置代表一个用户的脚本设置
        
        Returns:
            {
                "success": [成功启动的进程ID列表],
                "failed": [失败的用户配置列表]
            }
        """
        results = {"success": [], "failed": []}
        
        for user_config in user_configs:
            try:
                # 从用户配置生成进程配置
                process_config = self._build_process_config(user_config)
                process_id = self.create_process(process_config)
                
                if process_id:
                    results["success"].append(process_id)
                else:
                    results["failed"].append(user_config)
                    
            except Exception as e:
                print(f"处理用户配置失败: {e}")
                results["failed"].append(user_config)
        
        return results
    
    def _build_process_config(self, user_config: Dict) -> Dict:
        """
        从用户配置构建进程配置
        
        根据您的业务逻辑调整此方法
        """
        # 示例：用户配置转换为进程配置
        account_name = user_config.get("account_name", "")
        strategy_type = user_config.get("strategy_type", "")
        
        # 根据策略类型选择脚本
        script_map = {
            "day_trading": "day_trading_strategy.py",
            "swing_trading": "swing_trading_strategy.py",
            "arbitrage": "arbitrage_strategy.py",
        }
        
        script_name = script_map.get(strategy_type, "default_strategy.py")
        script_path = os.path.join("strategies", script_name)
        
        # 构建进程配置
        process_config = {
            "script_path": script_path,
            "script_name": script_name,
            "config_name": f"{account_name}_{strategy_type}",
            "user_config": user_config,  # 包含用户的所有设置
            "account_name": account_name,
            "strategy_type": strategy_type,
            "start_timeout": 15,
            "sleep_time": 0.1,
        }
        
        return process_config
    
    def stop_process(self, process_id: str, force: bool = False) -> bool:
        """停止指定进程"""
        with self._lock:
            #print(self.processes)
            #print(repr(process_id))  # 显示原始表示
            #print(repr(list(self.processes.keys())[0]))  # 对比字典中的键
            
            if process_id not in self.processes:
                print("没有这个线程啊")
                return False
            
            process = self.processes[process_id]
            config_name = process.config.get("config_name", process_id)
            
            # 发送前端通知
            self._send_frontend_message({
                "type": "system",
                "level": "info",
                "message": f"正在停止进程: {config_name}",
                "process_id": process_id,
                "config_name": config_name,
                "timestamp": time.time()
            })
            
            if force:
                success = process.stop()
            else:
                success = process.stop(timeout=30)
            
            if success:
                # 从进程池移除
                del self.processes[process_id]
                self._notify_status_change(process_id, "stopped")
                
                # 发送前端通知
                self._send_frontend_message({
                    "type": "system",
                    "level": "success",
                    "message": f"进程已停止: {config_name}",
                    "process_id": process_id,
                    "config_name": config_name,
                    "timestamp": time.time()
                })
            
            return success
    
    def restart_process(self, process_id: str) -> bool:
        """重启指定进程"""
        with self._lock:
            if process_id not in self.processes:
                return False
            
            process = self.processes[process_id]
            config_name = process.config.get("config_name", process_id)
            
            # 发送前端通知
            self._send_frontend_message({
                "type": "system",
                "level": "info",
                "message": f"正在重启进程: {config_name}",
                "process_id": process_id,
                "config_name": config_name,
                "timestamp": time.time()
            })
            
            return process.restart()
    
    def get_process_status(self, process_id: str) -> Optional[Dict]:
        """获取进程状态"""
        with self._lock:
            if process_id not in self.processes:
                return None
            
            return self.processes[process_id].get_status_info()
    
    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有进程状态"""
        with self._lock:
            status_dict = {}
            
            for process_id, process in self.processes.items():
                status_dict[process_id] = process.get_status_info()
            
            return status_dict
    
    def send_command_to_process(self, process_id: str, command: str, 
                               data: Optional[Dict] = None) -> bool:
        """向指定进程发送命令"""
        with self._lock:
            if process_id not in self.processes:
                return False
            
            process = self.processes[process_id]
            config_name = process.config.get("config_name", process_id)
            
            # 发送前端通知
            self._send_frontend_message({
                "type": "command",
                "level": "info",
                "message": f"发送命令: {command}",
                "process_id": process_id,
                "config_name": config_name,
                "command": command,
                "timestamp": time.time()
            })
            
            return process.send_command(command, data)
    
    def broadcast_command(self, command: str, data: Optional[Dict] = None) -> Dict[str, bool]:
        """向所有进程广播命令"""
        results = {}
        
        with self._lock:
            for process_id in self.processes.keys():
                success = self.send_command_to_process(process_id, command, data)
                results[process_id] = success
        
        return results
    
    def add_status_callback(self, callback: Callable) -> None:
        """添加状态变化回调函数"""
        with self._lock:
            self.status_callbacks.append(callback)
    
    def remove_status_callback(self, callback: Callable) -> None:
        """移除状态变化回调函数"""
        with self._lock:
            if callback in self.status_callbacks:
                self.status_callbacks.remove(callback)
    
    def add_frontend_callback(self, callback: Callable) -> None:
        """添加前端消息回调函数"""
        with self._lock:
            self.frontend_callbacks.append(callback)
    
    def remove_frontend_callback(self, callback: Callable) -> None:
        """移除前端消息回调函数"""
        with self._lock:
            if callback in self.frontend_callbacks:
                self.frontend_callbacks.remove(callback)
    
    def _notify_status_change(self, process_id: str, status: str) -> None:
        """通知状态变化"""
        callbacks = self.status_callbacks.copy()  # 复制一份避免在迭代中修改
        
        for callback in callbacks:
            try:
                callback(process_id, status)
            except Exception as e:
                print(f"状态回调执行失败: {e}")
    
    def _notify_frontend_message(self, message: Dict) -> None:
        """通知前端消息"""
        callbacks = self.frontend_callbacks.copy()  # 复制一份避免在迭代中修改
        
        for callback in callbacks:
            try:
                callback(message)
            except Exception as e:
                print(f"前端消息回调执行失败: {e}")
    
    def _send_frontend_message(self, message: Dict) -> None:
        """发送前端消息（内部调用）"""
        try:
            self.frontend_message_queue.put(message)
        except Exception as e:
            print(f"发送前端消息到队列失败: {e}")
    
    def handle_process_message(self, message: Dict):
        """
        处理来自进程的消息并转发到前端
        
        Args:
            message: 消息字典，应该包含:
                - type: 消息类型 (system, trade, account, error, warning, info)
                - level: 消息级别 (info, warning, error, success)
                - message: 消息内容
                - timestamp: 时间戳
                - process_id: 进程ID
                - config_name: 配置名称
        """
        if not self.window:
            return
        try:
            # 确保消息格式正确
            if not isinstance(message, dict):
                return
            
            # 添加默认字段
            if 'timestamp' not in message:
                message['timestamp'] = time.time()
            
            # 转换为JSON字符串
            message_json = json.dumps(message, ensure_ascii=False, default=str)
            # 调用前端JavaScript函数
            # 这里假设前端有showNotification函数
            #js_code = f"showNotification({message_json})"
            #js_code = f"console.log({message_json})"
            
            js_code = f"chulidata({message_json})"
            
            #print(6666666666666666666666666)
            #print(js_code)
            self.window.evaluate_js(js_code)
            #print(555555555)
        except Exception as e:
            print(f"处理进程消息失败: {e}")
            traceback.print_exc()
    
    def _frontend_message_worker(self):
        """前端消息转发工作线程"""
        print("前端消息转发线程启动")
        
        while self.running:
            try:
                # 从队列获取消息
                message = self.frontend_message_queue.get(timeout=1)
                #print('获取了')
                #print(json.dumps(message))
                # 检查是否为退出消息
                if message.get("action") == "exit":
                    print("收到退出信号，停止前端消息转发线程")
                    break
                
                # 处理消息
                try:
                    # 调用前端JavaScript
                    if self.window:
                        self.handle_process_message(message)
                    
                    # 调用前端回调
                    self._notify_frontend_message(message)
                    
                except Exception as e:
                    print(f"处理前端消息失败: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"前端消息转发线程异常: {e}")
                time.sleep(1)
        
        print("前端消息转发线程停止")
    
    def _monitor_loop(self) -> None:
        """监控线程主循环"""
        while self.running:
            try:
                # 检查所有进程的状态
                dead_processes = []
                
                with self._lock:
                    for process_id, process in list(self.processes.items()):
                        try:
                            if process.process and not process.process.is_alive():
                                # 进程意外退出
                                process.status = "error"
                                process.error_message = "进程意外退出"
                                dead_processes.append(process_id)
                                
                                self._notify_status_change(process_id, "crashed")
                                
                                # 发送前端通知
                                self._send_frontend_message({
                                    "type": "system",
                                    "level": "error",
                                    "message": f"进程意外退出: {process_id}",
                                    "process_id": process_id,
                                    "config_name": process.config.get("config_name", process_id),
                                    "error_message": process.error_message,
                                    "timestamp": time.time()
                                })
                                
                                print(f"警告: 进程 {process_id} 意外退出")
                        
                        except:
                            pass
                    
                    # 清理死亡进程
                    for process_id in dead_processes:
                        if process_id in self.processes:
                            del self.processes[process_id]
                    
                    # 收集状态信息和前端消息
                    self._collect_status_messages()
                    self._collect_frontend_messages()
                
            except Exception as e:
                print(f"监控循环异常: {e}")
            
            # 每2秒检查一次
            time.sleep(1)
    
    def _collect_status_messages(self) -> None:
        """收集所有进程的状态消息"""
        for process_id, process in self.processes.items():
            try:
                # 检查是否有新的状态消息
                while not process.status_queue.empty():
                    status_msg = process.status_queue.get()
                    
                    status_type = status_msg.get('status', '')
                    process_info = process.config.get("config_name", process_id)
                    
                    if status_type == 'heartbeat':
                        # 更新最后心跳时间
                        process.last_heartbeat = time.time()
                    elif status_type == 'error':
                        # 错误消息
                        process.error_message = status_msg.get('message', '')
                        self._notify_status_change(process_id, "error")
                        
                        # 发送前端通知
                        self._send_frontend_message({
                            "type": "system",
                            "level": "error",
                            "message": f"进程错误: {process_info}",
                            "process_id": process_id,
                            "config_name": process_info,
                            "error_message": process.error_message,
                            "timestamp": time.time()
                        })
                    elif status_type == 'warning':
                        # 警告消息
                        self._notify_status_change(process_id, "warning")
                        
                        # 发送前端通知
                        self._send_frontend_message({
                            "type": "system",
                            "level": "warning",
                            "message": f"进程警告: {process_info} - {status_msg.get('message', '')}",
                            "process_id": process_id,
                            "config_name": process_info,
                            "timestamp": time.time()
                        })
                    elif status_type == 'info':
                        # 信息消息
                        self._notify_status_change(process_id, "info")
                    
            except Exception as e:
                print(f"收集进程 {process_id} 状态消息失败: {e}")
    
    def _collect_frontend_messages(self) -> None:
        """收集所有进程的前端消息并转发"""
        for process_id, process in self.processes.items():
            try:
                # 检查是否有新的前端消息
                if process.has_frontend_messages():
                    messages = process.get_frontend_messages()
                    for message in messages:
                        # 确保消息包含必要信息
                        if 'process_id' not in message:
                            message['process_id'] = process_id
                        if 'config_name' not in message:
                            message['config_name'] = process.config.get("config_name", process_id)
                        
                        # 发送到前端消息队列
                        self._send_frontend_message(message)
                        
            except Exception as e:
                print(f"收集进程 {process_id} 前端消息失败: {e}")
    def set_window(self, window):
        """设置/更新窗口引用"""
        with self._lock:
            old_window = self.window
            self.window = window
            
            print(f"[DEBUG] 更新窗口引用: {old_window} -> {window}")
            
            # 如果从 None 变为有效窗口，发送积压消息
            if old_window is None and window is not None:
                print("[INFO] 窗口已就绪，进程池可以开始发送消息")
                
'''
# 单例模式
_process_pool_instance = None

def get_process_pool(max_processes: int = 20, window=None) -> ProcessPool:
    """获取全局进程池单例"""
    global _process_pool_instance
    
    if _process_pool_instance is None:
        _process_pool_instance = ProcessPool(max_processes=max_processes, window=window)
        _process_pool_instance.start()
    
    # 更新窗口引用
    if window and _process_pool_instance.window != window:
        _process_pool_instance.window = window
    
    return _process_pool_instance

'''

_process_pool_instance = None
def get_process_pool(max_processes: int = 20, window=None) -> ProcessPool:
    """获取全局进程池单例"""
    global _process_pool_instance
    
    print(f"[DEBUG] 获取进程池: window={window}, 已有实例={_process_pool_instance is not None}")
    
    if _process_pool_instance is None:
        print("[INFO] 创建新的进程池实例")
        _process_pool_instance = ProcessPool(max_processes=max_processes, window=window)
        _process_pool_instance.start()
    else:
        print("[INFO] 使用现有进程池实例")
    
    # 更新窗口引用（无论是否新建）
    if window is not None:
        print("[INFO] 更新进程池窗口引用")
        _process_pool_instance.set_window(window)
    
    return _process_pool_instance

def update_process_pool_window(window):
    """更新进程池的window引用"""
    global _process_pool_instance
    
    if _process_pool_instance is not None:
        _process_pool_instance.set_window(window)
        print("已更新进程池window引用")

def shutdown_process_pool() -> None:
    """关闭全局进程池"""
    global _process_pool_instance
    
    if _process_pool_instance is not None:
        _process_pool_instance.stop()
        _process_pool_instance = None


# 需要在文件顶部添加queue导入
try:
    import queue
except ImportError:
    import Queue as queue