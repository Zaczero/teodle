from dataclasses import asdict
from datetime import datetime

import orjson

from config import DATA_DIR, DB, TTV_CHANNEL
from summary import FriendState, TopUser


def run() -> None:
    # migrate data from summary.json to tinydb
    if (summary_path := DATA_DIR / 'summary.json').exists() and summary_path.stat().st_size > 0:
        data = orjson.loads(summary_path.read_bytes())
        assert isinstance(data, list)
        summary_table = DB.table('summary')
        summary_table.insert_multiple(data)
        summary_path.unlink()

    # migrate SummaryEntry date from str to int timestamp
    summary_table = DB.table('summary')
    for entry in summary_table.all():
        if isinstance(entry['date'], str):
            # parse date string to timestamp
            entry['date'] = int(datetime.strptime(entry['date'], '%d %b %Y').timestamp())
            summary_table.update(entry, doc_ids=[entry.doc_id])

    # migrate top_user data
    summary_table = DB.table('summary')
    for entry in summary_table.all():
        if 'friend_states' not in entry:
            entry['friend_states'] = {
                TTV_CHANNEL: asdict(FriendState(
                    date=entry['date'],
                    streamer_stars=entry['streamer_stars'],
                    users_stars=entry['users_stars'],
                    top_user=TopUser(
                        username=entry['top_user_name'],
                        stars=entry['top_user_stars'],
                        stars_history=entry.get('top_user_stars_history', tuple())
                    )
                ))
            }

            entry.pop('streamer_stars')
            entry.pop('users_stars')
            entry.pop('top_user_name')
            entry.pop('top_user_stars')
            entry.pop('top_user_stars_history', None)
            summary_table.remove(doc_ids=[entry.doc_id])
            summary_table.insert(entry)
