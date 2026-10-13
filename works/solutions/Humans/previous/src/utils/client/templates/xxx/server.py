#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SurvX 后端服务 - 多进程架构
实例管理器 (主进程) → 实例进程 (每个实例独立) → 计算子进程池 (每个实例多个)
"""

import json
import os
import time
import threading
import multiprocessing as mp
import shutil
import uuid
import signal
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from queue import Empty
from datetime import datetime

# ============================================================
# 常量
# ============================================================

DEFAULT_NUM_WORKERS = 4  # 每个实例的默认计算子进程数
TICK_INTERVAL = 0.5  # tick 间隔 (秒)
STATE_SAVE_INTERVAL = 10  # 状态保存间隔 (tick 次数)


# ============================================================
# 消息协议 (主进程 ↔ 实例进程 ↔ 计算子进程)
# ============================================================

class MessageType:
    # 主进程 → 实例进程
    CMD_START = 'cmd_start'          # 启动 tick
    CMD_STOP = 'cmd_stop'            # 停止 tick
    CMD_GET_STATE = 'cmd_get_state'  # 获取全量状态
    CMD_GET_UPDATE = 'cmd_get_update'  # 获取增量
    CMD_MOVE = 'cmd_move'            # 移动人物
    CMD_ACTION = 'cmd_action'        # 用户操作
    CMD_SHUTDOWN = 'cmd_shutdown'    # 关闭实例

    # 实例进程 → 主进程
    MSG_STATE_UPDATE = 'msg_state_update'  # 状态更新推送
    MSG_FULL_STATE = 'msg_full_state'      # 全量状态
    MSG_INSTANCE_INFO = 'msg_instance_info'  # 实例信息

    # 实例进程 → 计算子进程
    TASK_COMPUTE = 'task_compute'    # 计算任务

    # 计算子进程 → 实例进程
    RESULT_COMPUTE = 'result_compute'  # 计算结果


# ============================================================
# 计算子进程
# ============================================================

def worker_process(task_queue: mp.Queue, result_queue: mp.Queue, worker_id: int):
    """
    计算子进程主循环
    从 task_queue 接收任务，计算结果放入 result_queue
    """
    print(f"[Worker-{worker_id}] 启动")
    while True:
        try:
            task = task_queue.get(timeout=1.0)
            if task is None:
                # 收到 None 表示退出
                print(f"[Worker-{worker_id}] 收到退出信号")
                break

            task_id = task.get('task_id')
            task_type = task.get('type')
            params = task.get('params', {})

            # 执行计算
            result = _do_computation(task_type, params)

            # 返回结果
            result_queue.put({
                'type': MessageType.RESULT_COMPUTE,
                'task_id': task_id,
                'result': result,
                'worker_id': worker_id
            })

        except Empty:
            continue
        except Exception as e:
            print(f"[Worker-{worker_id}] 错误: {e}")
            # 返回错误结果
            result_queue.put({
                'type': MessageType.RESULT_COMPUTE,
                'task_id': task.get('task_id') if 'task' in locals() else 'unknown',
                'error': str(e),
                'worker_id': worker_id
            })

    print(f"[Worker-{worker_id}] 退出")


def _do_computation(task_type: str, params: Dict) -> Any:
    """
    实际计算逻辑
    这里放 AI 推理、路径规划、复杂模拟等
    """
    # 模拟计算耗时
    time.sleep(0.1)

    if task_type == 'pathfinding':
        # 路径规划示例
        start = params.get('start', {'x': 0, 'y': 0})
        end = params.get('end', {'x': 100, 'y': 100})
        # 简单直线路径
        steps = 10
        path = []
        for i in range(steps + 1):
            t = i / steps
            path.append({
                'x': start['x'] + (end['x'] - start['x']) * t,
                'y': start['y'] + (end['y'] - start['y']) * t
            })
        return {'path': path, 'steps': steps}

    elif task_type == 'ai_reasoning':
        # AI 推理示例
        prompt = params.get('prompt', '')
        return {'response': f"[AI] 收到: {prompt[:20]}...", 'confidence': 0.85}

    elif task_type == 'resource_calc':
        # 资源计算示例
        resources = params.get('resources', {})
        total = sum(resources.values()) if resources else 0
        return {'total': total, 'details': resources}

    else:
        return {'status': 'done', 'params': params}


# ============================================================
# 实例进程
# ============================================================

class InstanceProcess:
    """
    实例进程
    每个实例独立运行，管理自己的状态和计算子进程池
    """

    def __init__(self, instance_id: str, path: str, num_workers: int = DEFAULT_NUM_WORKERS):
        self.instance_id = instance_id
        self.path = path
        self.num_workers = num_workers

        # 状态
        self.status = 'created'  # 'created' | 'running' | 'stopped'
        self.config: Dict = {}
        self.sego: Dict = {}
        self.state: Dict = {}

        # 进程通信
        self.parent_pipe: Optional[mp.Pipe] = None
        self.worker_task_queues: List[mp.Queue] = []
        self.worker_result_queue: Optional[mp.Queue] = None
        self.workers: List[mp.Process] = []

        # Tick 控制
        self._running = False
        self._tick_thread: Optional[threading.Thread] = None
        self._tick_counter = 0
        self._weather_counter = 0
        self._update_queue: List[Dict] = []  # 待推送的更新

        # 加载数据
        self._load_config()
        self._load_sego()
        self._load_state()

    # ---- 加载/保存 ----

    def _load_config(self):
        path = os.path.join(self.path, 'config.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

    def _load_sego(self):
        path = os.path.join(self.path, 'sego.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.sego = json.load(f)

    def _load_state(self):
        path = os.path.join(self.path, 'state.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.state = json.load(f)
        else:
            self.state = self._create_default_state()

    def _save_state(self):
        path = os.path.join(self.path, 'state.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

    def _create_default_state(self) -> Dict:
        chars = self.sego.get('characters', {})
        state_chars = {}
        for cid, cinfo in chars.items():
            state_chars[cid] = {
                'x': cinfo.get('initial', {}).get('x', 200),
                'y': cinfo.get('initial', {}).get('y', 320),
                'z': cinfo.get('initial', {}).get('z', 0),
                **cinfo.get('stats', {})
            }
        return {
            'timeOfDay': 'day',
            'weather': 'clear',
            'intensity': 0,
            'items': {},
            'trees': {},
            'buildings': {},
            'characters': state_chars
        }

    # ---- 进程启动/停止 ----

    def start(self, parent_pipe: mp.Pipe):
        """启动实例进程"""
        self.parent_pipe = parent_pipe
        self._running = True
        self.status = 'running'

        # 启动计算子进程
        self._start_workers()

        # 启动 tick 线程
        self._tick_thread = threading.Thread(target=self._tick_loop, daemon=True)
        self._tick_thread.start()

        print(f"[Instance-{self.instance_id}] 启动 (workers={self.num_workers})")

    def stop(self):
        """停止实例进程"""
        self._running = False
        self.status = 'stopped'

        # 停止计算子进程
        self._stop_workers()

        if self._tick_thread:
            self._tick_thread.join(timeout=2)

        # 保存状态
        self._save_state()

        print(f"[Instance-{self.instance_id}] 停止")

    def _start_workers(self):
        """启动计算子进程池"""
        self.worker_result_queue = mp.Queue()
        for i in range(self.num_workers):
            task_queue = mp.Queue()
            self.worker_task_queues.append(task_queue)
            p = mp.Process(
                target=worker_process,
                args=(task_queue, self.worker_result_queue, i),
                daemon=True
            )
            p.start()
            self.workers.append(p)

    def _stop_workers(self):
        """停止计算子进程池"""
        # 发送 None 信号
        for q in self.worker_task_queues:
            try:
                q.put(None, timeout=0.5)
            except:
                pass

        # 等待子进程结束
        for p in self.workers:
            p.join(timeout=2)
            if p.is_alive():
                p.terminate()

        self.workers = []
        self.worker_task_queues = []

    # ---- Tick 循环 ----

    def _tick_loop(self):
        """tick 主循环"""
        save_counter = 0

        while self._running:
            try:
                self._update_state()
                save_counter += 1

                # 定期保存状态
                if save_counter >= STATE_SAVE_INTERVAL:
                    self._save_state()
                    save_counter = 0

                self._tick_counter += 1

                # 如果有父进程，推送更新
                if self.parent_pipe:
                    self._push_updates()

                # 处理计算结果
                self._process_results()

                time.sleep(TICK_INTERVAL)

            except Exception as e:
                print(f"[Instance-{self.instance_id}] tick 错误: {e}")
                time.sleep(1)

    def _update_state(self):
        """更新状态逻辑"""
        # 时间变化
        times = ['day', 'dusk', 'night', 'dawn']
        current = self.state.get('timeOfDay', 'day')
        if current in times:
            idx = times.index(current)
            if self._tick_counter % 20 == 0:
                self.state['timeOfDay'] = times[(idx + 1) % len(times)]

        # 天气随机变化
        import random
        weathers = ['clear', 'clear', 'clear', 'rain', 'snow', 'storm', 'fog']
        if self._tick_counter % 30 == 0:
            self.state['weather'] = random.choice(weathers)
            self.state['intensity'] = random.random() * 0.8 + 0.2

        # 人物随机移动 (模拟)
        chars = self.state.get('characters', {})
        w = self.config.get('field', {}).get('width', 1000)
        h = self.config.get('field', {}).get('height', 800)

        for cid, cdata in chars.items():
            import random
            cdata['x'] += random.randint(-2, 2)
            cdata['y'] += random.randint(-2, 2)
            cdata['x'] = max(10, min(w - 10, cdata['x']))
            cdata['y'] = max(10, min(h - 10, cdata['y']))

            # 随机状态变化
            if random.random() < 0.05:
                cdata['health'] = max(50, min(100, cdata.get('health', 80) + random.randint(-3, 3)))
            if random.random() < 0.05:
                cdata['energy'] = max(40, min(100, cdata.get('energy', 70) + random.randint(-3, 3)))

            # 随机想法/说话
            if random.random() < 0.02:
                thoughts = ['今天天气真好', '肚子有点饿了', '得想办法生火', '前面有片森林', '该造个更结实的住所了']
                cdata['thought'] = f"💭 {random.choice(thoughts)}"
            if random.random() < 0.02:
                speeches = ['这里的风景不错', '饿死了，找点吃的', '父亲你在哪里', '这片森林很安全', '日落了该回营地了']
                cdata['speech'] = f"🗣️ {random.choice(speeches)}"

    def _push_updates(self):
        """推送更新到主进程"""
        if not self.parent_pipe:
            return

        try:
            # 推送全量状态 (每 5 tick 一次)
            if self._tick_counter % 5 == 0:
                self.parent_pipe.send({
                    'type': MessageType.MSG_FULL_STATE,
                    'data': self.get_full_state()
                })
            else:
                # 推送增量 (人物变化)
                chars = self.state.get('characters', {})
                if chars:
                    self.parent_pipe.send({
                        'type': MessageType.MSG_STATE_UPDATE,
                        'data': {
                            'type': 'character',
                            'data': chars
                        }
                    })

                # 推送世界变化 (天气)
                self.parent_pipe.send({
                    'type': MessageType.MSG_STATE_UPDATE,
                    'data': {
                        'type': 'world',
                        'data': {
                            'timeOfDay': self.state.get('timeOfDay'),
                            'weather': self.state.get('weather'),
                            'intensity': self.state.get('intensity', 0),
                        }
                    }
                })

        except Exception as e:
            print(f"[Instance-{self.instance_id}] 推送失败: {e}")

    def _process_results(self):
        """处理计算子进程返回的结果"""
        if not self.worker_result_queue:
            return

        try:
            while True:
                result = self.worker_result_queue.get_nowait()
                # 处理结果 (更新状态或推送给前端)
                if result.get('error'):
                    print(f"[Instance-{self.instance_id}] 计算错误: {result.get('error')}")
                else:
                    # 将结果存入状态或推送
                    task_id = result.get('task_id')
                    if task_id:
                        # 可以存储结果供后续使用
                        pass
        except Empty:
            pass

    # ---- 公开接口 (供主进程调用) ----

    def get_full_state(self) -> Dict:
        return {
            'config': self.config,
            'sego': self.sego,
            'state': self.state
        }

    def get_info(self) -> Dict:
        return {
            'id': self.instance_id,
            'name': self.config.get('field', {}).get('name', '未命名'),
            'status': self.status
        }

    def handle_move(self, char_id: str, x: float, y: float):
        """处理移动"""
        chars = self.state.get('characters', {})
        if char_id in chars:
            chars[char_id]['x'] = x
            chars[char_id]['y'] = y
            # 计算地形高度
            z = self._get_terrain_z(x, y)
            chars[char_id]['z'] = z
            self._save_state()

    def _get_terrain_z(self, x: float, y: float) -> float:
        """获取地形高度"""
        terrains = self.config.get('terrains', [])
        for t in terrains:
            if self._point_in_polygon(x, y, t.get('points', [])):
                # 找最近点的 z
                min_dist = float('inf')
                closest_z = 0
                for p in t.get('points', []):
                    dx = p['x'] - x
                    dy = p['y'] - y
                    dist = dx * dx + dy * dy
                    if dist < min_dist:
                        min_dist = dist
                        closest_z = p.get('z', 0)
                return closest_z
        return 0

    def _point_in_polygon(self, px: float, py: float, polygon: List) -> bool:
        inside = False
        n = len(polygon)
        for i in range(n):
            j = (i + 1) % n
            xi, yi = polygon[i]['x'], polygon[i]['y']
            xj, yj = polygon[j]['x'], polygon[j]['y']
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
                inside = not inside
        return inside

    def handle_action(self, action: str, params: Dict):
        """处理用户操作"""
        if action == 'oracle':
            # 神谕操作 - 可以触发计算任务
            coord = params.get('coord')
            text = params.get('text')
            # 提交计算任务
            self._submit_computation_task('ai_reasoning', {
                'prompt': text,
                'coord': coord
            })
        elif action == 'communicate':
            target = params.get('target')
            text = params.get('text')
            # 处理交流
            pass
        elif action == 'teach':
            target = params.get('target')
            knowledge = params.get('knowledge')
            # 处理传授
            pass
        elif action == 'improve':
            target = params.get('target')
            attr = params.get('attr')
            # 处理提升
            pass

    def _submit_computation_task(self, task_type: str, params: Dict) -> Optional[str]:
        """提交计算任务到子进程"""
        if not self.worker_task_queues:
            return None

        task_id = str(uuid.uuid4())[:8]

        # 找空闲队列
        for i, q in enumerate(self.worker_task_queues):
            if q.empty():
                q.put({
                    'task_id': task_id,
                    'type': task_type,
                    'params': params
                })
                return task_id

        # 全忙，返回 None
        return None


# ============================================================
# 实例管理器 (主进程)
# ============================================================

class InstanceManager:
    """管理所有实例进程"""

    def __init__(self, instances_dir: str = './instances', templates_dir: str = './templates'):
        self.instances_dir = instances_dir
        self.templates_dir = templates_dir

        # 实例数据
        self.instances: Dict[str, Dict] = {}  # instance_id -> { process, pipe, instance_obj }
        self._load_all_instances()

        # 当前连接 (前端 → 实例)
        self.current_connection: Optional[str] = None

    def _load_all_instances(self):
        """加载所有实例"""
        if not os.path.exists(self.instances_dir):
            os.makedirs(self.instances_dir)

        for dir_name in os.listdir(self.instances_dir):
            dir_path = os.path.join(self.instances_dir, dir_name)
            if os.path.isdir(dir_path):
                try:
                    # 创建实例对象
                    inst = InstanceProcess(dir_name, dir_path)
                    self.instances[dir_name] = {
                        'process': None,
                        'pipe': None,
                        'instance': inst
                    }
                    print(f"加载实例: {dir_name} ({inst.status})")
                except Exception as e:
                    print(f"加载实例失败 {dir_name}: {e}")

    def get_instance_list(self) -> List[Dict]:
        """获取实例列表"""
        result = []
        for info in self.instances.values():
            inst = info['instance']
            result.append(inst.get_info())
        return result

    def get_instance(self, instance_id: str) -> Optional[InstanceProcess]:
        """获取实例对象"""
        info = self.instances.get(instance_id)
        if info:
            return info['instance']
        return None

    def start_instance(self, instance_id: str) -> bool:
        """启动实例进程"""
        info = self.instances.get(instance_id)
        if not info:
            return False

        inst = info['instance']
        if inst.status == 'running':
            return True

        # 创建管道
        parent_conn, child_conn = mp.Pipe()

        # 创建进程
        p = mp.Process(
            target=self._run_instance_process,
            args=(instance_id, inst.path, child_conn, inst.num_workers),
            daemon=True
        )
        p.start()

        info['process'] = p
        info['pipe'] = parent_conn

        # 等待实例进程启动
        time.sleep(0.5)

        return True

    def _run_instance_process(self, instance_id: str, path: str, conn: mp.Pipe, num_workers: int):
        """在子进程中运行实例"""
        # 在子进程中重建实例对象
        inst = InstanceProcess(instance_id, path, num_workers)
        inst.start(conn)

        # 主循环：监听父进程指令
        while inst._running:
            try:
                if conn.poll(timeout=0.5):
                    msg = conn.recv()
                    self._handle_parent_message(inst, msg)
            except Exception as e:
                print(f"[Instance-{instance_id}] 管道错误: {e}")
                break

        inst.stop()

    def _handle_parent_message(self, inst: InstanceProcess, msg: Dict):
        """处理来自父进程的消息"""
        cmd = msg.get('type')

        if cmd == MessageType.CMD_GET_STATE:
            # 返回全量状态
            if inst.parent_pipe:
                inst.parent_pipe.send({
                    'type': MessageType.MSG_FULL_STATE,
                    'data': inst.get_full_state()
                })

        elif cmd == MessageType.CMD_MOVE:
            char_id = msg.get('char_id')
            x = msg.get('x')
            y = msg.get('y')
            inst.handle_move(char_id, x, y)

        elif cmd == MessageType.CMD_ACTION:
            action = msg.get('action')
            params = msg.get('params', {})
            inst.handle_action(action, params)

        elif cmd == MessageType.CMD_STOP:
            inst._running = False

    def stop_instance(self, instance_id: str) -> bool:
        """停止实例进程"""
        info = self.instances.get(instance_id)
        if not info:
            return False

        inst = info['instance']
        if inst.status != 'running':
            return True

        # 发送停止命令
        if info['pipe']:
            try:
                info['pipe'].send({'type': MessageType.CMD_STOP})
            except:
                pass

        # 等待进程结束
        if info['process']:
            info['process'].join(timeout=5)
            if info['process'].is_alive():
                info['process'].terminate()

        info['process'] = None
        info['pipe'] = None

        return True

    def create_instance(self, name: str, template: str = 'island') -> Optional[InstanceProcess]:
        """创建新实例"""
        instance_id = f"world_{uuid.uuid4().hex[:8]}"
        instance_path = os.path.join(self.instances_dir, instance_id)
        os.makedirs(instance_path, exist_ok=True)

        # 从模板复制文件
        template_path = os.path.join(self.templates_dir, template)
        if os.path.exists(template_path):
            for filename in ['config.json', 'sego.json', 'state.json']:
                src = os.path.join(template_path, filename)
                dst = os.path.join(instance_path, filename)
                if os.path.exists(src):
                    shutil.copy(src, dst)

        # 修改 config 中的 name
        config_path = os.path.join(instance_path, 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            config['field']['name'] = name
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        # 创建实例
        inst = InstanceProcess(instance_id, instance_path)
        self.instances[instance_id] = {
            'process': None,
            'pipe': None,
            'instance': inst
        }

        print(f"创建实例: {instance_id} ({name})")
        return inst

    def delete_instance(self, instance_id: str) -> bool:
        """删除实例"""
        info = self.instances.get(instance_id)
        if not info:
            return False

        # 先停止
        self.stop_instance(instance_id)

        # 删除目录
        inst = info['instance']
        try:
            shutil.rmtree(inst.path)
            del self.instances[instance_id]
            print(f"删除实例: {instance_id}")
            return True
        except Exception as e:
            print(f"删除实例失败 {instance_id}: {e}")
            return False

    def set_connection(self, instance_id: Optional[str]):
        """设置当前连接 (前端连接的实例)"""
        self.current_connection = instance_id
        if instance_id:
            print(f"[连接] 当前连接到: {instance_id}")
        else:
            print("[连接] 已断开")

    # ---- 消息处理 (主进程接收实例进程的推送) ----

    def poll_messages(self) -> List[Dict]:
        """轮询所有实例进程的消息"""
        messages = []

        for instance_id, info in self.instances.items():
            pipe = info.get('pipe')
            if not pipe:
                continue

            try:
                while pipe.poll(timeout=0.01):
                    msg = pipe.recv()
                    msg['_instance_id'] = instance_id
                    messages.append(msg)
            except:
                pass

        return messages


# ============================================================
# 信号处理
# ============================================================

def signal_handler(signum, frame):
    print("\n收到退出信号，正在关闭所有实例...")
    sys.exit(0)


# ============================================================
# 创建默认模板
# ============================================================

def create_default_templates():
    """创建默认模板目录"""
    templates = {
        'island': {
            'config.json': {
                "field": {
                    "name": "荒岛求生",
                    "width": 1000,
                    "height": 800,
                    "zMin": -60,
                    "zMax": 150
                },
                "terrains": [
                    {"id": "beach", "name": "🏖️ 海滩", "color": "#f4d03f", "points": [
                        {"x": 506, "y": 726, "z": -5}, {"x": 509, "y": 653, "z": -5.3},
                        {"x": 558, "y": 588, "z": -5.4}, {"x": 648, "y": 573, "z": -5.7}
                    ]},
                    {"id": "grassland", "name": "🌿 草地", "color": "#7cb342", "points": [
                        {"x": 533, "y": 699, "z": 5}, {"x": 532, "y": 640, "z": 5},
                        {"x": 571, "y": 590, "z": 4.6}, {"x": 633, "y": 590, "z": 3.4}
                    ]},
                    {"id": "forest", "name": "🌳 森林", "color": "#2e7d32", "points": [
                        {"x": 459, "y": 604, "z": 20.1}, {"x": 438, "y": 569, "z": 20.7},
                        {"x": 389, "y": 564, "z": 19.6}, {"x": 388, "y": 521, "z": 20.6}
                    ]},
                    {"id": "hills", "name": "⛰️ 丘陵", "color": "#8d6e63", "points": [
                        {"x": 613, "y": 483, "z": 50.8}, {"x": 593, "y": 477, "z": 48.7},
                        {"x": 581, "y": 463, "z": 54.1}, {"x": 563, "y": 455, "z": 51.1}
                    ]},
                    {"id": "mountain", "name": "🏔️ 高山", "color": "#a569bd", "points": [
                        {"x": 588, "y": 458, "z": 80.2}, {"x": 575, "y": 457, "z": 77.8},
                        {"x": 566, "y": 452, "z": 79.2}, {"x": 556, "y": 448, "z": 78.8}
                    ]},
                    {"id": "snow", "name": "❄️ 雪顶", "color": "#ffffff", "points": [
                        {"x": 571, "y": 445, "z": 120.1}, {"x": 566, "y": 445, "z": 121.4},
                        {"x": 562, "y": 444, "z": 123.1}, {"x": 559, "y": 442, "z": 122.5}
                    ]}
                ],
                "items": [
                    {"id": "shell", "icon": "🐚", "name": "贝壳", "x": 550, "y": 560, "z": -1},
                    {"id": "coral", "icon": "🪸", "name": "珊瑚", "x": 533, "y": 623, "z": -4.7},
                    {"id": "berry", "icon": "🫐", "name": "浆果丛", "x": 443, "y": 624, "z": 10.3}
                ]
            },
            'sego.json': {
                "characters": {
                    "robinson": {
                        "name": "鲁滨逊",
                        "icon": "🧒",
                        "initial": {"x": 200, "y": 320, "z": 0},
                        "stats": {"health": 85, "energy": 70, "mood": 60, "hunger": 50}
                    },
                    "father": {
                        "name": "父亲",
                        "icon": "👨‍🦱",
                        "initial": {"x": 260, "y": 290, "z": 0},
                        "stats": {"health": 80, "energy": 65, "mood": 55, "hunger": 60}
                    }
                },
                "defaultCharacter": "robinson"
            },
            'state.json': {
                "timeOfDay": "day",
                "weather": "clear",
                "intensity": 0,
                "items": {},
                "trees": {},
                "buildings": {},
                "characters": {}
            }
        }
    }

    os.makedirs('./templates', exist_ok=True)

    for template_name, files in templates.items():
        template_path = os.path.join('./templates', template_name)
        os.makedirs(template_path, exist_ok=True)
        for filename, content in files.items():
            file_path = os.path.join(template_path, filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(content, f, indent=2, ensure_ascii=False)
                print(f"创建模板: {template_path}/{filename}")

    # 创建默认实例
    manager = InstanceManager()
    if len(manager.instances) == 0:
        inst = manager.create_instance("荒岛求生", "island")
        if inst:
            manager.start_instance(inst.instance_id)
            print(f"创建默认实例: {inst.instance_id} (已启动)")


# ============================================================
# JSBridge 适配器 (供原生层调用)
# ============================================================

class JSBridgeAdapter:
    """
    JSBridge 适配器
    原生层通过这个类处理前端调用
    """

    def __init__(self, manager: InstanceManager):
        self.manager = manager
        self._callbacks: Dict[str, callable] = {}

    def handle(self, action: str, params: Dict) -> Any:
        """处理前端 JSBridge 调用"""
        print(f"[JSBridge] action={action}, params={params}")

        if action == 'getInstanceList':
            return self.manager.get_instance_list()

        elif action == 'connectInstance':
            instance_id = params.get('instanceId')
            if instance_id:
                self.manager.set_connection(instance_id)
                # 启动实例（如果未启动）
                self.manager.start_instance(instance_id)
                # 返回全量状态
                inst = self.manager.get_instance(instance_id)
                if inst:
                    return {'status': 'connected', 'fullState': inst.get_full_state()}
            return {'status': 'error', 'message': '实例不存在'}

        elif action == 'disconnectInstance':
            self.manager.set_connection(None)
            return {'status': 'disconnected'}

        elif action == 'createInstance':
            name = params.get('name', '新世界')
            template = params.get('template', 'island')
            inst = self.manager.create_instance(name, template)
            if inst:
                return {'status': 'created', 'instanceId': inst.instance_id}
            return {'status': 'error', 'message': '创建失败'}

        elif action == 'startInstance':
            instance_id = params.get('instanceId')
            if instance_id:
                self.manager.start_instance(instance_id)
                return {'status': 'started'}
            return {'status': 'error', 'message': '实例不存在'}

        elif action == 'stopInstance':
            instance_id = params.get('instanceId')
            if instance_id:
                self.manager.stop_instance(instance_id)
                return {'status': 'stopped'}
            return {'status': 'error', 'message': '实例不存在'}

        elif action == 'deleteInstance':
            instance_id = params.get('instanceId')
            if instance_id:
                self.manager.delete_instance(instance_id)
                return {'status': 'deleted'}
            return {'status': 'error', 'message': '实例不存在'}

        elif action == 'moveCharacter':
            instance_id = self.manager.current_connection
            if not instance_id:
                return {'status': 'error', 'message': '未连接实例'}

            inst = self.manager.get_instance(instance_id)
            if not inst:
                return {'status': 'error', 'message': '实例不存在'}

            char_id = params.get('id')
            x = params.get('x')
            y = params.get('y')
            if char_id and x is not None and y is not None:
                # 通过管道发送移动命令
                info = self.manager.instances.get(instance_id)
                if info and info.get('pipe'):
                    info['pipe'].send({
                        'type': MessageType.CMD_MOVE,
                        'char_id': char_id,
                        'x': x,
                        'y': y
                    })
                    return {'status': 'ok'}
            return {'status': 'error', 'message': '参数错误'}

        elif action == 'userAction':
            instance_id = self.manager.current_connection
            if not instance_id:
                return {'status': 'error', 'message': '未连接实例'}

            info = self.manager.instances.get(instance_id)
            if info and info.get('pipe'):
                info['pipe'].send({
                    'type': MessageType.CMD_ACTION,
                    'action': params.get('action'),
                    'params': params.get('params', {})
                })
                return {'status': 'ok'}
            return {'status': 'error', 'message': '实例不可用'}

        else:
            return {'status': 'error', 'message': f'未知操作: {action}'}


# ============================================================
# 主进程入口
# ============================================================

def main():
    print("=" * 60)
    print("SurvX 后端服务 (多进程架构)")
    print("=" * 60)

    # 信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 创建模板和默认实例
    create_default_templates()

    # 初始化管理器
    manager = InstanceManager()
    print(f"\n当前实例: {len(manager.instances)} 个")
    for info in manager.get_instance_list():
        print(f"  - {info['id']}: {info['name']} ({info['status']})")

    # 创建 JSBridge 适配器
    bridge = JSBridgeAdapter(manager)

    print("\n" + "=" * 60)
    print("服务已启动")
    print("=" * 60)
    print("\n📡 JSBridge 接口:")
    print("  - getInstanceList")
    print("  - connectInstance { instanceId }")
    print("  - disconnectInstance")
    print("  - createInstance { name, template }")
    print("  - startInstance { instanceId }")
    print("  - stopInstance { instanceId }")
    print("  - deleteInstance { instanceId }")
    print("  - moveCharacter { id, x, y }")
    print("  - userAction { action, params }")
    print("\n💡 按 Ctrl+C 退出")

    # 暴露 bridge 给外部调用
    global _bridge
    _bridge = bridge

    try:
        # 主循环：轮询实例进程的消息
        while True:
            messages = manager.poll_messages()
            for msg in messages:
                instance_id = msg.pop('_instance_id', None)
                msg_type = msg.get('type')

                if msg_type == MessageType.MSG_FULL_STATE:
                    # 全量状态 → 推送到前端
                    print(f"[{instance_id}] 全量状态更新")
                    # 这里应该调用 WebView 的 evaluateJavascript
                    # 实际实现由原生层提供
                    pass

                elif msg_type == MessageType.MSG_STATE_UPDATE:
                    # 增量更新 → 推送到前端
                    data = msg.get('data', {})
                    # print(f"[{instance_id}] 增量更新: {data.get('type')}")

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n正在关闭所有实例...")
        for info in manager.instances.values():
            inst = info['instance']
            if inst.status == 'running':
                manager.stop_instance(inst.instance_id)
        print("已退出")


# ============================================================
# 导出 (供原生层直接调用)
# ============================================================

_bridge: Optional[JSBridgeAdapter] = None


def jsbridge_handle(action: str, params: Dict) -> Any:
    """原生层调用 JSBridge"""
    if _bridge:
        return _bridge.handle(action, params)
    return {'status': 'error', 'message': '服务未就绪'}


if __name__ == '__main__':
    main()