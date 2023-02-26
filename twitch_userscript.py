from asyncio import sleep
from collections import defaultdict

from fastapi import APIRouter

from config import MAX_USERSCRIPT_SLOTS
from utils import normalize_username
from ws_route import WSLoopTaskRoute

router = APIRouter(prefix='/userscript')

user_slots: dict[str, int] = defaultdict(int)
addr_slots: dict[str, int] = defaultdict(int)


@router.websocket('/ws')
class WS(WSLoopTaskRoute):
    username: str = ''

    @property
    def identifier(self) -> str:
        return f'{super().identifier} @ {self.username}'

    async def on_receive(self, data: dict) -> None:
        assert self.task is None, 'Unexpected receive'
        assert 'username' in data, 'Missing username'

        username = normalize_username(data['username'])

        # Twitch usernames must be between 4 and 25 characters
        assert 4 <= len(username) <= 25, f'Invalid username: {username}'

        self.username = username

        # limit the number of concurrent connections per user
        assert self.user_slots[self.username] < MAX_USERSCRIPT_SLOTS, 'Too many connections (user)'
        assert self.addr_slots[self.ws.client.host] < MAX_USERSCRIPT_SLOTS, 'Too many connections (addr)'

        user_slots[self.username] += 1
        addr_slots[self.ws.client.host] += 1

        await self.start()

    async def on_disconnect(self) -> None:
        await super().on_disconnect()

        user_slots[self.username] -= 1
        addr_slots[self.ws.client.host] -= 1

    async def loop(self) -> None:
        await sleep(0.2)
        ...
