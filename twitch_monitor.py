import traceback
from asyncio import Event, Lock, sleep

import websockets
from websockets.exceptions import ConnectionClosedOK
from websockets.legacy.client import WebSocketClientProtocol

from config import NO_MONITOR, TTV_TOKEN, TTV_USERNAME
from utils import normalize_username
from vote import Vote


class TwitchMonitor:
    lock = Lock()
    run_loop = Event()

    _vote: Vote
    _channel: str = ''

    _socket: WebSocketClientProtocol | None = None

    def load(self, vote: Vote) -> None:
        self._vote = vote

    async def reconnect(self) -> None:
        await self.disconnect()
        await self.connect(self._channel)

    async def disconnect(self) -> None:
        if not self.run_loop.is_set():
            return

        self.run_loop.clear()

        try:
            await self._socket.close()
        except Exception:
            pass

        self._socket = None
        print(f'[TTV] 🔴 Disconnected from @{self._channel}')

    async def connect(self, channel: str) -> None:
        if NO_MONITOR:
            return

        if self._channel != channel:
            await self.disconnect()
            self._channel = channel

        if self.run_loop.is_set():
            return

        timeout = 0.5

        while True:
            try:
                self._socket = await websockets.connect('wss://irc-ws.chat.twitch.tv:443')
                break
            except Exception:
                traceback.print_exc()
                await sleep(timeout)
                timeout = min(timeout * 2, 5)

        self.run_loop.set()
        print(f'[TTV] 🟢 Connected to @{channel}')

    async def loop(self) -> None:
        if NO_MONITOR:
            return

        while True:
            # reset connection if connected
            async with self.lock:
                if self.run_loop.is_set():
                    await self.reconnect()

            await self.run_loop.wait()

            print(f'[TTV] Started monitoring on @{self._channel}')

            try:
                await self._socket.send(f'CAP REQ :twitch.tv/membership')
                await self._socket.send(f'PASS oauth:{TTV_TOKEN}')
                await self._socket.send(f'NICK {TTV_USERNAME}')
                await self._socket.send(f'JOIN #{self._channel}')

                while True:
                    raw = (await self._socket.recv()).strip()
                    parts = raw.split(' ')

                    assert len(
                        parts) >= 2, f'Message contains no spaces: {raw}'

                    if parts[0] == 'PING':
                        nonce = ' '.join(parts[1:])
                        await self._socket.send(f'PONG {nonce}')  # 🏓

                    elif parts[1] == 'PRIVMSG' and parts[2] == f'#{self._channel}':
                        username = normalize_username(parts[0].split('!')[0].lstrip(':'))
                        message = ' '.join(parts[3:]).lstrip(':').lower()

                        if message.startswith('!'):
                            message = message.lstrip('!').strip()

                            # try multiple formats for better compatibility
                            for new_whitespace in ('', '_'):
                                if self._vote.cast_user_vote(username, message.replace(' ', new_whitespace)):
                                    break

                    elif parts[1] in {'JOIN', 'PART', '353'}:
                        pass
                    else:
                        print('[TTV]', raw)

            except ConnectionClosedOK:
                pass
            except Exception:
                traceback.print_exc()
                await sleep(2)

            print(f'[TTV] Stopped monitoring on @{self._channel}')
