import os
from pathlib import Path

for require in ['yt-dlp', 'ffmpeg']:
    assert any(os.path.exists(os.path.join(p, require))
               for p in os.environ['PATH'].split(os.pathsep)), \
        'You are missing the required dependency: ' + require

MAX_STARS = 2
# (if applicable)
# don't forget to adjust the easter egg values in results.jinja2

# maximum number of concurrent connections per userscript user
MAX_USERSCRIPT_SLOTS = 3

RANK_FILE_DEFAULT_EXT = '.png'

TTV_TOKEN = os.environ['TTV_TOKEN']
TTV_USERNAME = os.environ['TTV_USERNAME']
TTV_CHANNEL = os.environ['TTV_CHANNEL']

VOTE_WHITELIST = set(u.strip() for u in os.getenv('VOTE_WHITELIST', '').lower().split(','))
NO_MONITOR = os.getenv('NO_MONITOR') == '1'
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

RANKS_DIR = DATA_DIR / Path('ranks')
RANKS_DIR.mkdir(exist_ok=True)

DOWNLOAD_DIR = DATA_DIR / Path('download')
DOWNLOAD_DIR.mkdir(exist_ok=True)

BOARDS_DIR = DATA_DIR / Path('boards')
BOARDS_DIR.mkdir(exist_ok=True)

# ensure proper directory permissions
for dir in [DOWNLOAD_DIR, BOARDS_DIR]:
    assert os.access(dir, os.W_OK | os.X_OK), f'Permission denied: {dir}'
