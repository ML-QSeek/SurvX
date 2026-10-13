#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
世界进程 - 计算世界状态 (天气、时间、环境)
单进程，操作世界数据库
消息驱动模式 - 收到所有 ego 的 action 后才计算一个 tick

使用方式:
  python field.py <world_name> <ws_host> <ws_port>
  例: python field.py 荒岛求生 127.0.0.1 8765
"""

import sys
import time
import json
import random
import sqlite3
import os
from datetime import datetime
import websocket

# ==================== 日志重定向 ====================

LOG_FILE_PATH = None

def setup_logging(world_name: str):
    """将 print 输出重定向到文件"""
    global LOG_FILE_PATH
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(script_dir, "..", "..", "logs", world_name)
        os.makedirs(log_dir, exist_ok=True)
        LOG_FILE_PATH = os.path.join(log_dir, f"field_{world_name}.log")
        
        log_file = open(LOG_FILE_PATH, 'a', encoding='utf-8')
        
        log_file.write("\n" + "=" * 60 + "\n")
        log_file.write(f"Field 启动: {world_name}\n")
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
        
        print(f"[世界] 日志文件: {LOG_FILE_PATH}")
        return LOG_FILE_PATH
    except Exception as e:
        print(f"[世界] 日志设置失败: {e}")
        return None

# ==================== 参数解析 ====================

WORLD_NAME = sys.argv[1] if len(sys.argv) > 1 else "荒岛求生"
WS_HOST = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
WS_PORT = int(sys.argv[3]) if len(sys.argv) > 3 else 8765

setup_logging(WORLD_NAME)

# 自动扫描 db 路径
INSTANCE_DIR = f"../data/instance/{WORLD_NAME}"
DB_PATH = None
if os.path.exists(INSTANCE_DIR):
    for f in os.listdir(INSTANCE_DIR):
        if f.startswith('field_') and f.endswith('.db'):
            DB_PATH = os.path.join(INSTANCE_DIR, f)
            break

if DB_PATH is None:
    print(f"[世界] 错误: 找不到 field_*.db 文件在 {INSTANCE_DIR}")
    sys.exit(1)

WS_URL = f"ws://{WS_HOST}:{WS_PORT}"

# ==================== 数据库管理 ====================

class WorldDB:
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
            CREATE TABLE IF NOT EXISTS world_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                tick INTEGER DEFAULT 0,
                time_of_day TEXT DEFAULT 'day',
                weather TEXT DEFAULT 'clear',
                intensity REAL DEFAULT 0.0,
                temperature REAL DEFAULT 25.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT OR IGNORE INTO world_state (id, tick, time_of_day, weather, intensity, temperature)
            VALUES (1, 0, 'day', 'clear', 0.0, 25.0)
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS characters (
                character_id TEXT PRIMARY KEY,
                name TEXT,
                icon TEXT DEFAULT 'user',
                x REAL DEFAULT 500,
                y REAL DEFAULT 400,
                z REAL DEFAULT 0,
                health REAL DEFAULT 85,
                energy REAL DEFAULT 70,
                mood REAL DEFAULT 60,
                hunger REAL DEFAULT 50,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                online INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS world_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER,
                event_type TEXT,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS weather_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tick INTEGER,
                time_of_day TEXT,
                weather TEXT,
                intensity REAL,
                temperature REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
    
    def get_world_state(self) -> dict:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tick, time_of_day, weather, intensity, temperature
            FROM world_state WHERE id = 1
        ''')
        row = cursor.fetchone()
        if row:
            return {
                'tick': row[0],
                'timeOfDay': row[1],
                'weather': row[2],
                'intensity': row[3],
                'temperature': row[4]
            }
        return {'tick': 0, 'timeOfDay': 'day', 'weather': 'clear', 'intensity': 0, 'temperature': 25.0}
    
    def update_world_state(self, tick: int, time_of_day: str, weather: str, intensity: float, temperature: float):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE world_state 
            SET tick = ?, time_of_day = ?, weather = ?, intensity = ?, temperature = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        ''', (tick, time_of_day, weather, intensity, temperature))
        conn.commit()
    
    def add_character(self, character_id: str, name: str, icon: str = 'user'):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO characters 
            (character_id, name, icon, joined_at, last_active, online)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
        ''', (character_id, name, icon))
        conn.commit()
    
    def remove_character(self, character_id: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('UPDATE characters SET online = 0, last_active = CURRENT_TIMESTAMP WHERE character_id = ?', (character_id,))
        conn.commit()
    
    def delete_character(self, character_id: str):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM characters WHERE character_id = ?', (character_id,))
        conn.commit()
    
    def update_character_state(self, character_id: str, state: dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE characters 
            SET x = ?, y = ?, z = ?, 
                health = ?, energy = ?, mood = ?, hunger = ?,
                last_active = CURRENT_TIMESTAMP,
                online = 1
            WHERE character_id = ?
        ''', (
            state.get('x', 500),
            state.get('y', 400),
            state.get('z', 0),
            state.get('health', 85),
            state.get('energy', 70),
            state.get('mood', 60),
            state.get('hunger', 50),
            character_id
        ))
        conn.commit()
    
    def get_all_characters(self) -> dict:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT character_id, name, icon, x, y, z, health, energy, mood, hunger, online
            FROM characters
        ''')
        result = {}
        for row in cursor.fetchall():
            result[row[0]] = {
                'name': row[1],
                'icon': row[2] or 'user',
                'x': row[3],
                'y': row[4],
                'z': row[5],
                'health': row[6],
                'energy': row[7],
                'mood': row[8],
                'hunger': row[9],
                'online': row[10] == 1
            }
        return result
    
    def get_character(self, character_id: str) -> dict:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name, icon, x, y, z, health, energy, mood, hunger, online
            FROM characters WHERE character_id = ?
        ''', (character_id,))
        row = cursor.fetchone()
        if row:
            return {
                'name': row[0],
                'icon': row[1] or 'user',
                'x': row[2],
                'y': row[3],
                'z': row[4],
                'health': row[5],
                'energy': row[6],
                'mood': row[7],
                'hunger': row[8],
                'online': row[9] == 1
            }
        return None
    
    def add_log(self, tick: int, event_type: str, event_data: dict):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO world_logs (tick, event_type, event_data)
            VALUES (?, ?, ?)
        ''', (tick, event_type, json.dumps(event_data)))
        conn.commit()
    
    def add_weather_record(self, tick: int, time_of_day: str, weather: str, intensity: float, temperature: float):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO weather_history (tick, time_of_day, weather, intensity, temperature)
            VALUES (?, ?, ?, ?, ?)
        ''', (tick, time_of_day, weather, intensity, temperature))
        conn.commit()

# ==================== 全局变量 ====================

db = WorldDB(DB_PATH)

WORLD_ID = None
channel_id = -1
channel_topic = None

world_state = db.get_world_state()
world_state['characters'] = db.get_all_characters()

characters = {cid: info for cid, info in world_state['characters'].items() if info.get('online', False)}
pending_actions = {}
action_timeout = {}

TIMES = ["day", "dusk", "night", "dawn"]
WEATHERS = ["clear", "clear", "clear", "rain", "rain", "snow", "storm", "fog", "windy"]

ws = None
ws_connected = False
world_created = False
game_started = False
ready_sent = False
running = False

MAX_TIMEOUT_COUNT = 3
TICK_INTERVAL = 5.0

# ==================== 消息处理 ====================

def delete_world():
    if ws_connected and ws and channel_id >= 0:
        try:
            ws.send(json.dumps({
                "action": "delete_world",
                "channel_id": channel_id
            }))
            print(f"[世界] 请求删除世界: {WORLD_NAME} (频道 {channel_id})")
        except:
            pass

def stop_instance():
    if ws_connected and ws and channel_id >= 0:
        try:
            ws.send(json.dumps({
                "action": "stop_instance",
                "instance": WORLD_NAME
            }))
            print(f"[世界] 请求停止实例: {WORLD_NAME}")
        except:
            pass

def get_active_players() -> list:
    active = []
    for char_id, info in characters.items():
        if info.get('online', False):
            active.append(char_id)
    return active

def calculate_environment(tick: int) -> dict:
    time_index = (tick // 10) % len(TIMES)
    time_of_day = TIMES[time_index]
    
    if tick % 30 == 0:
        weather = random.choice(WEATHERS)
        intensity = round(random.random() * 0.8 + 0.2, 2)
        temperature = round(20 + random.random() * 15 - 5, 1)
    else:
        weather = world_state.get("weather", "clear")
        intensity = world_state.get("intensity", 0)
        temperature = world_state.get("temperature", 25.0)
    
    
    return {
        "timeOfDay": time_of_day,
        "weather": weather,
        "intensity": intensity,
        "temperature": temperature
    }

def apply_actions(actions: dict) -> dict:
    updated = {}
    for char_id, action in actions.items():
        char_data = db.get_character(char_id)
        if char_data:
            new_state = {
                'x': action.get('x', char_data.get('x', 500)),
                'y': action.get('y', char_data.get('y', 400)),
                'z': action.get('z', char_data.get('z', 0)),
                'health': action.get('health', char_data.get('health', 85)),
                'energy': action.get('energy', char_data.get('energy', 70)),
                'mood': action.get('mood', char_data.get('mood', 60)),
                'hunger': action.get('hunger', char_data.get('hunger', 50)),
                'online': True
            }
            new_state['x'] = max(10, min(990, new_state['x']))
            new_state['y'] = max(10, min(790, new_state['y']))
            
            db.update_character_state(char_id, new_state)
            updated[char_id] = db.get_character(char_id)
    
    world_state['characters'] = db.get_all_characters()
    return updated

def broadcast_world_state(tick: int):
    print(f"[世界] 广播 world_state, tick={tick}")
    if not ws_connected or not ws or not world_created or not channel_topic:
        return
    
    try:
        characters_data = {}
        for char_id, info in characters.items():
            if info.get('online', False):
                characters_data[char_id] = {
                    'name': info.get('name', char_id),
                    'icon': info.get('icon', 'user'),
                    'x': info.get('x', 500),
                    'y': info.get('y', 400),
                    'z': info.get('z', 0),
                    'health': info.get('health', 85),
                    'energy': info.get('energy', 70),
                    'mood': info.get('mood', 60),
                    'hunger': info.get('hunger', 50)
                }
        
        ws.send(json.dumps({
            "action": "publish",
            "topic": channel_topic,
            "data": {
                "type": "world_state",
                "data": {
                    "tick": tick,
                    "timeOfDay": world_state.get('timeOfDay', 'day'),
                    "weather": world_state.get('weather', 'clear'),
                    "intensity": world_state.get('intensity', 0),
                    "temperature": world_state.get('temperature', 25.0),
                    "timestamp": time.time(),
                    "characters": characters_data,
                    "active_count": len(characters_data)
                }
            }
        }))
    except Exception as e:
        print(f"[世界] 广播 world_state 失败: {e}")

def format_state() -> str:
    chars_str = ", ".join([
        f"{cid}({info.get('x', 0):.1f},{info.get('y', 0):.1f})"
        for cid, info in characters.items() if info.get('online', False)
    ])
    return f"[tick {world_state['tick']}] {world_state['timeOfDay']} {world_state['weather']} {world_state['temperature']:.1f}C 人物: {chars_str if chars_str else '无'}"

def process_tick():
    """处理一个 tick：计算环境、应用 action、广播世界状态"""
    global world_state
    
    tick = world_state.get('tick', 0) + 1
    
    # 计算环境
    env = calculate_environment(tick)
    
    world_state['tick'] = tick
    world_state['timeOfDay'] = env['timeOfDay']
    world_state['weather'] = env['weather']
    world_state['intensity'] = env['intensity']
    world_state['temperature'] = env['temperature']
    
    # 更新数据库
    db.update_world_state(tick, env['timeOfDay'], env['weather'], env['intensity'], env['temperature'])
    
    db.add_weather_record(tick, env['timeOfDay'], env['weather'], env['intensity'], env['temperature'])
    
    # 应用 action
    if pending_actions:
        apply_actions(pending_actions)
        print(f"[世界] tick {tick} 应用了 {len(pending_actions)} 个 action")
    
    # 广播
    broadcast_world_state(tick)
    
    # 打印状态
    active_players = get_active_players()
    if len(active_players) > 0:
        print(f"   {format_state()}")
    else:
        print(f"   {format_state()} (等待人物加入...)")
    
    # 写日志
    db.add_log(tick, 'tick_complete', {
        'characters_count': len(active_players),
        'actions_count': len(pending_actions),
        'weather': env['weather'],
        'temperature': env['temperature']
    })
    
    # 清空 pending_actions，准备下一轮
    pending_actions.clear()

def handle_action_submitted(char_id: str, action: dict):
    """处理 action_submitted 消息"""
    global pending_actions
    
    if char_id not in characters:
        print(f"[世界] 未知角色: {char_id}")
        return
    
    print(f"[action_submitted] ✅ {char_id} -> ({action.get('x')}, {action.get('y')})")
    
    # 更新角色数据
    characters[char_id]['x'] = action.get('x', characters[char_id].get('x', 500))
    characters[char_id]['y'] = action.get('y', characters[char_id].get('y', 400))
    characters[char_id]['z'] = action.get('z', characters[char_id].get('z', 0))
    characters[char_id]['health'] = action.get('health', characters[char_id].get('health', 85))
    characters[char_id]['energy'] = action.get('energy', characters[char_id].get('energy', 70))
    characters[char_id]['mood'] = action.get('mood', characters[char_id].get('mood', 60))
    characters[char_id]['hunger'] = action.get('hunger', characters[char_id].get('hunger', 50))
    
    characters[char_id]['x'] = max(10, min(990, characters[char_id]['x']))
    characters[char_id]['y'] = max(10, min(790, characters[char_id]['y']))
    
    db.update_character_state(char_id, characters[char_id])
    
    # 存入 pending_actions
    pending_actions[char_id] = action
    action_timeout[char_id] = 0

def on_message(ws_client, message):
    global ws_connected, WORLD_ID, channel_id, channel_topic, world_created
    global game_started, running, ready_sent, characters, world_state
    
    try:
        data = json.loads(message)
        msg_type = data.get('type')
        
        # 直接类型的消息
        if msg_type == 'world_created':
            world_data = data.get('data', {})
            channel_id = world_data.get('channel_id', -1)
            world_info = world_data.get('world', {})
            channel_topic = world_data.get('channel_topic')
            WORLD_ID = world_info.get('id')
            
            if WORLD_ID and channel_topic and channel_id >= 0:
                world_created = True
                
                ws.send(json.dumps({
                    "action": "subscribe",
                    "topic": channel_topic
                }))
                print(f"[世界] 世界创建成功: {WORLD_NAME} (频道 {channel_id})")
                print(f"[世界] 订阅频道: {channel_topic}")
                
                result = {
                    "status": "success",
                    "world_name": WORLD_NAME,
                    "channel_id": channel_id,
                    "ws_url": WS_URL,
                    "world_id": WORLD_ID
                }
                print(f"[RESULT] {json.dumps(result)}")
                sys.stdout.flush()
                
                if not ready_sent:
                    ws.send(json.dumps({
                        "action": "ready",
                        "instance": WORLD_NAME,
                        "role": "field",
                        "channel_id": channel_id,
                        "world_name": WORLD_NAME
                    }))
                    ready_sent = True
                    print(f"[世界] 已发送 ready field 到 server")
            else:
                print(f"[世界] 世界创建失败")
            return
        
        if msg_type == 'error':
            error_msg = data.get('message', '未知错误')
            print(f"[世界] 错误: {error_msg}")
            if "已存在" in error_msg or "没有空闲" in error_msg:
                result = {
                    "status": "failed",
                    "world_name": WORLD_NAME,
                    "error": error_msg
                }
                print(f"[RESULT] {json.dumps(result)}")
                sys.stdout.flush()
                ws_client.close()
            return
        
        if msg_type == 'subscribed':
            print(f"[世界] 订阅成功: {data.get('topic')}")
            return
        
        # 嵌套消息 (type == 'message')
        if msg_type == 'message':
            msg_data = data.get('data', {})
            inner_type = msg_data.get('type')
            
            if inner_type == 'game_start':
                game_started = True
                running = True
                players = msg_data.get('players', [])
                
                for player_id in players:
                    if player_id not in characters:
                        char_data = db.get_character(player_id)
                        if char_data:
                            characters[player_id] = char_data
                        else:
                            icon = 'user'
                            db.add_character(player_id, player_id, icon)
                            characters[player_id] = {
                                'name': player_id,
                                'icon': icon,
                                'x': random.randint(100, 900),
                                'y': random.randint(100, 700),
                                'z': 0,
                                'health': 85,
                                'energy': 70,
                                'mood': 60,
                                'hunger': 50,
                                'online': True
                            }
                            db.update_character_state(player_id, characters[player_id])
                
                world_state['characters'] = db.get_all_characters()
                print(f"[世界] 收到 GAME_START，开始运行! 玩家: {players}")
                print(f"[世界] 等待 ego 上报 action...")
                return
            
            if inner_type == 'lobby_cancelled':
                print(f"[世界] 收到取消指令，退出进程")
                running = False
                delete_world()
                sys.exit(0)
                return
            
            if inner_type == 'stop':
                print(f"[世界] 收到停止指令，退出进程")
                running = False
                delete_world()
                sys.exit(0)
                return
            
            if inner_type == 'character_joined':
                char_id = msg_data.get('character_id')
                char_name = msg_data.get('character_name', char_id)
                char_icon = msg_data.get('icon', 'user')
                
                if char_id not in characters:
                    db.add_character(char_id, char_name, char_icon)
                    init_state = {
                        'x': random.randint(100, 900),
                        'y': random.randint(100, 700),
                        'z': 0,
                        'health': 85,
                        'energy': 70,
                        'mood': 60,
                        'hunger': 50,
                        'online': True
                    }
                    db.update_character_state(char_id, init_state)
                    characters[char_id] = db.get_character(char_id)
                    world_state['characters'] = db.get_all_characters()
                    print(f"[世界] 人物加入: {char_name} ({char_id})")
                    db.add_log(world_state.get('tick', 0), 'character_joined', 
                              {'character_id': char_id, 'name': char_name, 'icon': char_icon})
                    action_timeout.pop(char_id, None)
                return
            
            if inner_type == 'character_left':
                char_id = msg_data.get('character_id')
                if char_id in characters:
                    char_name = characters[char_id].get('name', char_id)
                    db.remove_character(char_id)
                    del characters[char_id]
                    world_state['characters'] = db.get_all_characters()
                    pending_actions.pop(char_id, None)
                    action_timeout.pop(char_id, None)
                    print(f"[世界] 人物离开: {char_name} ({char_id})")
                    db.add_log(world_state.get('tick', 0), 'character_left',
                              {'character_id': char_id, 'name': char_name})
                return
            
            if inner_type == 'action_submitted':
                char_id = msg_data.get('character_id')
                action = msg_data.get('action', {})
                handle_action_submitted(char_id, action)
                
                # 检查是否所有活跃玩家都已上报
                active_players = get_active_players()
                if len(active_players) > 0 and len(pending_actions) >= len(active_players):
                    print(f"[世界] 所有 ego 已上报，开始计算 tick...")
                    if len(active_players) > 0 and len(pending_actions) >= len(active_players):
                        print(f"[世界] 所有 ego 已上报，开始计算 tick...")
                        print(f"[世界] 准备调用 process_tick, pending={len(pending_actions)}, active={len(active_players)}", flush=True)
                    process_tick()
                else:
                    print(f"[世界] 已收到 {len(pending_actions)}/{len(active_players)} 个 ego 上报，继续等待...")
                return
            
            # 其他嵌套消息类型，忽略
            return
        
        # 其他消息类型，忽略
        
    except Exception as e:
        print(f"[世界] 消息处理错误: {e}")
        import traceback
        traceback.print_exc()

def on_error(ws_client, error):
    print(f"[世界] WebSocket 错误: {error}")

def on_close(ws_client, close_status_code, close_msg):
    global ws_connected, running
    ws_connected = False
    running = False
    delete_world()
    print(f"[世界] WebSocket 连接关闭, code={close_status_code}, msg={close_msg}")

def on_open(ws_client):
    global ws, ws_connected
    ws = ws_client
    ws_connected = True
    print(f"[世界] WebSocket 已连接: {WS_URL}")
    
    ws.send(json.dumps({
        "action": "register",
        "role": "field",
        "character_id": f"field_{WORLD_NAME}",
        "character_name": f"房主_{WORLD_NAME}"
    }))
    
    ws.send(json.dumps({
        "action": "create_world",
        "name": WORLD_NAME,
        "template": "island"
    }))
    print(f"[世界] 请求创建世界: {WORLD_NAME}")

# ==================== 主函数 ====================

def main():
    global ws, ws_connected, world_created, game_started, running
    
    print("=" * 60)
    print("SurvX 世界进程启动 (消息驱动模式)")
    print(f"   世界名: {WORLD_NAME}")
    print(f"   WebSocket: {WS_URL}")
    print(f"   数据库: {DB_PATH}")
    print("=" * 60)
    
    # 使用同步 WebSocket
    websocket.enableTrace(False)
    ws_client = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # WebSocketApp 内部会开一个线程，但 on_message 是同步处理的
    # 我们使用 run_forever 阻塞主线程，所有消息在同一个线程处理
    ws_client.run_forever()
    
    # 如果 run_forever 退出，清理
    if running:
        running = False
        delete_world()
    
    # 关闭数据库长连接
    db._close_conn()
    print("[世界] 进程退出")

if __name__ == "__main__":
    main()