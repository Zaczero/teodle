from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from time import time

from config import DB, MAX_STARS, SUMMARY_MIN_VOTES
from vote import Vote, VoteState


@dataclass(frozen=True, kw_only=True, slots=True)
class SummaryEntry:
    date: int
    streamer_stars: int
    users_stars: int
    top_user_name: str
    top_user_stars: int
    top_user_stars_history: tuple[str, ...] = ()
    max_stars: int

    @property
    def date_str(self) -> str:
        return datetime.fromtimestamp(self.date, tz=UTC).strftime('%d %b %Y')


def get_summary() -> list[SummaryEntry]:
    summary_table = DB.table('summary')

    try:
        return sorted([SummaryEntry(**d) for d in summary_table.all()], key=lambda e: e.date, reverse=True)
    except Exception:
        return []


def update_summary(vote: Vote) -> None:
    assert vote.state == VoteState.RESULTS

    if vote.total_users_votes < SUMMARY_MIN_VOTES:
        return

    top_user = vote.result.top_users[0]

    summary_table = DB.table('summary')
    summary_table.insert(asdict(SummaryEntry(
        date=int(time()),
        streamer_stars=vote.total_streamer_stars,
        users_stars=vote.total_users_stars,
        top_user_name=top_user[1].username,
        top_user_stars=top_user[1].stars,
        top_user_stars_history=top_user[1].stars_history,
        max_stars=len(vote.clips) * MAX_STARS
    )))
