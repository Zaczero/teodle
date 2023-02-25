from dataclasses import dataclass
from datetime import datetime

from dataclasses_json import dataclass_json

from config import MAX_STARS, SUMMARY_MIN_VOTES, SUMMARY_PATH
from vote import Vote, VoteState


@dataclass_json
@dataclass(frozen=True, kw_only=True, slots=True)
class SummaryEntry:
    date: str
    teo_stars: int
    users_stars: int
    top_user_name: str
    top_user_stars: int
    max_stars: int


def update_summary(vote: Vote) -> None:
    assert vote.state == VoteState.RESULTS

    if vote.total_users_votes < SUMMARY_MIN_VOTES:
        return

    top_user = vote.result.top_users[0]

    summary = get_summary()
    summary.insert(0, SummaryEntry(
        date=datetime.utcnow().strftime('%d %b %Y'),
        teo_stars=vote.total_teo_stars,
        users_stars=vote.total_users_stars,
        top_user_name=top_user[1].username,
        top_user_stars=top_user[1].stars,
        max_stars=len(vote.clips) * MAX_STARS
    ))

    json = SummaryEntry.schema().dumps(summary, many=True, indent=2)

    with open(SUMMARY_PATH, 'w') as f:
        f.write(json)


def get_summary() -> list[SummaryEntry]:
    with open(SUMMARY_PATH, 'r') as f:
        json = f.read()

    try:
        return SummaryEntry.schema().loads(json, many=True)
    except Exception:
        return []
