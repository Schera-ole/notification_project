import logging

import asyncio
import websockets

from settings import Settings

peoples = {}  # Словарь будет содержать ник подключившегося человека и указатель на его websocket-соединение.


logging.basicConfig(level=logging.INFO)
logging.info("Сервер запущен")

async def remove_user(name: str) -> None:
    del peoples[name]
    for user in peoples.values():
        await user.send(f'Пользователь {name} покинул чат')


async def welcome(websocket: websockets.WebSocketServerProtocol) -> str:
    await websocket.send('Представьтесь!')
    name = await websocket.recv()
    await websocket.send('Чтобы поговорить, напишите "<имя>: <сообщение>". Например: Ира: купи хлеб.')
    await websocket.send('Посмотреть список участников можно командой "?"')
    peoples[name.strip()] = websocket
    return name


async def receiver(websocket: websockets.WebSocketServerProtocol) -> None:
    name = await welcome(websocket)

    for user in peoples.values():
        await user.send(f'К чату присоединился {name}')

    try:
        while True:
            message = (await websocket.recv()).strip()
            if message == '?':
                await websocket.send(', '.join(peoples.keys()))
                continue
            else:
                try:
                    to, text = message.split(': ', 1)
                except ValueError:
                    await websocket.send(f'Введите корректно необходимую информацию в формате "<имя>: <сообщение>"')
                    continue
                if to in peoples:
                    for user in peoples.values():
                        await user.send(f'Сообщение от {name}: {text}')
                else:
                    await websocket.send(f'Пользователь {to} не найден')
    except websockets.exceptions.ConnectionClosedOK:
        await remove_user(name)


ws_server = websockets.serve(receiver, "0.0.0.0", Settings.WS_PORT)

loop = asyncio.get_event_loop()
loop.run_until_complete(ws_server)
loop.run_forever()
