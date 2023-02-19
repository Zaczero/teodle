import re
from pathlib import Path


def _normalize_username(username: str) -> str:
    return re.sub(r'[^a-z0-9]', '', username.lower())


class Blacklist:
    _blacklist: set[str]

    def __init__(self, path_or_text: Path | str) -> None:
        if isinstance(path_or_text, str):
            text = path_or_text
        else:
            with open(path_or_text) as f:
                text = f.read()

        text = re.sub(r'[\t\r]', '', text)

        self._blacklist = set(
            _normalize_username(t.strip())
            for t in text.splitlines()
            if t.strip()
            and t.strip()[0] != '#'
        )

        print(f'[BLACKLIST] Loaded {len(self._blacklist)} entries')

    def is_blacklisted(self, username: str) -> bool:
        return _normalize_username(username) in self._blacklist
