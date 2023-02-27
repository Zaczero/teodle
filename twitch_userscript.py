from asyncio import FIRST_COMPLETED, sleep, wait
from collections import defaultdict
from typing import Callable

import orjson
from fastapi import APIRouter

from clip_state import ClipState
from config import MAX_USERSCRIPT_SLOTS
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

    func_on_disconnect: list[Callable] = []

    @property
    def identifier(self) -> str:
        return f'{super().identifier} @ {self.username}'

    async def on_connect(self) -> None:
        addr = self.ws.client.host

        if not addr_slots[addr].inc():
            raise Exception(f'Too many connections (host={addr})')

        self.func_on_disconnect.append(lambda: addr_slots[addr].dec())

    async def on_receive(self, data: dict) -> None:
        assert self.task is None, 'Unexpected receive'
        assert 'username' in data, 'Missing username'

        username = normalize_username(data['username'])

        # Twitch usernames must be between 4 and 25 characters
        assert 4 <= len(username) <= 25, f'Invalid username: {username}'

        self.username = username

        if not user_slots[self.username].inc():
            raise Exception(f'Too many connections (user={self.username})')

        self.func_on_disconnect.append(lambda: user_slots[self.username].dec())

        await self.start()

    async def on_disconnect(self) -> None:
        await super().on_disconnect()

        for func in self.func_on_disconnect:
            func()

    async def loop(self) -> None:
        with \
                Subscription(TYPE_CLIP_STATE) as s_clip, \
                Subscription(TYPE_USER_VOTE_STATE(self.username)) as s_vote, \
                Subscription(TYPE_USER_SCORE(self.username)) as s_score:

            clip: ClipState | None = None
            vote: UserVoteState | None = None
            score: int | None = None

            s_clip_wait = s_clip.wait()
            s_vote_wait = s_vote.wait()
            s_score_wait = s_score.wait()

            while self.connected:
                done, _ = await wait((s_clip_wait, s_vote_wait, s_score_wait), return_when=FIRST_COMPLETED)

                if s_clip_wait in done:
                    clip = await s_clip_wait
                    s_clip_wait = s_clip.wait()

                if s_vote_wait in done:
                    vote = await s_vote_wait
                    s_vote_wait = s_vote.wait()

                if s_score_wait in done:
                    score = await s_score_wait
                    s_score_wait = s_score.wait()

                if clip is not None:
                    json = orjson.dumps({
                        'clip': clip,
                        'vote': vote,
                        'score': score
                    })

                    await self.ws.send_bytes(json)

                await sleep(0.2)
