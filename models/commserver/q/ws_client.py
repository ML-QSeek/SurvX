# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 15:19:53 2026

@author: Administrator
"""

# -*- coding: utf-8 -*-
"""
ws_client.py

WebSocket 广播测试客户端。
连上频道后，一边收广播，一边可以手动发消息。
"""

import asyncio
import sys

import websockets


CHANNEL = "news"
URI = f"ws://localhost:8000/ws/{CHANNEL}"


async def receive_loop(ws):
    """一直收消息，收到就打印"""
    try:
        async for msg in ws:
            print(f"\n[收到广播] {msg}")
            print("> ", end="", flush=True)
    except websockets.ConnectionClosed:
        print("\n[连接已关闭]")


async def send_loop(ws):
    """从命令行读输入，发出去"""
    loop = asyncio.get_event_loop()
    while True:
        # 在终端里读一行（不阻塞事件循环）
        line = await loop.run_in_executor(None, sys.stdin.readline)
        line = line.strip()
        if not line:
            continue
        if line in ("/quit", "/exit"):
            await ws.close()
            break
        await ws.send(line)


async def main():
    print(f"[连接] {URI}")
    async with websockets.connect(URI) as ws:
        print(f"[已连接] 频道: {CHANNEL}")
        print("输入消息回车发送，/quit 退出\n")

        # 收、发两个协程并行
        recv_task = asyncio.create_task(receive_loop(ws))
        send_task = asyncio.create_task(send_loop(ws))

        done, pending = await asyncio.wait(
            [recv_task, send_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[退出]")