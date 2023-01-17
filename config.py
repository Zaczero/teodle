import os

MAX_STARS = 2

RANK_FILE_DEFAULT_EXT = '.png'

TTV_TOKEN = os.environ['TTV_TOKEN']
TTV_USERNAME = os.environ['TTV_USERNAME']
TTV_CHANNEL = os.environ['TTV_CHANNEL']

VOTE_WHITELIST = set(u.strip() for u in os.getenv('VOTE_WHITELIST', '').lower().split(','))
NO_MONITOR = os.getenv('NO_MONITOR') == '1'
DUMMY_VOTES = int(os.getenv('DUMMY_VOTES'))
