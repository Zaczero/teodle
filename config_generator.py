import re
import traceback
from hashlib import blake2b
from pathlib import Path
from pprint import pprint

from openai import ChatCompletion

from config import CACHE_DIR, OPENAI_KEY, RANKS_DIR


def get_dir_names(dir_path: Path) -> list[str]:
    return list(path.name for path in dir_path.iterdir() if path.is_dir())


def get_file_names(dir_path: Path, file_types: set[str] = {'.png', '.webp'}) -> list[str]:
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
    gameFull = match.group('full')
    gameShort = match.group('short')

    if gameShort not in games:
        return f'Unknown game, response: {response}'

    if username not in input:
        return f'Username not found in input, response: {response}'

    ranks = get_file_names(RANKS_DIR / gameShort)
    ranks_join = '\n'.join(ranks)

    system = 'Sort list of ranks from given game from lowest skill level to highest skill level'
    user = f'''{gameFull}:\n{ranks_join}'''

    messages = [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': '''Counter-Strike: Global Offensive:
silverelite
global
mge
silver
supreme
dmg
lem
mg
nova'''},
        {'role': 'assistant', 'content': '''silver
silverelite
nova
mg
mge
dmg
lem
supreme
global'''},
        {'role': 'user', 'content': user},
    ]

    response = await complete(messages)
    lines = response.splitlines()

    if len(lines) < 0.9 * len(ranks):
        return response

    ranks = [l for l in lines if l in ranks] + [r for r in ranks if r not in lines]
    ranks_join = '\n'.join(ranks)

    input = input.replace(username, '')
    input = re.sub(r'\s+', ' ', input).strip()

    system = '''In query find game rank, from list find entry which is closest match

Output format CSV:
entry'''
    user = f'''{input}\n{gameFull}:\n{ranks_join}'''

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
        f'*{gameShort}/{r}' if r == response else f'{gameShort}/{r}'
        for r in ranks
    )

    return f'''{url}\n{username}\n{config_ranks_join}'''
