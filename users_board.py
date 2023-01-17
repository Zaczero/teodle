from dataclasses import dataclass
from random import random
from time import time

from clip import Clip
from config import VOTE_WHITELIST
from rank import Rank
from utils import calculate_stars


@dataclass(frozen=True, kw_only=True, slots=True)
class ClipResult:
    teo_stars: int
    users_stars: int
    users_rank: Rank
    users_rank_percentages: dict[Rank, float]
    top_users: list[[int, str, int]]


@dataclass(frozen=True, kw_only=False, slots=True)
class UserVote:
    time: float
    rank: Rank


@dataclass(frozen=True, kw_only=True, slots=True)
class UserScore:
    order: int
    stars: int


class UsersBoard:
    clips: list[Clip]
    state: dict[Clip, dict[str, UserVote]]

    _max_known_clip_idx: int = 0

    def __init__(self, clips: list[Clip]):
        self.clips = clips
        self.state = {c: {} for c in clips}

    def vote(self, username: str, vote: str, clip_idx: int) -> bool:
        assert self._max_known_clip_idx <= clip_idx, f'Invalid clip: {clip_idx}, last is: {self._max_known_clip_idx}'
        self._max_known_clip_idx = clip_idx

        username = username.lower()

        if username in VOTE_WHITELIST:
            username += str(random())
            print(f'[INFO] Whitelisted vote: @{username}')

        vote = vote.lower()
        clip = self.clips[clip_idx]
        user_rank = next((r for r in clip.ranks if r.text == vote), None)

        if user_rank is None:
            return False

        self.state[clip][username] = UserVote(time(), user_rank)
        return True

    def total_votes(self, clip_idx: int) -> int:
        clip = self.clips[clip_idx]
        return len(self.state[clip])

    def calculate_clip_result(self, clip_idx: int, teo_rank: Rank, n_top_users: int = 5) -> ClipResult:
        clip = self.clips[clip_idx]
        votes_per_rank = {r: 0 for r in clip.ranks}

        for user_vote in self.state[clip].values():
            votes_per_rank[user_vote.rank] += 1

        users_rank = max(votes_per_rank.items(), key=lambda t: t[1])[0]

        # switch to correct answer in case of the same amount of votes
        if users_rank != clip.answer and votes_per_rank[users_rank] == votes_per_rank[clip.answer]:
            users_rank = clip.answer

        non_zero_total_votes = max(1, self.total_votes(clip_idx))
        users_rank_percentages = {k: v / non_zero_total_votes for k, v in votes_per_rank.items()}

        indices = clip.indices()
        teo_stars = calculate_stars(indices[teo_rank], clip.answer_idx)
        users_stars = calculate_stars(indices[users_rank], clip.answer_idx)

        users_scores = {}

        for i in range(clip_idx + 1):
            i_clip = self.clips[i]
            i_state = self.state[i_clip]
            i_indices = i_clip.indices()

            for user_order, (username, user_vote) in enumerate(sorted(i_state.items(), key=lambda t: t[1].time)):
                assert isinstance(username, str)
                assert isinstance(user_vote, UserVote)

                user_stars = calculate_stars(i_indices[user_vote.rank], i_clip.answer_idx)

                if username not in users_scores:
                    users_scores[username] = UserScore(order=user_order, stars=user_stars)
                else:
                    users_scores[username].order += user_order
                    users_scores[username].stars += user_stars

        max_order = max((v.order for v in users_scores.values()), default=0)
        sl = list(sorted(users_scores.items(),
                         key=lambda t: (t[1].stars, max_order - t[1].order),
                         reverse=True)[:n_top_users])
        sl += [('<none>', UserScore(order=0, stars=0)) for _ in range(max(n_top_users - len(sl), 0))]

        top_users = [(i + 1, *t) for i, t in enumerate(sl)]

        return ClipResult(
            teo_stars=teo_stars,
            users_stars=users_stars,
            users_rank=users_rank,
            users_rank_percentages=users_rank_percentages,
            top_users=top_users
        )
