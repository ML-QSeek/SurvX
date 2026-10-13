#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import asyncio
import logging
import threading
import time
import uuid
import sys
import os
import re
import sqlite3
import glob
from queue import Queue, Empty
from typing import Dict, Set, Any, Optional, List
from dataclasses import dataclass, field

from aiohttp import web

# ==================== 日志重定向 ====================

def setup_file_logging():
    """将 logging 输出同时写入文件"""
    try:
        # 获取当前文件所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # 相对路径: ../../logs/
        log_dir = os.path.join(script_dir, "..", "..", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "server.log")
        
        # 配置 logging
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
        
        # 获取 root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # 也处理 aiohttp 的日志
        aiohttp_logger = logging.getLogger('aiohttp')
        aiohttp_logger.setLevel(logging.WARNING)
        aiohttp_logger.addHandler(file_handler)
        
        print(f"[服务器] 日志文件: {log_path}")
        return log_path
    except Exception as e:
        print(f"[服务器] 日志设置失败: {e}")
        return None

# 设置日志（在模块加载时执行）
LOG_FILE_PATH = setup_file_logging()
logger = logging.getLogger(__name__)

# ==================== 原有代码 ====================

@dataclass
class World:
    id: str
    name: str
    template: str = 'island'
    status: str = 'created'
    config: Dict = field(default_factory=dict)
    state: Dict = field(default_factory=dict)


@dataclass
class CharacterInfo:
    id: str
    name: str
    icon: str = 'user'
    channel_id: int = -1
    role: str = 'ego'


@dataclass
class Channel:
    id: int
    world: Optional[World] = None
    characters: Dict[str, CharacterInfo] = field(default_factory=dict)
    max_characters: int = 5
    is_ready: bool = False
    field_connection_id: Optional[str] = None
    game_started: bool = False
    locked: bool = False

    def has_world(self) -> bool:
        return self.world is not None and self.is_ready

    def has_world_created(self) -> bool:
        return self.world is not None

    def is_full(self) -> bool:
        return len(self.characters) >= self.max_characters

    def is_empty(self) -> bool:
        return len(self.characters) == 0

    def has_field(self) -> bool:
        return self.field_connection_id is not None

    def is_locked(self) -> bool:
        return self.locked or self.game_started

    def add_character(self, character: CharacterInfo) -> bool:
        if self.is_full():
            return False
        if character.id in self.characters:
            return False
        self.characters[character.id] = character
        character.channel_id = self.id
        if character.role == 'field':
            self.field_connection_id = character.id
        return True

    def remove_character(self, character_id: str) -> bool:
        if character_id not in self.characters:
            return False
        character = self.characters[character_id]
        if character.role == 'field':
            self.field_connection_id = None
        del self.characters[character_id]
        return True

    def get_field(self) -> Optional[CharacterInfo]:
        for char in self.characters.values():
            if char.role == 'field':
                return char
        return None

    def create_world(self, name: str, template: str = 'island') -> World:
        if self.has_world_created():
            raise ValueError(f"频道 {self.id} 已有世界")
        world_id = f"world_{uuid.uuid4().hex[:8]}"
        self.world = World(id=world_id, name=name, template=template, status='created')
        self.is_ready = False
        self.game_started = False
        self.locked = False
        return self.world

    def delete_world(self):
        self.world = None
        self.characters.clear()
        self.is_ready = False
        self.field_connection_id = None
        self.game_started = False
        self.locked = False

    def set_ready(self, ready: bool = True):
        self.is_ready = ready
        if ready:
            logger.info(f"[频道 {self.id}] 已就绪")
        else:
            logger.info(f"[频道 {self.id}] 未就绪")

    def set_game_started(self, started: bool = True):
        self.game_started = started
        if started:
            self.locked = True
            logger.info(f"[频道 {self.id}] 游戏已开始，频道锁定")
        else:
            self.locked = False
            logger.info(f"[频道 {self.id}] 游戏未开始，频道解锁")

    def to_dict(self) -> Dict:
        return {
            'channel_id': self.id,
            'has_world': self.has_world(),
            'world': {
                'id': self.world.id,
                'name': self.world.name,
                'template': self.world.template,
                'status': self.world.status
            } if self.has_world_created() else None,
            'characters': [
                {'id': c.id, 'name': c.name, 'icon': c.icon, 'role': c.role}
                for c in self.characters.values()
            ],
            'character_count': len(self.characters),
            'max_characters': self.max_characters,
            'has_field': self.has_field(),
            'is_ready': self.is_ready,
            'game_started': self.game_started,
            'locked': self.locked
        }

    def get_channel_topic(self) -> str:
        return f"/channel/{self.id}"


class MessageQueue:
    def __init__(self, maxsize: int = 1000):
        self._queue = Queue(maxsize=maxsize)
        self._subscribers: Dict[str, Set[str]] = {}
        self._callbacks: Dict[str, callable] = {}

    def publish(self, topic: str, message: Any):
        try:
            self._queue.put_nowait({
                'topic': topic,
                'data': message,
                'timestamp': time.time()
            })
        except:
            logger.warning(f"队列已满，丢弃消息: {topic}")

    def subscribe(self, topic: str, subscriber_id: str, callback: callable):
        if topic not in self._subscribers:
            self._subscribers[topic] = set()
        self._subscribers[topic].add(subscriber_id)
        self._callbacks[subscriber_id] = callback

    def unsubscribe(self, topic: str, subscriber_id: str):
        if topic in self._subscribers:
            self._subscribers[topic].discard(subscriber_id)
        self._callbacks.pop(subscriber_id, None)

    def process_messages(self, timeout: float = 0.1):
        try:
            msg = self._queue.get(timeout=timeout)
            topic = msg.get('topic')
            data = msg.get('data')

            if topic in self._subscribers:
                for subscriber_id in list(self._subscribers[topic]):
                    callback = self._callbacks.get(subscriber_id)
                    if callback:
                        try:
                            callback(topic, data)
                        except Exception as e:
                            logger.error(f"回调失败 [{subscriber_id}]: {e}")
            return True
        except Empty:
            return False

    def get_stats(self) -> Dict:
        return {
            'queue_size': self._queue.qsize(),
            'subscribers': sum(len(s) for s in self._subscribers.values()),
            'topics': len(self._subscribers)
        }


class ChannelManager:
    MAX_CHANNELS = 3
    MAX_CHARACTERS_PER_CHANNEL = 5

    def __init__(self):
        self.channels: List[Channel] = [
            Channel(id=i, max_characters=self.MAX_CHARACTERS_PER_CHANNEL)
            for i in range(self.MAX_CHANNELS)
        ]
        self._character_channel_map: Dict[str, int] = {}
        self._broadcast_callback = None

    def set_broadcast_callback(self, callback):
        self._broadcast_callback = callback

    async def broadcast_channel_list(self):
        if self._broadcast_callback:
            await self._broadcast_callback()

    def get_all_channels(self) -> List[Dict]:
        return [c.to_dict() for c in self.channels]

    def get_channel(self, channel_id: int) -> Optional[Channel]:
        if 0 <= channel_id < len(self.channels):
            return self.channels[channel_id]
        return None

    def get_channel_by_world_name(self, world_name: str) -> Optional[Channel]:
        for c in self.channels:
            if c.has_world_created() and c.world.name == world_name:
                return c
        return None

    def get_character_channel(self, character_id: str) -> Optional[int]:
        return self._character_channel_map.get(character_id)

    def get_empty_channel(self) -> Optional[Channel]:
        for c in self.channels:
            if not c.has_world_created():
                return c
        return None

    def is_world_name_exists(self, name: str) -> bool:
        for c in self.channels:
            if c.has_world_created() and c.world.name == name:
                return True
        return False

    def allocate_channel(self, world_name: str, template: str = 'island') -> Optional[int]:
        channel = self.get_empty_channel()
        if not channel:
            return None
        if self.is_world_name_exists(world_name):
            return None
        channel.create_world(world_name, template)
        return channel.id

    def delete_world(self, channel_id: int) -> bool:
        channel = self.get_channel(channel_id)
        if not channel or not channel.has_world_created():
            return False
        for char_id in list(channel.characters.keys()):
            self._character_channel_map.pop(char_id, None)
        channel.delete_world()
        logger.info(f"删除世界: 频道 {channel_id}")
        return True

    def add_character(self, channel_id: int, character_id: str, character_name: str,
                      icon: str = 'user', role: str = 'ego') -> bool:
        channel = self.get_channel(channel_id)
        if not channel or not channel.has_world_created() or channel.is_full():
            return False

        if channel.is_locked():
            logger.warning(f"频道 {channel_id} 已锁定，拒绝加入")
            return False

        if character_id in self._character_channel_map:
            old_channel_id = self._character_channel_map[character_id]
            old_channel = self.get_channel(old_channel_id)
            if old_channel:
                old_channel.remove_character(character_id)

        character = CharacterInfo(id=character_id, name=character_name, icon=icon, role=role)
        if channel.add_character(character):
            self._character_channel_map[character_id] = channel_id
            return True
        return False

    def remove_character(self, character_id: str) -> bool:
        channel_id = self._character_channel_map.get(character_id)
        if channel_id is None:
            return False
        channel = self.get_channel(channel_id)
        if channel:
            channel.remove_character(character_id)
        self._character_channel_map.pop(character_id, None)
        return True

    def get_world_state(self, channel_id: int) -> Dict:
        channel = self.get_channel(channel_id)
        if not channel or not channel.has_world_created():
            return {}
        return {
            'channel_id': channel_id,
            'world_id': channel.world.id,
            'world_name': channel.world.name,
            'state': channel.world.state or {},
            'characters': [
                {'id': c.id, 'name': c.name, 'icon': c.icon, 'role': c.role}
                for c in channel.characters.values()
            ]
        }


class InstanceCoordinator:
    def __init__(self, queue: MessageQueue, channel_manager: ChannelManager, ws_server: 'WebSocketServer'):
        self.queue = queue
        self.channel_manager = channel_manager
        self.ws_server = ws_server
        self.ready_status: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._timeout_seconds = 30

    def register_ready(self, instance: str, role: str, character_id: str = None,
                       character_name: str = None, connection_id: str = None,
                       channel_id: int = None, world_name: str = None):
        with self._lock:
            if instance not in self.ready_status:
                self.ready_status[instance] = {
                    'field': False,
                    'field_connection_id': None,
                    'players': {},
                    'timer': None,
                    'channel_id': channel_id,
                    'game_started': False,
                    'world_name': world_name or instance,
                    'timeout_task': None
                }

            status = self.ready_status[instance]

            if world_name:
                status['world_name'] = world_name

            if role == 'field':
                status['field'] = True
                status['field_connection_id'] = connection_id
                if channel_id is not None:
                    status['channel_id'] = channel_id
                logger.info(f"[协调器] {instance} field 就绪")

            elif role == 'ego':
                if character_id:
                    status['players'][character_id] = {
                        'name': character_name or character_id,
                        'connection_id': connection_id
                    }
                    logger.info(f"[协调器] {instance} 玩家 {character_name} 加入")

    def unregister_player(self, instance: str, character_id: str):
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                return

            if character_id in status['players']:
                player_name = status['players'][character_id].get('name', character_id)
                del status['players'][character_id]
                logger.info(f"[协调器] {instance} 玩家 {player_name} 离开")

                channel = self.channel_manager.get_channel_by_world_name(instance)
                if channel:
                    self.queue.publish(channel.get_channel_topic(), {
                        'type': 'character_left',
                        'character_id': character_id,
                        'character_name': player_name
                    })

    def unregister_field(self, instance: str):
        with self._lock:
            if instance in self.ready_status:
                logger.info(f"[协调器] {instance} field 断开，清理状态")
                status = self.ready_status[instance]

                if not status.get('game_started', False):
                    channel_id = status.get('channel_id')
                    if channel_id is not None:
                        channel = self.channel_manager.get_channel(channel_id)
                        if channel:
                            channel.set_ready(False)
                            asyncio.create_task(self.channel_manager.broadcast_channel_list())

                for char_id, info in status.get('players', {}).items():
                    conn_id = info.get('connection_id')
                    if conn_id:
                        topic = f"/connection/{conn_id}"
                        self.queue.publish(topic, {
                            'type': 'host_disconnected',
                            'instance': instance,
                            'message': '房主已断开连接'
                        })
                        self.ws_server.close_connection(conn_id)

                if status.get('timeout_task'):
                    status['timeout_task'].cancel()

                if instance in self.ready_status:
                    del self.ready_status[instance]

    def kick_player(self, instance: str, character_id: str, connection_id: str):
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                return

            if connection_id != status.get('field_connection_id'):
                logger.warning(f"[协调器] 非房主尝试踢人: {connection_id}")
                return

            if character_id not in status['players']:
                return

            player = status['players'][character_id]
            target_conn_id = player.get('connection_id')
            player_name = player.get('name', character_id)

            del status['players'][character_id]
            logger.info(f"[协调器] {instance} 房主踢出玩家: {player_name}")

            channel = self.channel_manager.get_channel_by_world_name(instance)
            if channel:
                channel.remove_character(character_id)
                self.queue.publish(channel.get_channel_topic(), {
                    'type': 'character_left',
                    'character_id': character_id,
                    'character_name': player_name,
                    'kicked': True
                })
                asyncio.create_task(self.channel_manager.broadcast_channel_list())

            if target_conn_id:
                topic = f"/connection/{target_conn_id}"
                self.queue.publish(topic, {
                    'type': 'you_are_kicked',
                    'instance': instance,
                    'message': f'房主将你移出了游戏'
                })
                self.ws_server.close_connection(target_conn_id)

    def start_game(self, instance: str, connection_id: str) -> Optional[int]:
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                logger.warning(f"[协调器] {instance} 状态不存在")
                return None

            if status.get('game_started', False):
                logger.warning(f"[协调器] {instance} 游戏已开始")
                return None

            if len(status.get('players', {})) == 0:
                logger.warning(f"[协调器] {instance} 没有玩家，无法开始")
                return None

            channel_id = status.get('channel_id')
            world_name = status.get('world_name', instance)

            channel = None
            if channel_id is not None:
                channel = self.channel_manager.get_channel(channel_id)

            if channel is None:
                channel = self.channel_manager.get_channel_by_world_name(world_name)

            if channel:
                channel.set_ready(True)
                channel.set_game_started(True)
                asyncio.create_task(self.channel_manager.broadcast_channel_list())
                logger.info(f"[协调器] {instance} 频道 {channel.id} 已设为就绪并锁定")
            else:
                logger.warning(f"[协调器] {instance} 未找到对应的频道")

            self._broadcast_game_start(instance)
            status['game_started'] = True

            if status.get('timeout_task'):
                status['timeout_task'].cancel()
                status['timeout_task'] = None

            logger.info(f"[协调器] {instance} start_game 完成")
            return channel_id

    def cancel_lobby(self, instance: str, connection_id: str, channel_id: int = None):
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                logger.warning(f"[协调器] {instance} 状态不存在")
                return

            if channel_id is None:
                channel_id = status.get('channel_id')

            logger.info(f"[协调器] {instance} 取消大厅 (频道 {channel_id})")

            if channel_id is not None:
                channel = self.channel_manager.get_channel(channel_id)
                if channel:
                    channel.set_ready(False)
                    channel.delete_world()
                    asyncio.create_task(self.channel_manager.broadcast_channel_list())
                    self.queue.publish(f"/channel/{channel_id}", {
                        'type': 'lobby_cancelled',
                        'instance': instance,
                        'message': '大厅已取消'
                    })

            if status.get('timeout_task'):
                status['timeout_task'].cancel()

            if instance in self.ready_status:
                del self.ready_status[instance]

            logger.info(f"[协调器] {instance} 已清理完成")

    def _start_timeout(self, instance: str):
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                return

            if status.get('timeout_task'):
                status['timeout_task'].cancel()

            async def timeout_handler():
                await asyncio.sleep(self._timeout_seconds)
                with self._lock:
                    status = self.ready_status.get(instance)
                    if not status:
                        return

                    if status.get('game_started', False):
                        logger.info(f"[协调器] {instance} 超时检查: game_started=True，跳过清理")
                        return

                    logger.info(f"[协调器] {instance} 超时，强制断开所有连接")

                    for char_id, info in status.get('players', {}).items():
                        conn_id = info.get('connection_id')
                        if conn_id:
                            topic = f"/connection/{conn_id}"
                            self.queue.publish(topic, {
                                'type': 'timeout_disconnect',
                                'instance': instance,
                                'message': '连接超时'
                            })
                            self.ws_server.close_connection(conn_id)

                    channel = self.channel_manager.get_channel_by_world_name(instance)
                    if channel:
                        channel.delete_world()
                        asyncio.create_task(self.channel_manager.broadcast_channel_list())

                    if instance in self.ready_status:
                        del self.ready_status[instance]

            loop = asyncio.get_event_loop()
            status['timeout_task'] = asyncio.create_task(timeout_handler())

    def stop_instance(self, instance: str, connection_id: str, channel_id: int = None):
        with self._lock:
            status = self.ready_status.get(instance)

            if channel_id is None:
                if status:
                    channel_id = status.get('channel_id')
            if channel_id is None:
                channel = self.channel_manager.get_channel_by_world_name(instance)
                if channel:
                    channel_id = channel.id

            if channel_id is not None:
                channel = self.channel_manager.get_channel(channel_id)
                if channel:
                    self.queue.publish(channel.get_channel_topic(), {
                        'type': 'stop',
                        'instance': instance,
                        'message': '实例已停止'
                    })

                    for char_id in list(channel.characters.keys()):
                        self.ws_server.close_connection_by_character(char_id)

                    channel.delete_world()
                    asyncio.create_task(self.channel_manager.broadcast_channel_list())
                    logger.info(f"[协调器] {instance} 已停止 (频道 {channel_id})")

            if instance in self.ready_status:
                if self.ready_status[instance].get('timeout_task'):
                    self.ready_status[instance]['timeout_task'].cancel()
                del self.ready_status[instance]

    def get_instance_status(self, instance: str) -> Dict:
        with self._lock:
            status = self.ready_status.get(instance)
            if status:
                return {
                    'instance': instance,
                    'exists': True,
                    'status': 'running' if status.get('game_started', False) else 'waiting',
                    'field_ready': status.get('field', False),
                    'players': list(status.get('players', {}).keys())
                }

            channel = self.channel_manager.get_channel_by_world_name(instance)
            if channel and channel.has_world():
                return {
                    'instance': instance,
                    'exists': True,
                    'status': 'running' if channel.game_started else 'waiting',
                    'field_ready': True,
                    'players': list(channel.characters.keys())
                }

            return {'instance': instance, 'exists': False, 'status': 'stopped'}

    def get_all_instances_status(self) -> List[Dict]:
        with self._lock:
            result = []
            seen = set()

            for instance, status in self.ready_status.items():
                seen.add(instance)
                result.append({
                    'instance': instance,
                    'status': 'running' if status.get('game_started', False) else 'waiting',
                    'field_ready': status.get('field', False),
                    'players': list(status.get('players', {}).keys())
                })

            for channel in self.channel_manager.channels:
                if channel.has_world_created() and channel.has_world():
                    instance_name = channel.world.name
                    if instance_name not in seen:
                        result.append({
                            'instance': instance_name,
                            'status': 'running' if channel.game_started else 'waiting',
                            'field_ready': True,
                            'players': list(channel.characters.keys())
                        })

            return result

    def get_lobby_status(self, instance: str) -> Dict:
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                channel = self.channel_manager.get_channel_by_world_name(instance)
                if channel and channel.has_world():
                    return {
                        'instance': instance,
                        'exists': True,
                        'world_name': instance,
                        'field_ready': channel.has_field(),
                        'players': [
                            {'id': cid, 'name': c.name}
                            for cid, c in channel.characters.items() if c.role == 'ego'
                        ],
                        'connected_count': len([c for c in channel.characters.values() if c.role == 'ego']),
                        'game_started': channel.game_started
                    }
                return {'instance': instance, 'exists': False}

            players = status.get('players', {})
            return {
                'instance': instance,
                'exists': True,
                'world_name': status.get('world_name', instance),
                'field_ready': status.get('field', False),
                'players': [
                    {'id': pid, 'name': info.get('name', pid)}
                    for pid, info in players.items()
                ],
                'connected_count': len(players),
                'game_started': status.get('game_started', False)
            }

    def _broadcast_game_start(self, instance: str):
        status = self.ready_status.get(instance)
        if not status:
            return

        channel_id = status.get('channel_id')
        if channel_id is None:
            channel = self.channel_manager.get_channel_by_world_name(instance)
            if channel:
                channel_id = channel.id

        if channel_id is None:
            logger.error(f"[协调器] {instance} 没有 channel_id")
            return

        players = list(status.get('players', {}).keys())
        self.queue.publish(f"/channel/{channel_id}", {
            'type': 'game_start',
            'instance': instance,
            'world_name': status.get('world_name', instance),
            'timestamp': time.time(),
            'players': players
        })
        logger.info(f"[协调器] {instance} 游戏开始，玩家: {players}")


class WebSocketServer:
    def __init__(self, queue: MessageQueue, channel_manager: ChannelManager,
                 host: str = '127.0.0.1', port: int = 8765):
        self.queue = queue
        self.channel_manager = channel_manager
        self.host = host
        self.port = port
        self.http_port = port + 1  # 8766

        self.connections: Dict[str, Any] = {}
        self.connection_roles: Dict[str, str] = {}
        self.connection_character: Dict[str, str] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
        self._server = None
        self._running = False
        self._loop = None

        self._http_runner = None

        self.channel_manager.set_broadcast_callback(self._broadcast_channel_list)
        self.coordinator = InstanceCoordinator(queue, channel_manager, self)

    async def start(self):
        import websockets

        self._running = True
        self._loop = asyncio.get_running_loop()

        self._server = await websockets.serve(
            self._handle_connection,
            self.host,
            self.port
        )
        logger.info(f"WebSocket 服务启动: ws://{self.host}:{self.port}")

        app = web.Application()
        app.router.add_get('/api/terrain', self.handle_get_terrain)
        app.router.add_get('/api/terrain/{world_name}', self.handle_get_terrain_by_world)
        app.router.add_get('/api/channel/{world_name}', self.handle_get_channel)
        app.router.add_get('/health', self.handle_health)

        app.router.add_options('/api/terrain', self.handle_options)
        app.router.add_options('/api/terrain/{world_name}', self.handle_options)
        app.router.add_options('/api/channel/{world_name}', self.handle_options)

        self._http_runner = web.AppRunner(app)
        await self._http_runner.setup()
        site = web.TCPSite(self._http_runner, self.host, self.http_port)
        await site.start()
        logger.info(f"HTTP 服务启动: http://{self.host}:{self.http_port}")

        await self._server.wait_closed()

    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        if self._http_runner:
            await self._http_runner.cleanup()

        logger.info("服务已停止")

    def close_connection(self, connection_id: str):
        websocket = self.connections.get(connection_id)
        if websocket:
            try:
                asyncio.run_coroutine_threadsafe(
                    websocket.close(),
                    self._loop
                )
            except:
                pass

    def close_connection_by_character(self, character_id: str):
        for conn_id, char_id in self.connection_character.items():
            if char_id == character_id:
                self.close_connection(conn_id)
                break

    async def _handle_connection(self, websocket, *args):
        connection_id = f"conn_{uuid.uuid4().hex[:8]}"
        self.connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()
        self.connection_roles[connection_id] = None
        self.connection_character[connection_id] = None

        logger.info(f"[{connection_id}] 连接建立")

        await self._send_to_client(connection_id, {
            'type': 'connection_established',
            'connection_id': connection_id
        })

        def on_queue_message(topic: str, data: Any):
            if not self._running:
                return
            if self._loop and not self._loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    self._send_to_client(connection_id, {
                        'type': 'message',
                        'topic': topic,
                        'data': data
                    }),
                    self._loop
                )

        try:
            async for message in websocket:
                await self._handle_client_message(connection_id, message, on_queue_message)
        except:
            pass
        finally:
            self._cleanup_connection(connection_id)

    def _cleanup_connection(self, connection_id: str):
        role = self.connection_roles.get(connection_id)
        character_id = self.connection_character.get(connection_id)

        if role == 'field':
            for instance, status in list(self.coordinator.ready_status.items()):
                if status.get('field_connection_id') == connection_id:
                    self.coordinator.unregister_field(instance)
                    break

        elif role == 'ego':
            for instance, status in list(self.coordinator.ready_status.items()):
                for char_id, info in list(status.get('players', {}).items()):
                    if info.get('connection_id') == connection_id:
                        self.coordinator.unregister_player(instance, char_id)
                        break

            if character_id:
                self.channel_manager.remove_character(character_id)
                asyncio.create_task(self.channel_manager.broadcast_channel_list())

        elif role == 'dashboard':
            pass

        for topic in list(self.subscriptions.get(connection_id, [])):
            self.queue.unsubscribe(topic, connection_id)

        self.connections.pop(connection_id, None)
        self.subscriptions.pop(connection_id, None)
        self.connection_roles.pop(connection_id, None)
        self.connection_character.pop(connection_id, None)
        logger.info(f"[{connection_id}] 连接断开")

    async def _handle_client_message(self, connection_id: str, message: str, callback):
        try:
            data = json.loads(message)
            action = data.get('action')

            if action == 'register':
                role = data.get('role')
                character_id = data.get('character_id')
                character_name = data.get('character_name', character_id)

                if role not in ['field', 'ego', 'dashboard']:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '无效的角色类型，必须是 field/ego/dashboard'
                    })
                    return

                if not character_id:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '缺少 character_id'
                    })
                    return

                self.connection_roles[connection_id] = role
                self.connection_character[connection_id] = character_id

                await self._send_to_client(connection_id, {
                    'type': 'registered',
                    'role': role,
                    'character_id': character_id,
                    'character_name': character_name
                })

                if role == 'dashboard':
                    await self._send_to_client(connection_id, {
                        'type': 'channel_list',
                        'data': self.channel_manager.get_all_channels()
                    })

                logger.info(f"[{connection_id}] 注册为 {role}: {character_name}")

            elif action == 'subscribe':
                topic = data.get('topic')
                if topic:
                    self.subscriptions[connection_id].add(topic)
                    self.queue.subscribe(topic, connection_id, callback)
                    await self._send_to_client(connection_id, {
                        'type': 'subscribed',
                        'topic': topic
                    })

            elif action == 'unsubscribe':
                topic = data.get('topic')
                if topic:
                    self.subscriptions[connection_id].discard(topic)
                    self.queue.unsubscribe(topic, connection_id)
                    await self._send_to_client(connection_id, {
                        'type': 'unsubscribed',
                        'topic': topic
                    })

            elif action == 'create_world':
                role = self.connection_roles.get(connection_id)
                if role != 'field':
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '只有 field 可以创建世界'
                    })
                    return

                name = data.get('name', '新世界')
                template = data.get('template', 'island')

                if self.channel_manager.is_world_name_exists(name):
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': f'世界名 "{name}" 已存在'
                    })
                    return

                channel_id = self.channel_manager.allocate_channel(name, template)
                if channel_id is None:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '没有空闲频道'
                    })
                    return

                channel = self.channel_manager.get_channel(channel_id)
                character_id = self.connection_character.get(connection_id)

                if character_id:
                    self.channel_manager.add_character(
                        channel_id, character_id,
                        data.get('character_name', character_id),
                        data.get('icon', 'user'),
                        'field'
                    )

                await self._send_to_client(connection_id, {
                    'type': 'world_created',
                    'data': {
                        'channel_id': channel_id,
                        'world': channel.world.__dict__,
                        'channel_topic': channel.get_channel_topic()
                    }
                })

                self.coordinator.register_ready(
                    instance=name,
                    role='field',
                    character_id=character_id,
                    character_name=data.get('character_name', character_id),
                    connection_id=connection_id,
                    channel_id=channel_id,
                    world_name=name                )

                await self._broadcast_channel_list()

            elif action == 'join_world':
                role = self.connection_roles.get(connection_id)
                if role != 'ego':
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '只有 ego 可以加入世界'
                    })
                    return

                world_name = data.get('world_name')
                character_id = data.get('character_id')
                character_name = data.get('character_name', character_id)
                icon = data.get('icon', 'user')

                if not world_name or not character_id:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '缺少 world_name 或 character_id'
                    })
                    return

                channel = self.channel_manager.get_channel_by_world_name(world_name)
                if not channel:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': f'世界 "{world_name}" 不存在'
                    })
                    return

                if channel.game_started:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': f'世界 "{world_name}" 已经开始，无法加入'
                    })
                    return

                if channel.is_locked():
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': f'世界 "{world_name}" 已锁定'
                    })
                    return

                if not channel.has_field():
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': f'世界 "{world_name}" 尚未就绪，请等待房主连接'
                    })
                    return

                if channel.is_full():
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': f'世界 "{world_name}" 已满'
                    })
                    return

                channel_id = channel.id
                if not self.channel_manager.add_character(channel_id, character_id, character_name, icon, 'ego'):
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '加入世界失败'
                    })
                    return

                self.connection_character[connection_id] = character_id

                channel_topic = channel.get_channel_topic()
                self.queue.publish(channel_topic, {
                    'type': 'character_joined',
                    'character_id': character_id,
                    'character_name': character_name,
                    'icon': icon,
                    'role': 'ego'
                })

                self.coordinator.register_ready(
                    instance=world_name,
                    role='ego',
                    character_id=character_id,
                    character_name=character_name,
                    connection_id=connection_id,
                    channel_id=channel_id,
                    world_name=world_name
                )

                world_state = self.channel_manager.get_world_state(channel_id)
                await self._send_to_client(connection_id, {
                    'type': 'world_state',
                    'data': {
                        **world_state,
                        'channel_topic': channel_topic
                    }
                })
                await self._broadcast_channel_list()

            elif action == 'leave_world':
                character_id = data.get('character_id')
                if not character_id:
                    return

                channel_id = self.channel_manager.get_character_channel(character_id)
                if channel_id is not None:
                    channel = self.channel_manager.get_channel(channel_id)
                    if channel and channel.has_world_created():
                        channel_topic = channel.get_channel_topic()
                        self.queue.publish(channel_topic, {
                            'type': 'character_left',
                            'character_id': character_id
                        })
                        instance_name = channel.world.name
                        self.coordinator.unregister_player(instance_name, character_id)

                self.channel_manager.remove_character(character_id)
                await self._broadcast_channel_list()

            elif action == 'publish':
                topic = data.get('topic')
                payload = data.get('data')
                if topic and payload is not None:
                    self.queue.publish(topic, payload)

            elif action == 'get_channel_list':
                await self._send_to_client(connection_id, {
                    'type': 'channel_list',
                    'data': self.channel_manager.get_all_channels()
                })

            elif action == 'get_lobby_status':
                instance = data.get('instance')
                if instance:
                    status = self.coordinator.get_lobby_status(instance)
                    await self._send_to_client(connection_id, {
                        'type': 'lobby_status',
                        'data': status
                    })

            elif action == 'ready':
                role = self.connection_roles.get(connection_id)
                instance = data.get('instance')
                character_id = data.get('character_id')
                character_name = data.get('character_name')
                channel_id = data.get('channel_id')
                world_name = data.get('world_name')

                if not instance:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '缺少 instance'
                    })
                    return

                logger.info(f"[协调器] 收到 ready: {role} {instance} {character_id or ''}")

                self.coordinator.register_ready(
                    instance=instance,
                    role=role,
                    character_id=character_id,
                    character_name=character_name,
                    connection_id=connection_id,
                    channel_id=channel_id,
                    world_name=world_name
                )

                await self._send_to_client(connection_id, {
                    'type': 'ready_ack',
                    'instance': instance,
                    'role': role,
                    'character_id': character_id,
                    'status': 'registered'
                })

            elif action == 'kick_player':
                instance = data.get('instance')
                character_id = data.get('character_id')
                if instance and character_id:
                    self.coordinator.kick_player(instance, character_id, connection_id)
                    await self._send_to_client(connection_id, {
                        'type': 'kick_ack',
                        'instance': instance,
                        'character_id': character_id,
                        'status': 'kicked'
                    })

            elif action == 'start_game':
                instance = data.get('instance')
                if instance:
                    channel_id = self.coordinator.start_game(instance, connection_id)
                    await self._send_to_client(connection_id, {
                        'type': 'start_game_ack',
                        'instance': instance,
                        'channel_id': channel_id,
                        'status': 'started'
                    })

            elif action == 'cancel_lobby':
                instance = data.get('instance')
                channel_id = data.get('channel_id')
                if instance:
                    self.coordinator.cancel_lobby(instance, connection_id, channel_id)
                    await self._send_to_client(connection_id, {
                        'type': 'cancel_lobby_ack',
                        'instance': instance,
                        'status': 'cancelled'
                    })

            elif action == 'stop_instance':
                instance = data.get('instance')
                channel_id = data.get('channel_id')
                if instance:
                    self.coordinator.stop_instance(instance, connection_id, channel_id)
                    await self._send_to_client(connection_id, {
                        'type': 'stop_instance_ack',
                        'instance': instance,
                        'channel_id': channel_id,
                        'status': 'stopped'
                    })

            elif action == 'get_instance_status':
                instance = data.get('instance')
                if instance:
                    status = self.coordinator.get_instance_status(instance)
                    await self._send_to_client(connection_id, {
                        'type': 'instance_status',
                        'data': status
                    })

            elif action == 'get_all_instances_status':
                status = self.coordinator.get_all_instances_status()
                await self._send_to_client(connection_id, {
                    'type': 'all_instances_status',
                    'data': status
                })

            elif action == 'dashboard_command':
                role = self.connection_roles.get(connection_id)
                if role != 'dashboard':
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '只有 dashboard 可以发送指令'
                    })
                    return

                target = data.get('target')
                command = data.get('command')
                payload = data.get('payload', {})

                if target and command:
                    self.queue.publish(f"/command/{target}", {
                        'type': 'dashboard_command',
                        'command': command,
                        'payload': payload,
                        'source': connection_id
                    })
                    await self._send_to_client(connection_id, {
                        'type': 'command_ack',
                        'target': target,
                        'command': command,
                        'status': 'sent'
                    })

        except json.JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"处理消息错误: {e}")

    async def _send_to_client(self, connection_id: str, message: Any):
        websocket = self.connections.get(connection_id)
        if websocket:
            try:
                await websocket.send(json.dumps(message, ensure_ascii=False))
            except:
                pass

    async def _broadcast_channel_list(self):
        msg = {
            'type': 'channel_list',
            'data': self.channel_manager.get_all_channels()
        }
        msg_str = json.dumps(msg, ensure_ascii=False)
        for conn_id, ws in list(self.connections.items()):
            try:
                await ws.send(msg_str)
            except:
                pass

    # ===== HTTP 接口 =====

    async def handle_options(self, request):
        return web.Response(
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )

    async def handle_get_channel(self, request):
        """通过世界名获取 channel_id"""
        world_name = request.match_info.get('world_name', '')
        if not world_name:
            return web.json_response(
                {'success': False, 'error': '缺少 world_name'},
                status=400,
                headers={'Access-Control-Allow-Origin': '*'}
            )

        channel = self.channel_manager.get_channel_by_world_name(world_name)
        if not channel:
            return web.json_response(
                {'success': False, 'error': f'世界 "{world_name}" 不存在'},
                status=404,
                headers={'Access-Control-Allow-Origin': '*'}
            )

        if not channel.has_world_created():
            return web.json_response(
                {'success': False, 'error': f'世界 "{world_name}" 尚未创建'},
                status=404,
                headers={'Access-Control-Allow-Origin': '*'}
            )

        return web.json_response(
            {
                'success': True,
                'channel_id': channel.id,
                'world_name': channel.world.name if channel.world else world_name,
                'game_started': channel.game_started,
                'is_ready': channel.is_ready
            },
            headers={'Access-Control-Allow-Origin': '*'}
        )

    async def handle_get_terrain(self, request):
        world_name = request.query.get('world_name')
        if not world_name:
            return web.json_response(
                {'error': '缺少 world_name 参数，如 /api/terrain?world_name=荒岛求生'},
                status=400,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        return await self._load_terrain_from_file(world_name)

    async def handle_get_terrain_by_world(self, request):
        world_name = request.match_info.get('world_name', '')
        if not world_name:
            return web.json_response(
                {'error': '请指定世界名，如 /api/terrain/荒岛求生'},
                status=400,
                headers={'Access-Control-Allow-Origin': '*'}
            )
        return await self._load_terrain_from_file(world_name)

    def parse_points(self, point_str):
        if not point_str:
            return []
        result = []
        for part in point_str.split(';'):
            x, y, z = part.split(',')
            result.append({'x': float(x), 'y': float(y), 'z': float(z)})
        return result

    def restore_json_from_db(self, db_path: str):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 名称, 几何点集
            FROM 空间注册
            WHERE 实体类型 = 'field'
            ORDER BY tick DESC
            LIMIT 1
        ''')
        row = cursor.fetchone()
        field = None
        if row:
            points = self.parse_points(row[1])
            field = {"name": row[0], "width": 0, "height": 0, "zMin": 0, "zMax": 0}
            if points:
                xs = [p['x'] for p in points]
                ys = [p['y'] for p in points]
                field["width"] = max(xs) - min(xs)
                field["height"] = max(ys) - min(ys)
                field["zMin"] = points[0]["z"]
                field["zMax"] = points[4]["z"]

        cursor.execute('''
            SELECT t.id, t.名称, t.颜色, t.几何点集
            FROM 空间注册 t
            INNER JOIN (
                SELECT id, MAX(tick) AS max_tick
                FROM 空间注册
                WHERE 实体类型 = 'terrain'
                GROUP BY id
            ) latest ON t.id = latest.id AND t.tick = latest.max_tick
            ORDER BY t.id
        ''')
        terrains = []
        for row in cursor.fetchall():
            terrains.append({
                "id": row[0],
                "name": row[1],
                "color": row[2],
                "points": self.parse_points(row[3])
            })

        cursor.execute('''
            SELECT t.id, t.图标, t.名称, t.坐标_x, t.坐标_y, t.坐标_z
            FROM 空间注册 t
            INNER JOIN (
                SELECT id, MAX(tick) AS max_tick
                FROM 空间注册
                WHERE 实体类型 = 'item'
                GROUP BY id
            ) latest ON t.id = latest.id AND t.tick = latest.max_tick
            ORDER BY t.id
        ''')
        items = []
        for row in cursor.fetchall():
            items.append({
                "id": row[0],
                "icon": row[1],
                "name": row[2],
                "x": row[3],
                "y": row[4],
                "z": row[5]
            })

        conn.close()
        return {"field": field, "terrains": terrains, "items": items}

    def find_field_db(self, instance_name: str) -> Optional[str]:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, '..', 'data', 'instance', instance_name)

        if not os.path.exists(data_dir):
            return None

        db_files = glob.glob(os.path.join(data_dir, 'field_*.db'))
        if db_files:
            return db_files[0]
        return None

    async def _load_terrain_from_file(self, world_name: str = None):
        try:
            if not world_name:
                return web.json_response(
                    {'error': '请指定世界名，如 /api/terrain/荒岛求生'},
                    status=400,
                    headers={'Access-Control-Allow-Origin': '*'}
                )

            db_path = self.find_field_db(world_name)
            if not db_path or not os.path.exists(db_path):
                logger.warning(f"HTTP: 世界 {world_name} 的数据库不存在: {db_path}")
                return web.json_response(
                    {'error': f'世界 "{world_name}" 不存在或未初始化'},
                    status=404,
                    headers={'Access-Control-Allow-Origin': '*'}
                )

            terrain_data = self.restore_json_from_db(db_path)
            logger.info(f"HTTP: 从数据库加载世界地形: {world_name} -> {os.path.basename(db_path)}")
            return web.json_response(
                terrain_data,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Cache-Control': 'no-cache',
                }
            )

        except Exception as e:
            logger.error(f"加载地形数据失败: {e}")
            return web.json_response(
                {'error': f'加载失败: {str(e)}'},
                status=500,
                headers={'Access-Control-Allow-Origin': '*'}
            )

    async def handle_health(self, request):
        return web.json_response(
            {
                'status': 'ok',
                'timestamp': time.time(),
                'connections': len(self.connections),
                'channels': len(self.channel_manager.channels)
            },
            headers={'Access-Control-Allow-Origin': '*'}
        )


class MessageBroker:
    def __init__(self, host: str = '127.0.0.1', port: int = 8765):
        self.host = host
        self.port = port
        self.queue = MessageQueue()
        self.channel_manager = ChannelManager()
        self.ws_server = WebSocketServer(self.queue, self.channel_manager, host, port)
        self._processing_thread: Optional[threading.Thread] = None
        self._running = False
        self._ws_thread: Optional[threading.Thread] = None
        self._started = False

    def start(self):
        if self._started:
            return

        self._running = True
        self._started = True

        self._processing_thread = threading.Thread(target=self._process_loop, daemon=True)
        self._processing_thread.start()

        self._ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self._ws_thread.start()

        logger.info(f"消息队列服务器已启动")
        logger.info(f"WebSocket: ws://{self.host}:{self.port}")
        logger.info(f"HTTP: http://{self.host}:{self.port + 1}")
        logger.info(f"预设频道: {self.channel_manager.MAX_CHANNELS} 个")
        logger.info(f"每频道上限: {self.channel_manager.MAX_CHARACTERS_PER_CHANNEL} 人")

    def _run_websocket(self):
        try:
            asyncio.run(self._ws_server_task())
        except Exception as e:
            logger.error(f"WebSocket 服务异常: {e}")
            self._running = False

    async def _ws_server_task(self):
        await self.ws_server.start()

    def _process_loop(self):
        while self._running:
            try:
                self.queue.process_messages(timeout=0.1)
            except Exception as e:
                logger.error(f"队列处理错误: {e}")

    def stop(self):
        if not self._started:
            return

        self._running = False
        self._started = False

        try:
            if self.ws_server:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.ws_server.stop())
                loop.close()
        except Exception as e:
            logger.error(f"停止 WebSocket 服务失败: {e}")

        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=2)

        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=2)

        logger.info("消息队列服务器已停止")

    def is_running(self) -> bool:
        return self._running and self._started

    def get_stats(self) -> Dict:
        return self.queue.get_stats()


def start_server(host: str = '127.0.0.1', port: int = 8765):
    broker = MessageBroker(host, port)
    broker.start()

    print("=" * 60)
    print("SurvX 服务器已启动")
    print("=" * 60)
    print(f"WebSocket: ws://{host}:{port}      ← 实时通信")
    print(f"HTTP:      http://{host}:{port+1}  ← 地形数据")
    print("=" * 60)
    print("按 Ctrl+C 退出")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        broker.stop()
        logger.info("已退出")


if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765

    print("=" * 60)
    print("SurvX 消息队列服务器")
    print("=" * 60)
    print(f"WebSocket: ws://{host}:{port}")
    print(f"HTTP:      http://{host}:{port + 1}")
    print(f"预设频道: {ChannelManager.MAX_CHANNELS} 个")
    print(f"每频道上限: {ChannelManager.MAX_CHARACTERS_PER_CHANNEL} 人")
    print("按 Ctrl+C 退出")
    print("=" * 60)

    start_server(host, port)