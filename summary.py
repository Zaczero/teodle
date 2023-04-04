import traceback
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from time import time

from dacite import Config, from_dict

from config import (DB, FRIENDS, MAX_STARS, SUMMARY_MIN_VOTES, TTV_CHANNEL,
                    FriendConfig)
from vote import Vote, VoteState


@dataclass(frozen=True, kw_only=True, slots=True)
class TopUser:
    username: str
    stars: int
    stars_history: tuple[str, ...]


@dataclass(frozen=True, kw_only=True, slots=True)
class FriendState:
    date: int
    streamer_stars: int
    users_stars: int
    top_user: TopUser


@dataclass(frozen=True, kw_only=True, slots=True)
class SummaryEntry:
    date: int
    max_stars: int
    friend_states: dict[str, FriendState]

    @property
    def date_str(self) -> str:
        return datetime.fromtimestamp(self.date, tz=UTC).strftime('%d %b %Y')

    @property
    def streamer_stars(self) -> int:
        return self.friend_states[TTV_CHANNEL].streamer_stars

    @property
    def users_stars(self) -> int:
        return self.friend_states[TTV_CHANNEL].users_stars

    @property
    def top_user(self) -> TopUser:
        return self.friend_states[TTV_CHANNEL].top_user

    def get_extra_states(self) -> list[tuple[FriendConfig, FriendState | None]]:
        return [
            (config, self.friend_states.get(config.channel, None))
            for config in FRIENDS
            if config.channel != TTV_CHANNEL
        ]


def get_summary() -> list[SummaryEntry]:
    summary_table = DB.table('summary')
    return sorted([from_dict(SummaryEntry, d, config=Config(check_types=False)) for d in summary_table.all()],
                  key=lambda e: e.date,
                  reverse=True)


def update_summary(vote: Vote) -> None:
    assert vote.state == VoteState.RESULTS

    if vote.total_users_votes < SUMMARY_MIN_VOTES:
        return

    now = int(time())
    top_user_score = vote.result.top_users[0][1]

    summary_table = DB.table('summary')
    summary_table.insert(asdict(SummaryEntry(
        date=now,
        max_stars=len(vote.clips) * MAX_STARS,
        friend_states={
            TTV_CHANNEL: FriendState(
                date=now,
                streamer_stars=vote.total_streamer_stars,
                users_stars=vote.total_users_stars,
                top_user=TopUser(
                    username=top_user_score.username,
                    stars=top_user_score.stars,
                    stars_history=top_user_score.stars_history
                )
            )
        }
    )))
