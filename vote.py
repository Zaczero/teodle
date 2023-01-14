import re
from enum import Enum
from pathlib import Path
from typing import Optional

from clip import Clip

MAX_STARS = 2


class VoteState(Enum):
    IDLE = 0
    VOTING = 1
    RESULTS = 2


class Vote:
    clips: list[Clip]

    clip_idx: int = -1
    state: VoteState = VoteState.IDLE

    teo_vote: Optional[str]
    users_voted: set[str]
    users_votes: dict[str, int]
    users_votes_percentage: dict[str, float]

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

    def total_users_votes(self) -> int:
        return sum(self.users_votes.values())

    def begin_next_clip(self) -> bool:
        assert self.state in {VoteState.IDLE, VoteState.RESULTS}, 'Invalid state'

        self.clip_idx += 1

        if self.clip_idx >= len(self.clips):
            self.clip_idx = -1
            self.state = VoteState.IDLE
            return False

        clip = self.clips[self.clip_idx]

        self.teo_vote = None
        self.users_voted = set()
        self.users_votes = {r.text: 0 for r in clip.ranks}
        self.users_votes_percentage = {r.text: 0 for r in clip.ranks}
        self.current_teo_stars = 0
        self.current_users_stars = 0
        self.state = VoteState.VOTING
        return True

    def users_vote(self) -> str:
        return next(k for k, v in self.users_votes.items() if v == max(self.users_votes.values()))

    def end_clip(self) -> None:
        assert self.state == VoteState.VOTING, 'Invalid state'
        assert self.teo_vote is not None, 'Invalid state (teo_vote)'

        self.state = VoteState.RESULTS

        total_users_votes = self.total_users_votes()

        self.users_votes_percentage = {k: v / max(1, total_users_votes) for k, v in self.users_votes.items()}

        clip = self.clips[self.clip_idx]
        indices = {r.text: i for i, r in enumerate(clip.ranks)}

        self.current_teo_stars = MAX_STARS - min(abs(indices[self.teo_vote] - clip.answer_idx), MAX_STARS)
        self.current_users_stars = MAX_STARS - min(abs(indices[self.users_vote()] - clip.answer_idx), MAX_STARS)

        self.total_teo_stars += self.current_teo_stars
        self.total_users_stars += self.current_users_stars

    def cast_teo_vote(self, rank: str) -> None:
        assert self.state == VoteState.VOTING, 'Invalid state'
        assert rank in self.users_votes, 'Invalid vote'

        rank = rank.lower()

        self.teo_vote = rank

    def cast_user_vote(self, username: str, rank: str) -> bool:
        if self.state != VoteState.VOTING:
            return False

        if username in self.users_voted:
            return False

        rank = rank.lower()

        if rank not in self.users_votes:
            return False

        self.users_voted.add(username)
        self.users_votes[rank] += 1
        return True
