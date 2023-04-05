from asyncio import FIRST_COMPLETED, CancelledError, create_task, sleep, wait
from collections import defaultdict
from typing import Callable

import orjson
from fastapi import APIRouter, WebSocket

from clip_state import ClipState
from config import FRIENDS, MAX_USERSCRIPT_SLOTS, TTV_CHANNEL
from events import (TYPE_CLIP_STATE, TYPE_USER_SCORE, TYPE_USER_VOTE_STATE,
                    Subscription)
from user_vote_state import UserVoteState
from utils import normalize_username
from ws_route import WSLoopTaskRoute

router = APIRouter(prefix='/userscript')


class Counter:
    _counter: int = 0

    def inc(self) -> bool:
        if self._counter < MAX_USERSCRIPT_SLOTS:
            self._counter += 1
            return True

        return False

    def dec(self) -> None:
        self._counter -= 1


user_slots: dict[str, Counter] = defaultdict(Counter)
addr_slots: dict[str, Counter] = defaultdict(Counter)


@router.websocket('/ws')
class WS(WSLoopTaskRoute):
    username: str = ''
    channel: str = ''
    func_on_disconnect: list[Callable]

    def __init__(self, ws: WebSocket):
        super().__init__(ws)
        self.func_on_disconnect = []

    @property
    def identifier(self) -> str:
        return f'{super().identifier} @ {self.channel} : {self.username}'

    async def on_connect(self) -> None:
        addr = self.ws.client.host

        if not addr_slots[addr].inc():
            raise Exception(f'Too many connections (host={addr})')

        self.func_on_disconnect.append(lambda: addr_slots[addr].dec())

    async def on_receive(self, data: dict) -> None:
        assert self.task is None, 'Unexpected receive'
        assert 'username' in data, 'Missing username'

        # TODO: in later release
        # assert 'channel' in data, 'Missing channel'

        username = normalize_username(data['username'])

        # Twitch usernames must be between 4 and 25 characters
        assert 4 <= len(username) <= 25, f'Invalid username: {username}'

        channel = data.get('channel', TTV_CHANNEL)

        # Channel must be valid
        assert any(f.channel == channel for f in FRIENDS), f'Invalid channel: {channel}'

        self.username = username
        self.channel = channel

        if not user_slots[self.username].inc():
            raise Exception(f'Too many connections (user={self.username})')

        self.func_on_disconnect.append(lambda: user_slots[self.username].dec())

        await self.start()

    async def on_disconnect(self) -> None:
        await super().on_disconnect()

        for func in self.func_on_disconnect:
            func()

    async def loop(self) -> None:
        await self.ws.send_text('ok')

        with \
                Subscription(TYPE_CLIP_STATE(self.channel)) as s_clip, \
                Subscription(TYPE_USER_VOTE_STATE(self.channel, self.username)) as s_vote, \
                Subscription(TYPE_USER_SCORE(self.channel, self.username)) as s_score:

            clip: ClipState | None = None
            vote: UserVoteState | None = None
            score: int | None = None

            s_clip_wait = create_task(s_clip.wait())
            s_vote_wait = create_task(s_vote.wait())
            s_score_wait = create_task(s_score.wait())

            while self.connected:
                try:
                    done, _ = await wait((s_clip_wait, s_vote_wait, s_score_wait), return_when=FIRST_COMPLETED)
                except CancelledError as e:
                    s_clip_wait.cancel()
                    s_vote_wait.cancel()
                    s_score_wait.cancel()
                    raise e

                if s_clip_wait in done:
                    clip = s_clip_wait.result()
                    s_clip_wait = create_task(s_clip.wait())

                if s_vote_wait in done:
                    vote = s_vote_wait.result()
                    s_vote_wait = create_task(s_vote.wait())

                if s_score_wait in done:
                    score = s_score_wait.result()
                    s_score_wait = create_task(s_score.wait())

                if clip is not None:
                    json = orjson.dumps({
                        'clip': vars(clip) if clip else None,
                        'vote': vars(vote) if vote else None,
                        'score': score
                    })

                    await self.ws.send_bytes(json)

                await sleep(0.2)
