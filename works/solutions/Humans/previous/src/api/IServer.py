#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SurvX 消息队列服务器

功能:
  1. 消息队列: 接收消息 -> 队列 -> 转发给订阅者
  2. WebSocket 服务: 前端通过 WebSocket 连接
  3. 频道管理: 预设 3 个频道
  4. 世界管理: 每个频道可创建一个世界
  5. 人物管理: 人物动态加入/退出世界
  6. 频道订阅: 所有消息走 /channel/{channel_id}
  7. 实例协调: 等待房主确认后统一开始
"""

import json
import asyncio
import logging
import threading
import time
import uuid
from queue import Queue, Empty
from typing import Dict, Set, Any, Optional, List
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class World:
    id: str
    name: str
    template: str = 'island'
    status: str = 'created'
    config: Dict = field(default_factory=dict)
    sego: Dict = field(default_factory=dict)
    state: Dict = field(default_factory=dict)


@dataclass
class CharacterInfo:
    id: str
    name: str
    icon: str = 'user'
    channel_id: int = -1


@dataclass
class Channel:
    id: int
    world: Optional[World] = None
    characters: Dict[str, CharacterInfo] = field(default_factory=dict)
    max_characters: int = 5

    def has_world(self) -> bool:
        return self.world is not None

    def is_full(self) -> bool:
        return len(self.characters) >= self.max_characters

    def add_character(self, character: CharacterInfo) -> bool:
        if self.is_full():
            return False
        if character.id in self.characters:
            return False
        self.characters[character.id] = character
        character.channel_id = self.id
        return True

    def remove_character(self, character_id: str) -> bool:
        if character_id not in self.characters:
            return False
        del self.characters[character_id]
        return True

    def create_world(self, name: str, template: str = 'island') -> World:
        if self.has_world():
            raise ValueError(f"频道 {self.id} 已有世界")
        world_id = f"world_{uuid.uuid4().hex[:8]}"
        self.world = World(id=world_id, name=name, template=template, status='created')
        return self.world

    def delete_world(self):
        self.world = None
        self.characters.clear()

    def to_dict(self) -> Dict:
        return {
            'channel_id': self.id,
            'has_world': self.has_world(),
            'world': {
                'id': self.world.id,
                'name': self.world.name,
                'template': self.world.template,
                'status': self.world.status
            } if self.has_world() else None,
            'characters': [
                {'id': c.id, 'name': c.name, 'icon': c.icon}
                for c in self.characters.values()
            ],
            'character_count': len(self.characters),
            'max_characters': self.max_characters
        }

    def get_channel_topic(self) -> str:
        return f"/channel/{self.id}"


class InstanceCoordinator:
    """等待房主确认后统一开始游戏"""
    
    def __init__(self, queue: 'MessageQueue'):
        self.queue = queue
        self.ready_status: Dict[str, Dict] = {}
        self._lock = threading.RLock()
    
    def register_ready(self, instance: str, role: str, 
                       character_id: str = None, 
                       character_name: str = None,
                       connection_id: str = None,
                       channel_id: int = None,
                       world_name: str = None):
        """进程就绪时调用"""
        with self._lock:
            if instance not in self.ready_status:
                self.ready_status[instance] = {
                    'field': False,
                    'field_connection_id': None,
                    'players': {},
                    'timer': None,
                    'channel_id': channel_id,
                    'game_started': False,
                    'world_name': world_name or instance
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
            
            self._broadcast_lobby_status(instance)
            
            if status['timer'] is None and not status['game_started']:
                logger.info(f"[协调器] {instance} 等待玩家加入... (当前 {len(status['players'])} 人)")
                status['timer'] = threading.Timer(30.0, self._timeout, [instance])
                status['timer'].start()
    
    def unregister_player(self, instance: str, character_id: str):
        """玩家断开连接时调用"""
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                return
            
            if character_id in status['players']:
                player_name = status['players'][character_id].get('name', character_id)
                del status['players'][character_id]
                logger.info(f"[协调器] {instance} 玩家 {player_name} 离开")
                self._broadcast_lobby_status(instance)
    
    def unregister_field(self, instance: str):
        """field 断开连接时调用"""
        with self._lock:
            if instance in self.ready_status:
                logger.info(f"[协调器] {instance} field 断开，清理状态")
                status = self.ready_status[instance]
                for char_id, info in status.get('players', {}).items():
                    conn_id = info.get('connection_id')
                    if conn_id:
                        topic = f"/connection/{conn_id}"
                        self.queue.publish(topic, {
                            'type': 'host_disconnected',
                            'instance': instance,
                            'message': '房主已断开连接'
                        })
                del self.ready_status[instance]
    
    def kick_player(self, instance: str, character_id: str, connection_id: str):
        """房主踢人"""
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
            
            if target_conn_id:
                topic = f"/connection/{target_conn_id}"
                self.queue.publish(topic, {
                    'type': 'you_are_kicked',
                    'instance': instance,
                    'message': f'房主将你移出了游戏'
                })
            
            self._broadcast_lobby_status(instance)
    
    def start_game(self, instance: str, connection_id: str):
        """房主点击开始游戏"""
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                return
            
            if connection_id != status.get('field_connection_id'):
                logger.warning(f"[协调器] 非房主尝试开始游戏: {connection_id}")
                return
            
            if status.get('game_started', False):
                return
            
            if len(status.get('players', {})) == 0:
                logger.warning(f"[协调器] {instance} 没有玩家，无法开始")
                return
            
            self._broadcast_game_start(instance)
            status['game_started'] = True
            
            timer = status.get('timer')
            if timer:
                timer.cancel()
                status['timer'] = None
    
    def _broadcast_lobby_status(self, instance: str):
        """广播大厅状态给前端"""
        status = self.ready_status.get(instance, {})
        players = status.get('players', {})
        field_ready = status.get('field', False)
        
        data = {
            'type': 'lobby_status',
            'instance': instance,
            'world_name': status.get('world_name', instance),
            'field_ready': field_ready,
            'players': [
                {'id': pid, 'name': info.get('name', pid)}
                for pid, info in players.items()
            ],
            'connected_count': len(players),
            'game_started': status.get('game_started', False),
            'can_start': field_ready and len(players) > 0
        }
        
        topic = f"/lobby/{instance}"
        self.queue.publish(topic, data)
    
    def _broadcast_game_start(self, instance: str):
        """广播开始"""
        status = self.ready_status.get(instance)
        if not status:
            return
        
        channel_id = status.get('channel_id')
        if channel_id is None:
            logger.error(f"[协调器] {instance} 没有 channel_id，无法广播")
            return
        
        topic = f"/channel/{channel_id}"
        self.queue.publish(topic, {
            'type': 'game_start',
            'instance': instance,
            'world_name': status.get('world_name', instance),
            'timestamp': time.time()
        })
        
        logger.info(f"[协调器] {instance} 游戏开始!")
        
        self.queue.publish(f"/lobby/{instance}", {
            'type': 'game_started',
            'instance': instance,
            'world_name': status.get('world_name', instance)
        })
    
    def _timeout(self, instance: str):
        """超时处理"""
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
                return
            
            if status.get('game_started', False):
                return
            
            players = status.get('players', {})
            
            self.queue.publish(f"/lobby/{instance}", {
                'type': 'lobby_timeout',
                'instance': instance,
                'players': list(players.keys()),
                'message': f'等待玩家加入超时 (当前 {len(players)} 人)'
            })
            
            logger.warning(f"[协调器] {instance} 等待超时，当前 {len(players)} 人")
            
            status['timer'] = threading.Timer(30.0, self._timeout, [instance])
            status['timer'].start()
    
    def get_lobby_status(self, instance: str) -> Dict:
        """获取大厅状态"""
        with self._lock:
            status = self.ready_status.get(instance)
            if not status:
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
    
    def get_all_instances(self) -> List[str]:
        """获取所有正在等待的实例列表"""
        with self._lock:
            return list(self.ready_status.keys())


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

    def get_all_channels(self) -> List[Dict]:
        return [c.to_dict() for c in self.channels]

    def get_channel(self, channel_id: int) -> Optional[Channel]:
        if 0 <= channel_id < len(self.channels):
            return self.channels[channel_id]
        return None

    def get_channel_by_world_name(self, world_name: str) -> Optional[Channel]:
        for c in self.channels:
            if c.has_world() and c.world.name == world_name:
                return c
        return None

    def get_character_channel(self, character_id: str) -> Optional[int]:
        return self._character_channel_map.get(character_id)

    def get_empty_channel(self) -> Optional[Channel]:
        for c in self.channels:
            if not c.has_world():
                return c
        return None

    def is_world_name_exists(self, name: str) -> bool:
        for c in self.channels:
            if c.has_world() and c.world.name == name:
                return True
        return False

    def create_world(self, channel_id: int, name: str, template: str = 'island') -> Optional[World]:
        channel = self.get_channel(channel_id)
        if not channel:
            return None
        if channel.has_world():
            return None
        if self.is_world_name_exists(name):
            return None
        return channel.create_world(name, template)

    def delete_world(self, channel_id: int) -> bool:
        channel = self.get_channel(channel_id)
        if not channel or not channel.has_world():
            return False
        for char_id in list(channel.characters.keys()):
            self._character_channel_map.pop(char_id, None)
        channel.delete_world()
        logger.info(f"删除世界: 频道 {channel_id}")
        return True

    def add_character(self, channel_id: int, character_id: str, character_name: str, icon: str = 'user') -> bool:
        channel = self.get_channel(channel_id)
        if not channel or not channel.has_world() or channel.is_full():
            return False
        
        if character_id in self._character_channel_map:
            old_channel_id = self._character_channel_map[character_id]
            old_channel = self.get_channel(old_channel_id)
            if old_channel:
                old_channel.remove_character(character_id)
        
        character = CharacterInfo(id=character_id, name=character_name, icon=icon)
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
        if not channel or not channel.has_world():
            return {}
        return {
            'channel_id': channel_id,
            'world_id': channel.world.id,
            'world_name': channel.world.name,
            'state': channel.world.state or {},
            'characters': [
                {'id': c.id, 'name': c.name, 'icon': c.icon}
                for c in channel.characters.values()
            ]
        }


class WebSocketServer:
    def __init__(self, queue: MessageQueue, channel_manager: ChannelManager,
                 host: str = '127.0.0.1', port: int = 8765):
        self.queue = queue
        self.channel_manager = channel_manager
        self.host = host
        self.port = port
        self.connections: Dict[str, Any] = {}
        self.subscriptions: Dict[str, Set[str]] = {}
        self._server = None
        self._running = False
        self._loop = None
        
        self.coordinator = InstanceCoordinator(queue)

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
        await self._server.wait_closed()

    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        logger.info("WebSocket 服务已停止")

    async def _handle_connection(self, websocket, *args):
        connection_id = f"frontend_{id(websocket)}"
        self.connections[connection_id] = websocket
        self.subscriptions[connection_id] = set()

        logger.info(f"[{connection_id}] 连接建立")

        await self._send_to_client(connection_id, {
            'type': 'channel_list',
            'data': self.channel_manager.get_all_channels()
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
            for instance, status in list(self.coordinator.ready_status.items()):
                for char_id, info in list(status.get('players', {}).items()):
                    if info.get('connection_id') == connection_id:
                        self.coordinator.unregister_player(instance, char_id)
                if status.get('field_connection_id') == connection_id:
                    self.coordinator.unregister_field(instance)
            
            for topic in list(self.subscriptions.get(connection_id, [])):
                self.queue.unsubscribe(topic, connection_id)
            self.connections.pop(connection_id, None)
            self.subscriptions.pop(connection_id, None)
            logger.info(f"[{connection_id}] 连接断开")

    async def _handle_client_message(self, connection_id: str, message: str, callback):
        try:
            data = json.loads(message)
            action = data.get('action')

            if action == 'subscribe':
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

            elif action == 'subscribe_lobby':
                instance = data.get('instance')
                if instance:
                    topic = f"/lobby/{instance}"
                    self.subscriptions[connection_id].add(topic)
                    self.queue.subscribe(topic, connection_id, callback)
                    status = self.coordinator.get_lobby_status(instance)
                    await self._send_to_client(connection_id, {
                        'type': 'lobby_status',
                        'data': status
                    })
                    logger.info(f"[{connection_id}] 订阅大厅: {instance}")

            elif action == 'create_world':
                channel_id = data.get('channel_id')
                name = data.get('name', '新世界')
                template = data.get('template', 'island')
                
                if channel_id is None:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '缺少 channel_id'
                    })
                    return
                
                if self.channel_manager.is_world_name_exists(name):
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': f'世界名 "{name}" 已存在'
                    })
                    return
                
                world = self.channel_manager.create_world(channel_id, name, template)
                if world:
                    channel = self.channel_manager.get_channel(channel_id)
                    channel_topic = channel.get_channel_topic() if channel else None
                    
                    await self._send_to_client(connection_id, {
                        'type': 'world_created',
                        'data': {
                            'channel_id': channel_id,
                            'world': world.__dict__,
                            'channel_topic': channel_topic
                        }
                    })
                    await self._broadcast_channel_list()
                else:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '创建世界失败 (频道已被占用或不存在)'
                    })

            elif action == 'delete_world':
                channel_id = data.get('channel_id')
                if channel_id is None:
                    return
                self.channel_manager.delete_world(channel_id)
                await self._broadcast_channel_list()

            elif action == 'join_world':
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
                
                channel_id = channel.id
                if channel.is_full():
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': f'世界 "{world_name}" 已满 ({channel.max_characters} 人)'
                    })
                    return
                
                if not self.channel_manager.add_character(channel_id, character_id, character_name, icon):
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': '加入世界失败'
                    })
                    return
                
                channel_topic = channel.get_channel_topic()
                self.queue.publish(channel_topic, {
                    'type': 'character_joined',
                    'character_id': character_id,
                    'character_name': character_name,
                    'icon': icon
                })
                
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
                    if channel and channel.has_world():
                        channel_topic = channel.get_channel_topic()
                        self.queue.publish(channel_topic, {
                            'type': 'character_left',
                            'character_id': character_id
                        })
                
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

            elif action == 'ready':
                instance = data.get('instance')
                role = data.get('role')
                character_id = data.get('character_id')
                character_name = data.get('character_name')
                channel_id = data.get('channel_id')
                world_name = data.get('world_name')
                
                if not instance or not role:
                    await self._send_to_client(connection_id, {
                        'type': 'error',
                        'message': 'ready 消息缺少 instance 或 role'
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
                    self.coordinator.start_game(instance, connection_id)
                    await self._send_to_client(connection_id, {
                        'type': 'start_game_ack',
                        'instance': instance,
                        'status': 'started'
                    })

            elif action == 'get_lobby_status':
                instance = data.get('instance')
                if instance:
                    status = self.coordinator.get_lobby_status(instance)
                    await self._send_to_client(connection_id, {
                        'type': 'lobby_status',
                        'data': status
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
        logger.info(f"预设频道: {self.channel_manager.MAX_CHANNELS} 个")
        logger.info(f"每频道上限: {self.channel_manager.MAX_CHARACTERS_PER_CHANNEL} 人")
        logger.info(f"实例协调器已启用 (房主确认模式)")

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
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        broker.stop()
        logger.info("已退出")


if __name__ == '__main__':
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8765

    print("=" * 60)
    print("SurvX 消息队列服务器")
    print("=" * 60)
    print(f"WebSocket: ws://{host}:{port}")
    print(f"预设频道: {ChannelManager.MAX_CHANNELS} 个")
    print(f"每频道上限: {ChannelManager.MAX_CHARACTERS_PER_CHANNEL} 人")
    print("实例协调器: 房主确认模式")
    print("按 Ctrl+C 退出")
    print("=" * 60)

    start_server(host, port)