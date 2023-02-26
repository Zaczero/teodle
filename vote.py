import re
from asyncio import Event
from enum import Enum
from pathlib import Path
from random import choice, random
from time import time

from blacklist import Blacklist
from clip import Clip
from config import BLACKLIST_PATH, DUMMY_VOTES
from rank import Rank
from users_board import ClipResult, UsersBoard


class VoteState(Enum):
    IDLE = 0
    VOTING = 1
    RESULTS = 2


class Vote:
    clips: list[Clip]
    board: UsersBoard

    state: VoteState = VoteState.IDLE
    clip_idx: int = -1
    clip_time: float = 0
    result: ClipResult | None = None
    teo_rank: Rank | None = None

    total_teo_stars: int = 0
    total_users_stars: int = 0

    _cast_user_vote_event = Event()

    def __init__(self, path_or_text: Path | str, blacklist: Blacklist | None = None) -> None:
        if isinstance(path_or_text, str):
            text = path_or_text
        else:
            with open(path_or_text) as f:
                text = f.read()

        if blacklist is None:
            blacklist = Blacklist(BLACKLIST_PATH)

        text = re.sub(r'[\t\r]', '', text)

        self.clips = [Clip(t) for t in text.split('\n\n') if t]
        self.board = UsersBoard(self.clips)

        for clip in self.clips:
            assert not blacklist.is_blacklisted(clip.credits), f'Blacklisted user found: {clip.credits}'

        print(f'[VOTE] Loaded {len(self.clips)} clips')

    @property
    def clip(self) -> Clip:
        return self.clips[self.clip_idx]

    @property
    def has_next_clip(self) -> bool:
        return self.clip_idx + 1 < len(self.clips)

    @property
    def total_users_votes(self) -> int:
        return self.board.total_votes(self.clip_idx)

    def begin_next_clip(self) -> bool:
        assert self.state in {VoteState.IDLE, VoteState.RESULTS}, 'Invalid state'

        self.clip_idx += 1
        self.clip_time = time()

        if self.clip_idx >= len(self.clips):
            self.clip_idx = -1
            self.state = VoteState.IDLE
            return False

        self.teo_rank = None
        self.state = VoteState.VOTING
        return True

    def end_clip(self) -> None:
        assert self.state == VoteState.VOTING, 'Invalid state'
        assert self.teo_rank is not None, 'Invalid state (teo_rank)'

        for _ in range(DUMMY_VOTES):
            self.cast_user_vote(str(random()), choice(list(r.text for r in self.clip.ranks)))

        self.state = VoteState.RESULTS

        self.result = self.board.calculate_clip_result(self.clip_idx, self.teo_rank)

        self.total_teo_stars += self.result.teo_stars
        self.total_users_stars += self.result.users_stars

    def cast_teo_vote(self, vote: str) -> None:
        assert self.state == VoteState.VOTING, 'Invalid state'

        vote = vote.lower()
        teo_rank = next((r for r in self.clip.ranks if r.text == vote), None)

        assert teo_rank is not None, f'Invalid vote: {vote}'

        self.teo_rank = teo_rank

    def cast_user_vote(self, username: str, vote: str) -> bool:
        if self.state != VoteState.VOTING:
            return False

        if self.board.vote(username, vote, self.clip_idx, self.clip_time):
            self._cast_user_vote_event.set()
            return True

        return False

    async def wait_user_vote(self) -> None:
        await self._cast_user_vote_event.wait()
        self._cast_user_vote_event.clear()
