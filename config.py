import itertools
import os
from pathlib import Path
from typing import NamedTuple

import openai
from tinydb import TinyDB

from orjson_storage import ORJSONStorage


class FriendConfig(NamedTuple):
    is_friend: bool
    name: str
    icon: str
    good_icon: str
    bad_icon: str
    channel: str

    def ui_config(self) -> dict[str, str]:
        return UI_CONFIG | {
            'IS_FRIEND': self.is_friend,
            'STREAMER_NAME': self.name,
            'STREAMER_ICON': self.icon,
            'STREAMER_GOOD_ICON': self.good_icon,
            'STREAMER_BAD_ICON': self.bad_icon
        }


for require in ['yt-dlp', 'ffmpeg']:
    assert any(os.path.exists(os.path.join(p, require))
               for p in os.environ['PATH'].split(os.pathsep)), \
        'You are missing the required dependency: ' + require

MAX_STARS = 2
# (if applicable)
# don't forget to adjust the easter egg (STREAMER_GOOD_ICON, STREAMER_BAD_ICON) values in results.jinja2

# maximum number of concurrent connections per userscript user
MAX_USERSCRIPT_SLOTS = 3

RANK_FILE_CONVERT_EXT = {'.png'}
RANK_FILE_EXT = '.webp'

TTV_TOKEN = os.environ['TTV_TOKEN']
TTV_USERNAME = os.environ['TTV_USERNAME']
TTV_CHANNEL = os.environ['TTV_CHANNEL']

VOTE_WHITELIST = set(u.strip() for u in os.getenv('VOTE_WHITELIST', '').lower().split(','))
NO_MONITOR = os.getenv('NO_MONITOR') == '1'
NO_DOWNLOAD = os.getenv('NO_DOWNLOAD') == '1'
NO_AUTO_FINISH = os.getenv('NO_AUTO_FINISH') == '1'
DUMMY_VOTES = int(os.getenv('DUMMY_VOTES', '0'))

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

CLIPS_PATH = DATA_DIR / 'clips.txt'
CLIPS_REPLAY_PATH = DATA_DIR / 'clips_replay.txt'
BLACKLIST_PATH = DATA_DIR / 'blacklist.txt'
DB_PATH = DATA_DIR / 'db.json'

SUMMARY_MIN_VOTES = int(os.getenv('SUMMARY_MIN_VOTES', '5'))

# ensure proper file permissions
for file in [CLIPS_PATH, BLACKLIST_PATH, DB_PATH]:
    with open(file, 'a+') as f:
        pass

CACHE_DIR = DATA_DIR / 'cache'
CACHE_DIR.mkdir(exist_ok=True)

RANKS_DIR = DATA_DIR / 'ranks'
RANKS_DIR.mkdir(exist_ok=True)

DOWNLOAD_DIR = DATA_DIR / 'download'
DOWNLOAD_DIR.mkdir(exist_ok=True)

BOARDS_DIR = DATA_DIR / 'boards'
BOARDS_DIR.mkdir(exist_ok=True)

# ensure proper directory permissions
for dir in [CACHE_DIR, DOWNLOAD_DIR, BOARDS_DIR]:
    assert os.access(dir, os.W_OK | os.X_OK), f'Permission denied: {dir}'

OPENAI_KEY = os.getenv('OPENAI_KEY', None)

if OPENAI_KEY:
    openai.api_key = OPENAI_KEY

N_TOP_USERS = 5


UI_CONFIG = {
    'APP_NAME': 'Teodle',
    'APP_TITLE': 'Teodle',
    'HEAD_PREFIX': 'teo',
    'STREAMER_NAME': 'Teo',
    'STREAMER_ICON': 'teo.png',
    'STREAMER_GOOD_ICON': 'teo-gold.png',  # optional
    'STREAMER_BAD_ICON': 'laugh.png',  # optional
    'FIRST_PLACE_ICON': 'jam.gif',
    'MVP_ICON': 'chad.webp',
    'FRIENDS': []
}

# override UI_CONFIG with environment variables
for key, default in UI_CONFIG.items():
    if (val := os.getenv(key, None)) is not None:
        UI_CONFIG[key] = val

FRIENDS: list[FriendConfig] = UI_CONFIG['FRIENDS']
FRIENDS.append(FriendConfig(
    is_friend=False,
    name=UI_CONFIG['STREAMER_NAME'],
    icon=UI_CONFIG['STREAMER_ICON'],
    good_icon=UI_CONFIG['STREAMER_GOOD_ICON'],
    bad_icon=UI_CONFIG['STREAMER_BAD_ICON'],
    channel=TTV_CHANNEL))

for i in itertools.count():
    if (name := os.getenv(f'FRIEND_{i}_NAME')) is None \
            or (icon := os.getenv(f'FRIEND_{i}_ICON')) is None \
            or (good_icon := os.getenv(f'FRIEND_{i}_GOOD_ICON')) is None \
            or (bad_icon := os.getenv(f'FRIEND_{i}_BAD_ICON')) is None \
            or (channel := os.getenv(f'FRIEND_{i}_CHANNEL')) is None:
        break

    FRIENDS.append(FriendConfig(
        is_friend=True,
        name=name,
        icon=icon,
        good_icon=good_icon,
        bad_icon=bad_icon,
        channel=channel))

print(f'[CONFIG] Loaded 1+{len(FRIENDS) - 1} friend profiles')

DB = TinyDB(DB_PATH, storage=ORJSONStorage)
