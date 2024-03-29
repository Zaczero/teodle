import traceback
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from time import time

from dacite import Config, from_dict
from tinydb import Query

from config import (CLIPS_PATH, CLIPS_REPLAY_PATH, DB, FRIENDS, MAX_STARS,
                    SUMMARY_MIN_VOTES, TTV_CHANNEL, FriendConfig)
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

    @property
    def date_str(self) -> str:
        return datetime.fromtimestamp(self.date, tz=UTC).strftime('%d %b %Y')

    def get_extra_states(self) -> None:
        return None


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


def get_summary(channel: str | None = None) -> list[SummaryEntry]:
    summary_table = DB.table('summary')
    summary = sorted([from_dict(SummaryEntry, d, config=Config(check_types=False)) for d in summary_table.all()],
                     key=lambda e: e.date,
                     reverse=True)

    if channel is None or channel == TTV_CHANNEL:
        return summary

    return [state for e in summary if (state := e.friend_states.get(channel, None)) is not None]


def is_game_available(channel: str) -> bool:
    summary = get_summary()

    if channel == TTV_CHANNEL:
        # is host
        if not summary:
            return True

        last = summary[0]

        return CLIPS_PATH.stat().st_mtime > last.date

    else:
        # is friend
        if not CLIPS_REPLAY_PATH.is_file() or CLIPS_REPLAY_PATH.stat().st_size == 0:
            return False

        if not summary:
            return False

        last = summary[0]

        return channel not in last.friend_states


def update_summary(vote: Vote) -> bool:
    assert vote.state == VoteState.RESULTS

    if vote.total_users_votes < SUMMARY_MIN_VOTES:
        return False

    now = int(time())
    top_user_score = vote.result.top_users[0][1]

    summary_table = DB.table('summary')

    if vote.friend_config.channel == TTV_CHANNEL:
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

    else:
        last = get_summary()[0]
        last.friend_states[vote.friend_config.channel] = FriendState(
            date=now,
            streamer_stars=vote.total_streamer_stars,
            users_stars=vote.total_users_stars,
            top_user=TopUser(
                username=top_user_score.username,
                stars=top_user_score.stars,
                stars_history=top_user_score.stars_history
            )
        )

        entry = Query()
        summary_table.update(asdict(last), entry.date == last.date)

    return True
