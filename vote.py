import os
import random
import re
from enum import Enum
from pathlib import Path
from typing import Optional

from clip import Clip
from rank import Rank

MAX_STARS = 2
VOTE_WHITELIST = set(u.strip() for u in os.getenv('VOTE_WHITELIST', '').lower().split(','))


class VoteState(Enum):
    IDLE = 0
    VOTING = 1
    RESULTS = 2


class Vote:
    clips: list[Clip]

    clip_idx: int = -1
    state: VoteState = VoteState.IDLE

    teo_rank: Optional[Rank]
    users_rank: Optional[Rank]
    users_rank_perc: dict[Rank, float]
    users_ranks: dict[str, Rank]

    current_teo_stars: int = 0
    current_users_stars: int = 0

    total_teo_stars: int = 0
    total_users_stars: int = 0

    def __init__(self, path_or_text: Path | str):
        if isinstance(path_or_text, str):
            text = path_or_text
        else:
            with open(path_or_text) as f:
                text = f.read()

        text = re.sub(r'[\t\r]', '', text)

        self.clips = [Clip(t) for t in text.split('\n\n') if t]

        print(f'Loaded {len(self.clips)} clips')

    @property
    def clip(self) -> Clip:
        return self.clips[self.clip_idx]

    @property
    def has_next_clip(self) -> bool:
        return self.clip_idx + 1 < len(self.clips)

    @property
    def total_users_votes(self) -> int:
        return len(self.users_ranks)

    def begin_next_clip(self) -> bool:
        assert self.state in {VoteState.IDLE, VoteState.RESULTS}, 'Invalid state'

        self.clip_idx += 1

        if self.clip_idx >= len(self.clips):
            self.clip_idx = -1
            self.state = VoteState.IDLE
            return False

        clip = self.clips[self.clip_idx]

        self.teo_rank = None
        self.users_rank = None
        self.users_ranks = {}
        self.users_rank_perc = {r: 0 for r in clip.ranks}
        self.current_teo_stars = 0
        self.current_users_stars = 0
        self.state = VoteState.VOTING
        return True

    def end_clip(self) -> None:
        assert self.state == VoteState.VOTING, 'Invalid state'
        assert self.teo_rank is not None, 'Invalid state (teo_rank)'

        self.state = VoteState.RESULTS

        votes_per_rank = {r: 0 for r in self.clip.ranks}

        for user_rank in self.users_ranks.values():
            votes_per_rank[user_rank] += 1

        self.users_rank = max(votes_per_rank.items(), key=lambda t: t[1])[0]
        self.users_rank_perc = {k: v / max(1, self.total_users_votes) for k, v in votes_per_rank.items()}

        clip = self.clips[self.clip_idx]
        indices = {r: i for i, r in enumerate(clip.ranks)}

        self.current_teo_stars = MAX_STARS - min(abs(indices[self.teo_rank] - clip.answer_idx), MAX_STARS)
        self.current_users_stars = MAX_STARS - min(abs(indices[self.users_rank] - clip.answer_idx), MAX_STARS)

        self.total_teo_stars += self.current_teo_stars
        self.total_users_stars += self.current_users_stars

    def cast_teo_vote(self, vote: str) -> None:
        assert self.state == VoteState.VOTING, 'Invalid state'

        vote = vote.lower()
        teo_rank = next((r for r in self.clip.ranks if r.text == vote), None)

        assert teo_rank is not None, f'Invalid vote: {vote}'

        self.teo_rank = teo_rank

    def cast_user_vote(self, username: str, vote: str) -> bool:
        if self.state != VoteState.VOTING:
            return False

        username = username.lower()

        if username in VOTE_WHITELIST:
            username += str(random.random())

        vote = vote.lower()
        user_rank = next((r for r in self.clip.ranks if r.text == vote), None)

        if user_rank is None:
            return False

        self.users_ranks[username] = user_rank
        return True
