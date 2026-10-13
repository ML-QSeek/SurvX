#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
人物进程 - 三层决策架构 (带SQLite持久化)

进程1 (主进程): 实时行为控制，与服务器tick同步
进程2 (规划进程): 中长期目标生成，不与服务器同步
进程3 (反思进程): 经验总结与自我改进，不与服务器同步

使用方式:
  python ego.py <world_name> <character_id> <character_name> <ws_host> <ws_port> <channel_id>
  例: python ego.py 荒岛求生 robinson 鲁滨逊 127.0.0.1 8765 0
"""

import sys
import time
import json
import random
import threading
import queue
import multiprocessing as mp
import sqlite3
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# ==================== 日志重定向 ====================

LOG_FILE_PATH = None

def setup_logging(world_name: str, character_id: str, character_name: str):
    """将 print 输出重定向到文件"""
    global LOG_FILE_PATH
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(script_dir, "..", "..", "logs", world_name)
        os.makedirs(log_dir, exist_ok=True)
        LOG_FILE_PATH = os.path.join(log_dir, f"ego_{character_id}.log")
        
        log_file = open(LOG_FILE_PATH, 'a', encoding='utf-8')
        
        log_file.write("\n" + "=" * 60 + "\n")
        log_file.write(f"Ego 启动: {character_name} ({character_id})\n")
        log_file.write(f"世界: {world_name}\n")
        log_file.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("=" * 60 + "\n")
        log_file.flush()
        
        original_stdout = sys.stdout
        original_stderr = sys.stderr
        
        class Tee:
            def __init__(self, *files):
                self.files = files
            def write(self, obj):
                for f in self.files:
                    try:
                        f.write(obj)
                        f.flush()
                    except:
                        pass
            def flush(self):
                for f in self.files:
                    try:
                        f.flush()
                    except:
                        pass
        
        sys.stdout = Tee(original_stdout, log_file)
        sys.stderr = Tee(original_stderr, log_file)
        
        print(f"[{character_name}] 日志文件: {LOG_FILE_PATH}")
        return LOG_FILE_PATH
    except Exception as e:
        print(f"[{character_name}] 日志设置失败: {e}")
        return None

# 设置多进程启动方式 (Windows 需要)
try:
    mp.set_start_method('spawn', force=True)
except RuntimeError:
    pass

# ==================== 参数解析 ====================

WORLD_NAME = sys.argv[1] if len(sys.argv) > 1 else "荒岛求生"
CHARACTER_ID = sys.argv[2] if len(sys.argv) > 2 else "ego_test"
CHARACTER_NAME = sys.argv[3] if len(sys.argv) > 3 else "测试人物"
WS_HOST = sys.argv[4] if len(sys.argv) > 4 else "127.0.0.1"
WS_PORT = int(sys.argv[5]) if len(sys.argv) > 5 else 8765
CHANNEL_ID = int(sys.argv[6]) if len(sys.argv) > 6 else -1

setup_logging(WORLD_NAME, CHARACTER_ID, CHARACTER_NAME)

# 自动扫描 db 路径
INSTANCE_DIR = f"../data/instance/{WORLD_NAME}"
DB_PATH = None
if os.path.exists(INSTANCE_DIR):
    for f in os.listdir(INSTANCE_DIR):
        if f.startswith('ego_') and f.endswith('.db'):
            if CHARACTER_ID in f:
                DB_PATH = os.path.join(INSTANCE_DIR, f)
                break

if DB_PATH is None:
    print(f"[{CHARACTER_NAME}] 错误: 找不到 ego_{CHARACTER_ID}.db 文件在 {INSTANCE_DIR}")
    sys.exit(1)

WS_URL = f"ws://{WS_HOST}:{WS_PORT}"

# ==================== 数据库管理 ====================

class CharacterDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None  # 长连接，延迟初始化
        self._init_db()
    
    def _get_conn(self):
        """获取或创建长连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def _close_conn(self):
        """关闭长连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
        
    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS character_state (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                description TEXT,
                priority INTEGER,
                target_state TEXT,
                progress REAL DEFAULT 0.0,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT,
                importance REAL,
                emotion TEXT,
                lesson TEXT,
                context TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER,
                action_type TEXT,
                action_data TEXT,
                state_before TEXT,
                state_after TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experience_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_key TEXT UNIQUE,
                stat_value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
    
    def get_state(self, key: str, default=None):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM character_state WHERE key = ?', (key,))
        row = cursor.fetchone()
        return json.loads(row[0]) if row else default
            
    def set_state(self, key: str, value: Any):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO character_state (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (key, json.dumps(value)))
        conn.commit()
    
    def get_all_states(self) -> Dict:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT key, value FROM character_state')
        return {row[0]: json.loads(row[1]) for row in cursor.fetchall()}
    
    def add_goal(self, goal: 'Goal') -> int:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO goals (type, description, priority, target_state, progress, active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            goal.type.value,
            goal.description,
            goal.priority,
            json.dumps(goal.target_state),
            goal.progress,
            1 if goal.active else 0
        ))
        conn.commit()
        return cursor.lastrowid
            
    def get_active_goals(self) -> List['Goal']:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, type, description, priority, target_state, progress, active
            FROM goals WHERE active = 1 ORDER BY priority DESC
        ''')
        goals = []
        for row in cursor.fetchall():
            goals.append(Goal(
                id=row[0],
                type=GoalType(row[1]),
                description=row[2],
                priority=row[3],
                target_state=json.loads(row[4]),
                progress=row[5],
                active=bool(row[6])
            ))
        return goals
            
    def update_goal_progress(self, goal_id: int, progress: float):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE goals SET progress = ? WHERE id = ?
        ''', (progress, goal_id))
        conn.commit()
            
    def complete_goal(self, goal_id: int):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE goals SET active = 0, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (goal_id,))
        conn.commit()
    
    def add_memory(self, memory: 'Memory'):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO memories (event, importance, emotion, lesson, context)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            memory.event,
            memory.importance,
            memory.emotion,
            memory.lesson,
            json.dumps(memory.context)
        ))
        conn.commit()
            
    def get_recent_memories(self, limit: int = 20) -> List['Memory']:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT event, importance, emotion, lesson, context, created_at
            FROM memories ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        memories = []
        for row in cursor.fetchall():
            memories.append(Memory(
                event=row[0],
                importance=row[1],
                emotion=row[2],
                lesson=row[3],
                context=json.loads(row[4]),
                created_at=row[5]
            ))
        return memories
    
    def add_action(self, tick: int, action_type: str, action_data: Dict, 
                   state_before: Dict, state_after: Dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO action_history (tick, action_type, action_data, state_before, state_after)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            tick,
            action_type,
            json.dumps(action_data),
            json.dumps(state_before),
            json.dumps(state_after)
        ))
        conn.commit()
            
    def get_action_history(self, limit: int = 100) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tick, action_type, action_data, state_before, state_after, created_at
            FROM action_history ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        return [{
            'tick': row[0],
            'action_type': row[1],
            'action_data': json.loads(row[2]),
            'state_before': json.loads(row[3]),
            'state_after': json.loads(row[4]),
            'created_at': row[5]
        } for row in cursor.fetchall()]

# ==================== 数据结构 ====================

class GoalType(Enum):
    SURVIVAL = "survival"
    EXPLORATION = "exploration"
    BUILDING = "building"
    SOCIAL = "social"
    HEALTH = "health"
    RESOURCE = "resource"

@dataclass
class Goal:
    type: GoalType
    description: str
    priority: int
    target_state: Dict[str, Any]
    progress: float = 0.0
    active: bool = True
    id: Optional[int] = None
    created_at: Optional[str] = None

@dataclass
class Memory:
    event: str
    importance: float
    emotion: str = ""
    lesson: str = ""
    context: Dict[str, Any] = None
    created_at: Optional[str] = None

# ==================== 进程1: 主进程 ====================

class EgoMainProcess:
    def __init__(self, character_id, character_name, ws_host, ws_port, channel_id, db_path):
        self.character_id = character_id
        self.character_name = character_name
        self.ws_host = ws_host
        self.ws_port = ws_port
        self.channel_id = channel_id
        
        self.db = CharacterDB(db_path)
        self.db_path = db_path
        
        self.state = self.db.get_state('current_state', {
            "x": random.randint(100, 900),
            "y": random.randint(100, 700),
            "z": 0,
            "health": 85,
            "energy": 70,
            "mood": 60,
            "hunger": 50,
        })
        
        self.current_goals = self.db.get_active_goals()
        
        # 使用 multiprocessing.Queue 跨进程通信
        self.plan_input = mp.Queue()
        self.plan_output = mp.Queue()
        self.reflect_input = mp.Queue()
        self.reflect_output = mp.Queue()
        
        self.ws = None
        self.ws_connected = False
        self.joined = False
        self.game_started = False
        self.kicked = False
        self.should_exit = False
        self.channel_topic = None
        self.current_tick = -1
        self.last_message_time = time.time()
        self.decision_timeout = 45
        
        self.thought = ""
        self.speech = ""
        self.thought_timer = 0
        self.speech_timer = 0
        
        self.tick_count = 0
        
        self._start_child_processes()
        
        # 主进程中的消息处理线程 (处理子进程发来的消息)
        threading.Thread(target=self._handle_plan_messages, daemon=True).start()
        threading.Thread(target=self._handle_reflect_messages, daemon=True).start()
        
    def _start_child_processes(self):
        self.plan_process = mp.Process(
            target=_run_plan_process,
            args=(self.character_id, self.character_name, self.db_path,
                  self.plan_input, self.plan_output)
        )
        self.plan_process.start()
        
        self.reflect_process = mp.Process(
            target=_run_reflect_process,
            args=(self.character_id, self.character_name, self.db_path,
                  self.reflect_input, self.reflect_output)
        )
        self.reflect_process.start()
        
    def _handle_plan_messages(self):
        while not self.should_exit:
            try:
                msg = self.plan_output.get(timeout=0.1)
                if msg.get('type') == 'new_goal':
                    goal_data = msg['data']
                    goal = Goal(
                        type=GoalType(goal_data['type']),
                        description=goal_data['description'],
                        priority=goal_data['priority'],
                        target_state=goal_data['target_state']
                    )
                    goal_id = self.db.add_goal(goal)
                    goal.id = goal_id
                    self.current_goals.append(goal)
                    print(f"[{self.character_name}] 新目标: {goal.description}")
            except queue.Empty:
                continue
                
    def _handle_reflect_messages(self):
        while not self.should_exit:
            try:
                msg = self.reflect_output.get(timeout=0.1)
                if msg.get('type') == 'memory':
                    memory = Memory(**msg['data'])
                    self.db.add_memory(memory)
                    self.thought = f"反思: {memory.lesson}"
                    self.thought_timer = time.time() + 5.0
                    print(f"[{self.character_name}] 反思: {memory.lesson}")
            except queue.Empty:
                continue

    # ==================== WebSocket ====================
    
    def on_message(self, ws_client, message):
        print(f"[{self.character_name}] 收到消息: {message[:150]}...")
        
        try:
            data = json.loads(message)
            self.last_message_time = time.time()
            
            # 处理直接类型的消息
            if data.get('type') == 'world_state':
                print(f"[{self.character_name}] 收到直接 world_state")
                state_data = data.get('data', {})
                self.current_tick = state_data.get('tick', -1)
                if not self.channel_topic:
                    self.channel_topic = state_data.get('channel_topic')
                
                if not self.joined and self.channel_topic:
                    print(f"[{self.character_name}] 发送 subscribe, topic={self.channel_topic}")
                    ws_client.send(json.dumps({
                        "action": "subscribe",
                        "topic": self.channel_topic
                    }))
                    self.joined = True
                    print(f"[{self.character_name}] 加入世界成功 (频道 {self.channel_id})")
                    
                chars = state_data.get('characters', {})
                if self.character_id in chars:
                    char_data = chars[self.character_id]
                    for key in ['x', 'y', 'z', 'health', 'energy', 'mood', 'hunger']:
                        if key in char_data:
                            self.state[key] = char_data[key]
                    self.db.set_state('current_state', self.state)
                
                # ===== 收到 world_state 后立即决策 =====
                print(f"[{self.character_name}] 收到 world_state，进入下一轮决策...")
                world_state = {"tick": self.current_tick}
                action = self.decide_action(world_state)
                self.submit_action(action)
            
            elif data.get('type') == 'message':
                msg_data = data.get('data', {})
                msg_type = msg_data.get('type')
                
                if msg_type == 'game_start':
                    self.game_started = True
                    players = msg_data.get('players', [])
                    print(f"[{self.character_name}] 游戏开始! 当前玩家: {players}")
                    print(f"[{self.character_name}] channel_topic={self.channel_topic}")
                    # ===== 游戏开始后立即决策 =====
                    print(f"[{self.character_name}] 游戏开始，进入第一轮决策...")
                    world_state = {"tick": 0}
                    action = self.decide_action(world_state)
                    self.submit_action(action)
                    
                elif msg_type == 'you_are_kicked':
                    self.kicked = True
                    self.should_exit = True
                    print(f"[{self.character_name}] 被房主踢出")
                    
                elif msg_type == 'stop':
                    self.should_exit = True
                    print(f"[{self.character_name}] 收到停止指令")
                    
                elif msg_type == 'lobby_cancelled':
                    self.should_exit = True
                    print(f"[{self.character_name}] 大厅已取消")
                    
                elif msg_type == 'world_state':
                    # ===== 嵌套 world_state 处理 =====
                    print(f"[{self.character_name}] 收到嵌套 world_state")
                    state_data = msg_data.get('data', {})
                    self.current_tick = state_data.get('tick', -1)
                    if not self.channel_topic:
                        self.channel_topic = state_data.get('channel_topic')
                    
                    if not self.joined and self.channel_topic:
                        print(f"[{self.character_name}] 发送 subscribe, topic={self.channel_topic}")
                        ws_client.send(json.dumps({
                            "action": "subscribe",
                            "topic": self.channel_topic
                        }))
                        self.joined = True
                        print(f"[{self.character_name}] 加入世界成功 (频道 {self.channel_id})")
                        
                    chars = state_data.get('characters', {})
                    if self.character_id in chars:
                        char_data = chars[self.character_id]
                        for key in ['x', 'y', 'z', 'health', 'energy', 'mood', 'hunger']:
                            if key in char_data:
                                self.state[key] = char_data[key]
                        self.db.set_state('current_state', self.state)
                    
                    # ===== 收到 world_state 后立即决策 =====
                    print(f"[{self.character_name}] 收到 world_state，进入下一轮决策...")
                    world_state = {"tick": self.current_tick}
                    action = self.decide_action(world_state)
                    self.submit_action(action)
                
                elif msg_type == 'action_submitted':
                    print(f"[{self.character_name}] 收到 action_submitted (来自 {msg_data.get('character_id')})")
                    
        except Exception as e:
            print(f"[{self.character_name}] 消息处理错误: {e}")
    
    def on_open(self, ws_client):
        self.ws = ws_client
        self.ws_connected = True
        print(f"[{self.character_name}] WebSocket 已连接")
        
        ws_client.send(json.dumps({
            "action": "register",
            "role": "ego",
            "character_id": self.character_id,
            "character_name": self.character_name
        }))
        print(f"[{self.character_name}] 已发送 register")
        
        ws_client.send(json.dumps({
            "action": "join_world",
            "world_name": WORLD_NAME,
            "character_id": self.character_id,
            "character_name": self.character_name
        }))
        print(f"[{self.character_name}] 请求加入世界 (频道 {self.channel_id})")
        
    def on_error(self, ws_client, error):
        print(f"[{self.character_name}] WebSocket 错误: {error}")
        
    def on_close(self, ws_client, code, msg):
        self.ws_connected = False
        self.should_exit = True
        print(f"[{self.character_name}] WebSocket 连接关闭, code={code}, msg={msg}")
        # 关闭数据库长连接
        self.db._close_conn()

    # ==================== 决策 ====================
    
    def apply_physical_effects(self, world_state: Dict) -> Dict:
        weather = world_state.get('weather', 'clear')
        temperature = world_state.get('temperature', 25.0)
        
        effects = {}
        state_before = self.state.copy()
        
        if weather == 'rain':
            effects['mood'] = -3
            effects['energy'] = -1
        elif weather == 'storm':
            effects['mood'] = -5
            effects['energy'] = -2
            effects['health'] = -1
        elif weather == 'snow':
            effects['mood'] = -2
            effects['health'] = -1
        elif weather == 'fog':
            effects['mood'] = -1
        
        if temperature > 35:
            effects['health'] = -2
            effects['energy'] = -3
        elif temperature < 5:
            effects['health'] = -2
            effects['energy'] = -2
        
        effects['hunger'] = 1
        effects['energy'] = effects.get('energy', 0) - 1
        
        for key, delta in effects.items():
            if key in self.state:
                self.state[key] = max(0, min(100, self.state[key] + delta))
        
        self.db.set_state('current_state', self.state)
        
        return {
            'applied_effects': effects,
            'state_before': state_before,
            'state_after': self.state.copy()
        }
    
    def decide_action(self, world_state: Dict) -> Dict:
        self.tick_count += 1
        tick = world_state.get('tick', 0)
        
        active_goals = [g for g in self.current_goals if g.active]
        if active_goals:
            goal = max(active_goals, key=lambda g: g.priority)
        else:
            goal = Goal(
                type=GoalType.SURVIVAL,
                description="保持生存",
                priority=10,
                target_state={"health": 70, "hunger": 50}
            )
        
        action = self._generate_action(goal, tick)
        
        state_before = self.state.copy()
        for key in ['x', 'y', 'z', 'health', 'energy', 'mood', 'hunger']:
            if key in action and key in self.state:
                self.state[key] = action[key]
        self.db.set_state('current_state', self.state)
        self.db.add_action(tick, "move", action, state_before, self.state)
        
        if tick % 5 == 0:
            try:
                self.plan_input.put({
                    'type': 'goal_progress',
                    'goal_id': goal.id if hasattr(goal, 'id') else None,
                    'progress': goal.progress,
                    'state': self.state
                })
            except:
                pass
            
        if tick % 10 == 0:
            try:
                self.reflect_input.put({
                    'type': 'state_snapshot',
                    'state': self.state,
                    'action': action,
                    'tick': tick
                })
            except:
                pass
            
        return action
    
    def _generate_action(self, goal: Goal, tick: int) -> Dict:
        dx = random.randint(-30, 30)
        dy = random.randint(-30, 30)
        
        action_types = ['explore', 'gather', 'rest', 'move', 'idle']
        decision = random.choice(action_types)
        
        if goal.type == GoalType.SURVIVAL and self.state.get('hunger', 50) > 70:
            decision = 'gather'
            dx = random.randint(-40, 40)
            dy = random.randint(-40, 40)
        elif goal.type == GoalType.HEALTH and self.state.get('health', 80) < 60:
            decision = 'rest'
            dx = 0
            dy = 0
        
        actions = {
            'explore': {'dx': random.randint(-50, 50), 'dy': random.randint(-50, 50)},
            'gather': {'dx': random.randint(-30, 30), 'dy': random.randint(-30, 30)},
            'rest': {'dx': 0, 'dy': 0},
            'move': {'dx': random.randint(-20, 20), 'dy': random.randint(-20, 20)},
            'idle': {'dx': 0, 'dy': 0}
        }
        
        action_data = actions.get(decision, actions['idle'])
        
        new_x = max(10, min(990, self.state['x'] + action_data['dx']))
        new_y = max(10, min(790, self.state['y'] + action_data['dy']))
        
        health_delta = random.randint(-2, 2)
        energy_delta = -random.randint(1, 3)
        hunger_delta = random.randint(0, 2)
        mood_delta = random.randint(-2, 2)
        
        if decision == 'rest':
            health_delta += 2
            energy_delta += 3
            hunger_delta += 1
            mood_delta += 1
        elif decision == 'gather':
            health_delta -= 1
            energy_delta -= 3
            hunger_delta += 1
            mood_delta += 1
        
        # ===== 生成想法和说话 =====
        thought_text = ""
        speech_text = ""
        
        # 基于决策类型生成内容
        if decision == 'explore':
            thoughts = [
                "前面好像有什么东西...",
                "这边走看看，感觉有发现",
                "路在脚下，继续探索",
                "每走一步都是新的发现",
                "这片区域看起来很陌生"
            ]
            speeches = [
                "我去看看那边！",
                "这边好像有路！",
                "发现新地方了！",
                "继续往前走！",
                "那边好像有动静"
            ]
            thought_text = random.choice(thoughts)
            speech_text = random.choice(speeches)
            
        elif decision == 'gather':
            thoughts = [
                "附近有资源，收集一下",
                "这些东西有用",
                "多收集点材料",
                "资源不能浪费",
                "这里东西不少"
            ]
            speeches = [
                "我收集点东西",
                "这个有用，拿着",
                "材料够了！",
                "收获不错",
                "多拿点回去"
            ]
            thought_text = random.choice(thoughts)
            speech_text = random.choice(speeches)
            
        elif decision == 'rest':
            thoughts = [
                "好累啊，休息一下",
                "恢复体力很重要",
                "歇会儿再走",
                "躺一会儿...",
                "终于可以休息了"
            ]
            speeches = [
                "歇会儿",
                "休息一下",
                "喘口气",
                "好累...",
                "先歇歇"
            ]
            thought_text = random.choice(thoughts)
            speech_text = random.choice(speeches)
            
        elif decision == 'move':
            thoughts = [
                "继续前进",
                "路还长着呢",
                "往前走",
                "换个地方看看",
                "一直走"
            ]
            speeches = [
                "走了！",
                "继续走",
                "出发",
                "前进！",
                "上路了"
            ]
            thought_text = random.choice(thoughts)
            speech_text = random.choice(speeches)
            
        elif decision == 'idle':
            thoughts = [
                "发呆中...",
                "在想什么呢",
                "今天天气不错",
                "风吹着挺舒服",
                "肚子饿了..."
            ]
            speeches = [
                "...",
                "嗯...",
                "好无聊",
                "发会呆",
                "想什么呢"
            ]
            thought_text = random.choice(thoughts)
            speech_text = random.choice(speeches)
        
        # 偶尔加入反思内容
        if self.thought and time.time() < self.thought_timer:
            thought_text = self.thought
        else:
            self.thought = ""
        
        if self.speech and time.time() < self.speech_timer:
            speech_text = self.speech
        else:
            self.speech = ""
        
        return {
            'x': new_x,
            'y': new_y,
            'z': 0,
            'health': max(0, min(100, self.state['health'] + health_delta)),
            'energy': max(0, min(100, self.state['energy'] + energy_delta)),
            'hunger': max(0, min(100, self.state['hunger'] + hunger_delta)),
            'mood': max(0, min(100, self.state['mood'] + mood_delta)),
            'decision': decision,
            'target_x': new_x + random.randint(-20, 20),
            'target_y': new_y + random.randint(-20, 20),
            'reason': f"执行 {decision} 行为",
            'goal': goal.description,
            'thought': thought_text,
            'speech': speech_text,
            'state_delta': {
                'health': health_delta,
                'energy': energy_delta,
                'hunger': hunger_delta,
                'mood': mood_delta
            }
        }
    
    def submit_action(self, action: Dict, is_idle: bool = False):
        print(f"[{self.character_name}] submit_action: ws_connected={self.ws_connected}, ws={self.ws is not None}, channel_topic={self.channel_topic}")
        
        if not self.ws_connected or not self.ws:
            print(f"[{self.character_name}] 无法发送: ws_connected={self.ws_connected}, ws={self.ws is not None}")
            return False
        
        if not self.channel_topic:
            print(f"[{self.character_name}] channel_topic 为空，无法发送")
            return False
        
        try:
            data = {
                "action": "publish",
                "topic": self.channel_topic,
                "data": {
                    "type": "action_submitted",
                    "character_id": self.character_id,
                    "character_name": self.character_name,
                    "action": action,
                    "is_idle": is_idle
                }
            }
            self.ws.send(json.dumps(data))
            print(f"[{self.character_name}] 已发送 action (tick {self.current_tick})")
            return True
        except Exception as e:
            print(f"[{self.character_name}] 上报失败: {e}")
            return False

# ==================== 进程2: 规划进程 (独立运行) ====================

def _run_plan_process(char_id, char_name, db_path, input_queue, output_queue):
    """规划进程入口函数 (在子进程中运行)"""
    db = CharacterDB(db_path)
    planner = EgoPlanProcess(char_id, char_name, db)
    planner.run(input_queue, output_queue)

class EgoPlanProcess:
    def __init__(self, character_id: str, character_name: str, db: CharacterDB):
        self.character_id = character_id
        self.character_name = character_name
        self.db = db
        
        self.goal_templates = [
            {"type": GoalType.SURVIVAL, "description": "建造庇护所", "priority": 8},
            {"type": GoalType.EXPLORATION, "description": "探索岛屿森林", "priority": 6},
            {"type": GoalType.BUILDING, "description": "制作工具", "priority": 7},
            {"type": GoalType.RESOURCE, "description": "寻找水源", "priority": 9},
            {"type": GoalType.HEALTH, "description": "恢复健康状态", "priority": 7},
            {"type": GoalType.EXPLORATION, "description": "探索海岸线", "priority": 5},
            {"type": GoalType.BUILDING, "description": "建造火堆", "priority": 6},
        ]
        
    def run(self, input_queue: mp.Queue, output_queue: mp.Queue):
        print(f"[Plan-{self.character_name}] 规划进程启动")
        
        while True:
            try:
                msg = input_queue.get(timeout=10.0)
                self._process_feedback(msg)
            except queue.Empty:
                self._generate_goals(output_queue)
                
    def _process_feedback(self, msg: Dict):
        if msg.get('type') == 'goal_progress':
            goal_id = msg.get('goal_id')
            progress = msg.get('progress', 0)
            if goal_id:
                self.db.update_goal_progress(goal_id, progress)
                if progress >= 1.0:
                    self.db.complete_goal(goal_id)
                    print(f"[Plan-{self.character_name}] 目标完成!")
                    
    def _generate_goals(self, output_queue: mp.Queue):
        if random.random() < 0.08:
            template = random.choice(self.goal_templates)
            output_queue.put({
                'type': 'new_goal',
                'data': {
                    'type': template['type'].value,
                    'description': template['description'],
                    'priority': template['priority'] + random.randint(-1, 2),
                    'target_state': {"status": "pending", "created_at": time.time()}
                }
            })

# ==================== 进程3: 反思进程 (独立运行) ====================

def _run_reflect_process(char_id, char_name, db_path, input_queue, output_queue):
    """反思进程入口函数 (在子进程中运行)"""
    db = CharacterDB(db_path)
    reflector = EgoReflectProcess(char_id, char_name, db)
    reflector.run(input_queue, output_queue)

class EgoReflectProcess:
    def __init__(self, character_id: str, character_name: str, db: CharacterDB):
        self.character_id = character_id
        self.character_name = character_name
        self.db = db
        self.action_buffer: List[Dict] = []
        
    def run(self, input_queue: mp.Queue, output_queue: mp.Queue):
        print(f"[Reflect-{self.character_name}] 反思进程启动")
        
        while True:
            try:
                msg = input_queue.get(timeout=15.0)
                self._record_experience(msg)
                
                if len(self.action_buffer) >= 10:
                    memory = self._reflect()
                    if memory:
                        output_queue.put({
                            'type': 'memory',
                            'data': asdict(memory)
                        })
                        self.action_buffer = []
                        
            except queue.Empty:
                if self.action_buffer:
                    memory = self._reflect()
                    if memory:
                        output_queue.put({
                            'type': 'memory',
                            'data': asdict(memory)
                        })
                        self.action_buffer = []
                        
    def _record_experience(self, msg: Dict):
        if msg.get('type') == 'state_snapshot':
            self.action_buffer.append({
                'state': msg.get('state', {}),
                'action': msg.get('action', {}),
                'tick': msg.get('tick', 0)
            })
            
    def _reflect(self) -> Optional[Memory]:
        if not self.action_buffer:
            return None
            
        states = [a['state'] for a in self.action_buffer]
        actions = [a['action'] for a in self.action_buffer]
        
        avg_hunger = sum(s.get('hunger', 50) for s in states) / len(states)
        avg_health = sum(s.get('health', 80) for s in states) / len(states)
        avg_energy = sum(s.get('energy', 70) for s in states) / len(states)
        avg_mood = sum(s.get('mood', 60) for s in states) / len(states)
        
        decisions = [a.get('decision', 'idle') for a in actions]
        decision_counts = {}
        for d in decisions:
            decision_counts[d] = decision_counts.get(d, 0) + 1
        most_common_decision = max(decision_counts, key=decision_counts.get) if decision_counts else 'idle'
        
        if avg_hunger > 70:
            return Memory(
                event="饥饿状态持续",
                importance=0.8,
                emotion="焦虑",
                lesson="需要更积极地寻找食物",
                context={"avg_hunger": avg_hunger, "most_common_action": most_common_decision}
            )
        elif avg_health < 60:
            return Memory(
                event="健康状况下降",
                importance=0.9,
                emotion="担忧",
                lesson="应该优先恢复健康",
                context={"avg_health": avg_health, "avg_energy": avg_energy}
            )
        elif avg_energy < 40:
            return Memory(
                event="精力严重不足",
                importance=0.7,
                emotion="疲惫",
                lesson="需要更多休息",
                context={"avg_energy": avg_energy}
            )
        elif avg_mood < 40:
            return Memory(
                event="情绪低落",
                importance=0.6,
                emotion="沮丧",
                lesson="需要做一些愉快的事情",
                context={"avg_mood": avg_mood}
            )
        elif most_common_decision == 'explore' and len(self.action_buffer) > 5:
            return Memory(
                event="探索行为频繁",
                importance=0.5,
                emotion="好奇",
                lesson="正在熟悉环境",
                context={"exploration_count": decision_counts.get('explore', 0)}
            )
            
        return None

# ==================== 主入口 ====================

if __name__ == "__main__":
    if len(sys.argv) < 7:
        print("用法: python ego.py <world_name> <character_id> <character_name> <ws_host> <ws_port> <channel_id>")
        print("示例: python ego.py 荒岛求生 robinson 鲁滨逊 127.0.0.1 8765 0")
        sys.exit(1)
    
    WORLD_NAME = sys.argv[1]
    CHARACTER_ID = sys.argv[2]
    CHARACTER_NAME = sys.argv[3]
    WS_HOST = sys.argv[4]
    WS_PORT = int(sys.argv[5])
    CHANNEL_ID = int(sys.argv[6])
    
    print("=" * 60)
    print("Ego AI 系统启动")
    print(f"   角色: {CHARACTER_NAME} ({CHARACTER_ID})")
    print(f"   世界: {WORLD_NAME}")
    print(f"   频道: {CHANNEL_ID}")
    print(f"   数据库: {DB_PATH}")
    print("=" * 60)
    
    ego = EgoMainProcess(
        CHARACTER_ID, CHARACTER_NAME,
        WS_HOST, WS_PORT, CHANNEL_ID,
        DB_PATH
    )
    
    import websocket
    WS_URL = f"ws://{WS_HOST}:{WS_PORT}"
    
    ws_client = websocket.WebSocketApp(
        WS_URL,
        on_open=ego.on_open,
        on_message=ego.on_message,
        on_error=ego.on_error,
        on_close=ego.on_close
    )
    
    # 阻塞主线程，所有消息在 on_message 中同步处理
    ws_client.run_forever()
    
    # 关闭数据库长连接
    ego.db._close_conn()
    print(f"[{CHARACTER_NAME}] 退出")