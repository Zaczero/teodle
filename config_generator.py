import re
import traceback
from hashlib import blake2b
from pathlib import Path
from pprint import pprint

from openai import ChatCompletion

import ai
from config import (CACHE_DIR, OPENAI_KEY, RANK_FILE_CONVERT_EXT,
                    RANK_FILE_EXT, RANKS_DIR)


def get_dir_names(dir_path: Path) -> list[str]:
    return list(path.name for path in dir_path.iterdir() if path.is_dir())


def get_file_names(dir_path: Path, file_types: set[str] = {RANK_FILE_EXT, *RANK_FILE_CONVERT_EXT}) -> list[str]:
    return list(set(path.with_suffix("").name.lower() for path in dir_path.iterdir() if path.suffix in file_types))


async def complete(messages: list, **kwargs) -> None:
    messages_hash = blake2b(str(messages).encode(), digest_size=4, usedforsecurity=False).hexdigest()
    cache_file = CACHE_DIR / f'{messages_hash}.txt'

    if cache_file.exists():
        return cache_file.read_text()

    try:
        completion = await ChatCompletion.acreate(
            model='gpt-3.5-turbo',
            messages=messages,
            temperature=0,  # more randomness
            max_tokens=256,
            frequency_penalty=0,  # less repetition
            presence_penalty=0,  # more diversity
            timeout=10,
            **kwargs
        )

        response: str = completion.choices[0].message.content.strip()
        pprint(response)
    except:
        pprint(messages)
        traceback.print_exc()
        return 'Connection error'

    cache_file.write_text(response)

    return response


async def generate_config(input: str) -> str | None:
    if not (match := re.search(r'https?://\S+', input)):
        return 'Missing url'

    url = match.group(0)

    input = input[:match.start()] + input[match.end():]
    input = re.sub(r'\b(true|false|null|nil|def|default|\d|\.|,|\-)\b', '', input, flags=re.IGNORECASE)
    input = re.sub(r'\s+', ' ', input).strip()

    if len(input) < 8:
        return 'Too short'

    if len(input) > 128:
        return 'Too long'

    if not OPENAI_KEY:
        return 'Not configured'

    games = get_dir_names(RANKS_DIR)
    games_join = '\n'.join(games)

    system = f'''From input extract information:
username
game

Match game to one of the short names:
{games_join}'

If successful, print CSV:
username,fullname,shortname

If unsuccessful, print an error'''

    messages = [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': '.cs legendary eagle falseJade'},
        {'role': 'assistant', 'content': 'falseJade,Counter-Strike: Global Offensive,cs'},
        {'role': 'user', 'content': 'plat Voot siege,'},
        {'role': 'assistant', 'content': 'Voot,Rainbow Six Siege,r6'},
        {'role': 'user', 'content': 'grafan lol bronze but I play with higer friends (boosted)'},
        {'role': 'assistant', 'content': 'grafan,League of Legends,lol'},
        {'role': 'user', 'content': input},
    ]

    response = await complete(messages)

    if not (match := re.match(r'^(?P<user>.*?),(?P<full>.*?),(?P<short>.*?)$', response)):
        return response

    username = match.group('user')
    game_full = match.group('full')
    game_short = match.group('short')

    if game_short not in games:
        return f'Unknown game, response: {response}'

    if username not in input:
        return f'Username not found in input, response: {response}'

    ranks = get_file_names(RANKS_DIR / game_short)
    ranks_join = '\n'.join(ranks)

    if game_full == 'Rainbow Six Siege':
        response = 'copper\nbronze\nsilver\ngold\nplatinum\nemerald\ndiamond\nchampions'
    elif game_full == 'Valorant':
        response = 'iron\nbronze\nsilver\ngold\nplatinum\ndiamond\nascendant\nimmortal\nradiant'
    else:
        system = 'Sort list of ranks from given game from lowest skill level to highest skill level.'
        user = f'{game_full}:\n{ranks_join}'

        response = await ai.complete(
            system,
            '''Counter-Strike: Global Offensive:
silverelite
global
mge
silver
supreme
dmg
lem
mg
nova''',
            '''silver
silverelite
nova
mg
mge
dmg
lem
supreme
global''',
            user,
            max_tokens=256)

    lines = response.splitlines()

    if len(lines) < 0.9 * len(ranks):
        return response

    ranks = [l for l in lines if l in ranks] + [r for r in ranks if r not in lines]
    ranks_join = '\n'.join(ranks)

    # make ranks needed checking stand out
    ranks = [r if r in lines else f'{r}.checkme' for r in ranks]

    input = input.replace(username, '')
    input = re.sub(r'\s+', ' ', input).strip()

    system = '''In query find game rank, from list find entry which is closest match

Output format CSV:
entry'''
    user = f'''{input}\n{game_full}:\n{ranks_join}'''

    messages = [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': '''query: cs Legendary Eagle

Counter-Strike: Global Offensive:
silver
silverelite
nova
mg
mge
dmg
lem
supreme
global'''},
        {'role': 'assistant', 'content': 'lem'},
        {'role': 'user', 'content': user},
    ]

    response = (await complete(messages)).lower()

    config_ranks_join = '\n'.join(
        f'*{game_short}/{r}' if r == response else f'{game_short}/{r}'
        for r in ranks
    )

    return f'''{url}\n{username}\n{config_ranks_join}'''
