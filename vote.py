import re
from pathlib import Path
from random import choice, random
from time import time

from blacklist import Blacklist
from clip import Clip
from clip_state import ClipState
from commentator import Commentator
from config import BLACKLIST_PATH, DUMMY_VOTES
from events import TYPE_CLIP_STATE, TYPE_TOTAL_VOTES, empty_user_state, publish
from rank import Rank
from users_board import ClipResult, UsersBoard
from vote_state import VoteState


class Vote:
    clips: list[Clip]
    board: UsersBoard
    commentator: Commentator

    state: VoteState = VoteState.IDLE
    clip_idx: int = -1
    clip_time: float = 0
    result: ClipResult | None = None
    teo_rank: Rank | None = None

    total_streamer_stars: int = 0
    total_users_stars: int = 0

    comment: list[str] | None = None

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
        self.commentator = Commentator()

        for clip in self.clips:
            assert not blacklist.is_blacklisted(clip.credits), f'Blacklisted user found: {clip.credits}'

        print(f'[VOTE] Loaded {len(self.clips)} clips')
        empty_user_state()
        publish(TYPE_TOTAL_VOTES, 0)
        publish(TYPE_CLIP_STATE, ClipState(self))

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
        else:
            self.teo_rank = None
            self.state = VoteState.VOTING

        publish(TYPE_TOTAL_VOTES, 0)
        publish(TYPE_CLIP_STATE, ClipState(self))
        return self.clip_idx >= 0

    async def end_clip(self) -> None:
        assert self.state == VoteState.VOTING, 'Invalid state'
        assert self.teo_rank is not None, 'Invalid state (teo_rank)'

        for _ in range(DUMMY_VOTES):
            self.cast_user_vote(str(random()), choice(list(r.text for r in self.clip.ranks)))

        self.state = VoteState.RESULTS

        self.result = self.board.calculate_clip_result(self.clip_idx, self.teo_rank)

        self.total_streamer_stars += self.result.streamer_stars
        self.total_users_stars += self.result.users_stars
        publish(TYPE_CLIP_STATE, ClipState(self))

        # None in case the redirect happens before the comment is ready
        self.comment = None
        # temporarily disabled, further work needed
        # self.comment = await self.commentator.comment(self)

    def cast_streamer_vote(self, vote: str) -> None:
        assert self.state == VoteState.VOTING, 'Invalid state'

        vote = vote.lower()
        teo_rank = next((r for r in self.clip.ranks if r.text == vote), None)

        assert teo_rank is not None, f'Invalid vote: {vote}'

        self.teo_rank = teo_rank

    def cast_user_vote(self, username: str, vote: str) -> bool:
        if self.state != VoteState.VOTING:
            return False

        if not self.board.vote(username, vote, self.clip_idx, self.clip_time):
            return False

        publish(TYPE_TOTAL_VOTES, self.total_users_votes)
        return True
