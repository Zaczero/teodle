from dataclasses import dataclass
from datetime import datetime

import orjson

from config import MAX_STARS, SUMMARY_MIN_VOTES, SUMMARY_PATH
from vote import Vote, VoteState


@dataclass(frozen=True, kw_only=True, slots=True)
class SummaryEntry:
    date: str
    streamer_stars: int
    users_stars: int
    top_user_name: str
    top_user_stars: int
    top_user_stars_history: tuple[str, ...] = ()
    max_stars: int


def update_summary(vote: Vote) -> None:
    assert vote.state == VoteState.RESULTS

    if vote.total_users_votes < SUMMARY_MIN_VOTES:
        return

    top_user = vote.result.top_users[0]

    summary = get_summary()
    summary.insert(0, SummaryEntry(
        date=datetime.utcnow().strftime('%d %b %Y'),
        streamer_stars=vote.total_streamer_stars,
        users_stars=vote.total_users_stars,
        top_user_name=top_user[1].username,
        top_user_stars=top_user[1].stars,
        top_user_stars_history=top_user[1].stars_history,
        max_stars=len(vote.clips) * MAX_STARS
    ))

    json = orjson.dumps(summary, option=orjson.OPT_INDENT_2)

    with open(SUMMARY_PATH, 'wb') as f:
        f.write(json)


def get_summary() -> list[SummaryEntry]:
    with open(SUMMARY_PATH, 'rb') as f:
        json = f.read()

    try:
        return [SummaryEntry(**d) for d in orjson.loads(json)]
    except Exception:
        return []
