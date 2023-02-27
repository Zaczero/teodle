from collections import defaultdict
from dataclasses import dataclass
from random import random
from time import time
from typing import NamedTuple

import orjson

from clip import Clip
from config import BOARDS_DIR, SUMMARY_MIN_VOTES, VOTE_WHITELIST
from events import TYPE_USER_SCORE, TYPE_USER_VOTE_STATE, publish
from rank import Rank
from user_vote_state import UserVoteState
from utils import calculate_stars


class UserVote(NamedTuple):
    delay: float
    rank: Rank


@dataclass(frozen=True, kw_only=True, slots=True)
class UserScore:
    username: str
    delay: float
    order: int
    stars: int

    @classmethod
    def dummy(cls) -> 'UserScore':
        return cls(
            username='<none>',
            delay=0,
            order=0,
            stars=0
        )


@dataclass(frozen=True, kw_only=True, slots=True)
class ClipResult:
    teo_stars: int
    users_stars: int
    users_rank: Rank
    users_rank_percentages: dict[Rank, float]
    users_rank_users: dict[Rank, list[str]]
    top_users: list[tuple[int, UserScore]]


class UsersBoard:
    clips: list[Clip]
    state: dict[Clip, dict[str, UserVote]]
    scores: dict[Clip, list[UserScore]]

    _max_known_clip_idx: int = 0

    def __init__(self, clips: list[Clip]):
        self.clips = clips
        self.state = {c: {} for c in clips}
        self.scores = {}

    def vote(self, username: str, vote: str, clip_idx: int, clip_time: float) -> bool:
        assert self._max_known_clip_idx <= clip_idx, f'Invalid clip: {clip_idx}, last is: {self._max_known_clip_idx}'

        self._max_known_clip_idx = clip_idx

        # whitelisted users get a random suffix
        if username in VOTE_WHITELIST:
            username += str(random())
            print(f'[BOARD] Whitelisted vote: @{username}')

        clip = self.clips[clip_idx]

        # count only the first vote
        if username in self.state[clip]:
            return False

        vote = vote.lower()
        vote_delay = time() - clip_time
        user_rank = next((r for r in clip.ranks if r.text == vote), None)

        # use vote as a prefix match for the rank
        if user_rank is None and len(vote) >= 3:
            matched_ranks = list(r for r in clip.ranks if r.text.startswith(vote))

            # if there is only one match, use it
            if len(matched_ranks) == 1:
                vote = matched_ranks[0].text
                user_rank = matched_ranks[0]

        if user_rank is None:
            return False

        # register the vote
        self.state[clip][username] = UserVote(
            delay=vote_delay,
            rank=user_rank
        )

        publish(TYPE_USER_VOTE_STATE(username), UserVoteState(vote=vote, clip_idx=clip_idx))
        return True

    def total_votes(self, clip_idx: int) -> int:
        clip = self.clips[clip_idx]
        return len(self.state[clip])

    def calculate_clip_result(self, clip_idx: int, teo_rank: Rank, n_top_users: int = 5) -> ClipResult:
        clip = self.clips[clip_idx]
        votes_per_rank = {r: 0 for r in clip.ranks}
        users_rank_users = {r: [] for r in clip.ranks}

        for username, user_vote in self.state[clip].items():
            votes_per_rank[user_vote.rank] += 1
            users_rank_users[user_vote.rank].append(username)

        users_rank = max(votes_per_rank.items(), key=lambda t: t[1])[0]

        # switch to correct answer in case of the same amount of votes
        if users_rank != clip.answer and votes_per_rank[users_rank] == votes_per_rank[clip.answer]:
            users_rank = clip.answer

        non_zero_total_votes = max(1, self.total_votes(clip_idx))
        users_rank_percentages = {k: v / non_zero_total_votes for k, v in votes_per_rank.items()}

        indices = clip.indices()
        teo_stars = calculate_stars(indices[teo_rank], clip.answer_idx)
        users_stars = calculate_stars(indices[users_rank], clip.answer_idx)

        # calculate scores for the current clip
        self._calculate_clip_scores(clip_idx)

        # save the scores
        self._save_clip_scores(clip_idx)

        # group all scores into: username -> list of the user scores
        grouped = defaultdict(list)

        for clip_scores in self.scores.values():
            for user_score in clip_scores:
                grouped[user_score.username].append(user_score)

        # calculate the total score for each user
        users_scores = [
            UserScore(
                username=username,
                delay=sum(s.delay for s in scores),
                order=sum(s.order for s in scores),
                stars=sum(s.stars for s in scores)
            )
            for username, scores in grouped.items()
        ]

        # find the max order (we are doing an inverse sort)
        max_order = max((v.order for v in users_scores), default=0)

        # sort by stars and then by order (~ vote time)
        sl = list(sorted(users_scores,
                         key=lambda s: (s.stars, max_order - s.order),
                         reverse=True)[:n_top_users])

        # fill up with dummy users
        sl.extend(UserScore.dummy() for _ in range(max(n_top_users - len(sl), 0)))

        # add the rank (#1, #2, #3, etc.)
        # TODO: namedtuple
        top_users = [(i + 1, s) for i, s in enumerate(sl)]

        # publish the user scores
        for user_score in users_scores:
            publish(TYPE_USER_SCORE(user_score.username), user_score.stars)

        return ClipResult(
            teo_stars=teo_stars,
            users_stars=users_stars,
            users_rank=users_rank,
            users_rank_percentages=users_rank_percentages,
            users_rank_users=users_rank_users,
            top_users=top_users
        )

    def _calculate_clip_scores(self, clip_idx: int) -> None:
        clip = self.clips[clip_idx]

        assert clip not in self.scores, f'Clip {clip_idx} has already been scored'

        state = self.state[clip]
        indices = clip.indices()
        clip_scores = []

        for user_order, (username, user_vote) in enumerate(sorted(state.items(), key=lambda t: t[1].delay)):
            user_stars = calculate_stars(indices[user_vote.rank], clip.answer_idx)

            clip_scores.append(UserScore(
                username=username,
                delay=user_vote.delay,
                order=user_order,
                stars=user_stars
            ))

        self.scores[clip] = clip_scores

        print(f'[BOARD] Calculated scores for clip {clip_idx}')

    def _save_clip_scores(self, clip_idx: int) -> None:
        timestamp = int(time())

        clip = self.clips[clip_idx]
        clip_scores = self.scores[clip]

        # skip save if there are not enough votes (just testing)
        if len(clip_scores) < SUMMARY_MIN_VOTES:
            return

        path = BOARDS_DIR / f'{timestamp}-{clip_idx}.json'
        json = orjson.dumps(clip_scores, option=orjson.OPT_INDENT_2)

        with open(path, 'xb') as f:
            f.write(json)

        print(f'[BOARD] Saved scores for clip {clip_idx} to {path}')
