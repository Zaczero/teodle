import traceback
from asyncio import CancelledError, Task, create_task
from contextlib import suppress
from typing import Generator

import starlette.status as status
from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocket, WebSocketDisconnect, WebSocketState


class WSRoute:

    def __init__(self, ws: WebSocket):
        self.ws = ws

    def __await__(self) -> Generator:
        return self.dispatch().__await__()

    @property
    def connected(self) -> bool:
        return self.ws.client_state == WebSocketState.CONNECTED

    async def dispatch(self) -> None:
        await self.ws.accept()

        with suppress(Exception):
            try:
                await self.on_connect()
                while self.connected:
                    data = await self.ws.receive_json()
                    await self.on_receive(data)
            except WebSocketDisconnect:
                pass
            except Exception:
                traceback.print_exc()
                await self.error_disconnect()

        await self.on_disconnect()

    async def on_connect(self) -> None:
        pass

    async def on_disconnect(self) -> None:
        pass

    async def on_receive(self, data: dict) -> None:
        pass

    async def disconnect(self, message: str = '') -> None:
        await self.ws.close(status.WS_1000_NORMAL_CLOSURE, message)

    async def error_disconnect(self, message: str = 'Internal error') -> None:
        await self.ws.close(status.WS_1011_INTERNAL_ERROR, message)


class WSTaskRoute(WSRoute):
    task: Task | None = None

    @property
    def identifier(self) -> str:
        return id(self)

    async def start(self) -> None:
        assert self.task is None, 'Task has already been started'

        self.task = create_task(self.run())

        print(f'[WSTask] Started: {self.identifier}')

    async def on_disconnect(self) -> None:
        await self.stop()
        await super().on_disconnect()

    async def stop(self) -> None:
        if self.task is None:
            return

        if self.task.cancel():
            # never awaited loop (instant disconnect), will not suppress itself
            with suppress(CancelledError):
                await self.task

        self.loop = None

        print(f'[WSTask] Stopped: {self.identifier}')

    async def run(self) -> None:
        pass


class WSLoopTaskRoute(WSTaskRoute):
    async def run(self) -> None:
        print(f'[WSTaskRoute] Loop started: {self.identifier}')

        with suppress(Exception, CancelledError):
            try:
                await self.loop()
            except WebSocketDisconnect:
                pass
            except Exception:
                traceback.print_exc()
                await self.error_disconnect()

        print(f'[WSTaskRoute] Loop stopped: {self.identifier}')

    async def loop(self) -> None:
        pass
