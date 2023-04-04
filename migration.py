from datetime import datetime

import orjson

from config import DATA_DIR, DB


def run() -> None:
    # migrate data from summary.json to tinydb
    if (summary_path := DATA_DIR / 'summary.json').exists():
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
