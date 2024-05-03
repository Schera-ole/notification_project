import asyncio
import websockets
from settings import Settings

async def spammer():
    async with websockets.connect(f"ws://localhost:{Settings.WS_PORT}") as websocket:
        data = await websocket.recv()

        if data == 'Представьтесь!':
            await websocket.send("Хулиган")

        for _ in range(10):
            await websocket.send("Хулиган: Хулиганское сообщение для всех!")
            await asyncio.sleep(0.1)


loop = asyncio.get_event_loop()
loop.run_until_complete(spammer())
