import itertools
import os
from pathlib import Path
from typing import NamedTuple

import openai


class FriendConfig(NamedTuple):
    name: str
    icon: str
    good_icon: str
    bad_icon: str
    channel: str

    def configure_ui(self) -> dict[str, str]:
        return UI_CONFIG | {
            'IS_FRIEND': True,
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

FRIENDS = []

for i in itertools.count():
    if (name := os.getenv(f'FRIEND_{i}_NAME')) is None \
            or (icon := os.getenv(f'FRIEND_{i}_ICON')) is None \
            or (good_icon := os.getenv(f'FRIEND_{i}_GOOD_ICON')) is None \
            or (bad_icon := os.getenv(f'FRIEND_{i}_BAD_ICON')) is None \
            or (channel := os.getenv(f'FRIEND_{i}_CHANNEL')) is None:
        break

    FRIENDS.append(FriendConfig(name, icon, good_icon, bad_icon, channel))

print(f'[CONFIG] Loaded {len(FRIENDS)} friend profiles')

VOTE_WHITELIST = set(u.strip() for u in os.getenv('VOTE_WHITELIST', '').lower().split(','))
NO_MONITOR = os.getenv('NO_MONITOR') == '1'
NO_DOWNLOAD = os.getenv('NO_DOWNLOAD') == '1'
NO_AUTO_FINISH = os.getenv('NO_AUTO_FINISH') == '1'
DUMMY_VOTES = int(os.getenv('DUMMY_VOTES', '0'))

DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)

CLIPS_PATH = DATA_DIR / Path('clips.txt')
BLACKLIST_PATH = DATA_DIR / Path('blacklist.txt')

SUMMARY_MIN_VOTES = int(os.getenv('SUMMARY_MIN_VOTES', '5'))
SUMMARY_PATH = DATA_DIR / Path('summary.json')

# ensure proper file permissions
for file in [CLIPS_PATH, BLACKLIST_PATH, SUMMARY_PATH]:
    with open(file, 'a+') as f:
        pass

CACHE_DIR = DATA_DIR / Path('cache')
CACHE_DIR.mkdir(exist_ok=True)

RANKS_DIR = DATA_DIR / Path('ranks')
RANKS_DIR.mkdir(exist_ok=True)

DOWNLOAD_DIR = DATA_DIR / Path('download')
DOWNLOAD_DIR.mkdir(exist_ok=True)

BOARDS_DIR = DATA_DIR / Path('boards')
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
    'IS_FRIEND': False,
    'STREAMER_NAME': 'Teo',
    'STREAMER_ICON': 'teo.png',
    'STREAMER_GOOD_ICON': 'teo-gold.png',  # optional
    'STREAMER_BAD_ICON': 'laugh.png',  # optional
    'FIRST_PLACE_ICON': 'jam.gif',
    'MVP_ICON': 'chad.webp',
    'FRIENDS': FRIENDS
}

# override UI_CONFIG with environment variables
for key, default in UI_CONFIG.items():
    if (val := os.getenv(key, None)) is not None:
        UI_CONFIG[key] = val
