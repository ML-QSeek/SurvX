# -*- coding: utf-8 -*-
"""
ws_test.py

WebSocket 广播自动化测试。

用法:
    python ws_test.py <频道名> <客户端名> [发送条数]

示例:
    # 终端 A
    python ws_test.py news A 5

    # 终端 B
    python ws_test.py news B 5
"""

import asyncio
import sys

import websockets


async def client(uri, name, count):
    async with websockets.connect(uri) as ws:
        print(f"[{name}] 已连接 {uri}")

        # 后台收消息
        async def recv():
            try:
                async for msg in ws:
                    print(f"[{name} 收到] {msg}")
            except websockets.ConnectionClosed:
                pass

        recv_task = asyncio.create_task(recv())

        # 每隔 1 秒发一条
        for i in range(count):
            await asyncio.sleep(1)
            msg = f"{name}-{i}"
            await ws.send(msg)
            print(f"[{name} 发送] {msg}")

        # 再等 2 秒，收完别人的广播
        await asyncio.sleep(2)
        recv_task.cancel()


async def main():
    if len(sys.argv) < 3:
        print("用法: python ws_test.py <频道名> <客户端名> [发送条数]")
        sys.exit(1)

    channel = sys.argv[1]
    name = sys.argv[2]
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    uri = f"ws://localhost:8000/ws/{channel}"
    await client(uri, name, count)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[退出]")