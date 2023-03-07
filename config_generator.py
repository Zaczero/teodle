import traceback
from functools import cache
from pprint import pprint

from openai import ChatCompletion

from config import OPENAI_KEY, RANKS_DIR
from utils import tree


@cache
async def generate_config(input: str) -> str | None:
    if len(input) < 32:
        return 'Too short'

    if len(input) > 128:
        return 'Too long'

    if not OPENAI_KEY:
        return 'Not configured'

    filesystem = '\n'.join(tree(RANKS_DIR))

    system = f'''
The current filesystem is:
{filesystem}

You generate configuration files.

From the user input you extract 4 kinds of information:
1. URL
2. Username
3. Game name
4. Competitive rank name from that game

The first line of the configuration simply contains the URL.

The second line of the configuration simply contains the username.

The remaining configuration are rank files. Inside the filesystem, you find game directories with their corresponding rank files. You list the rank files in the game directory which is specified by the input. The ranks must be ordered from the lowest skill level to the highest skill level.

The rank line which is specified by the input (or the closest one if not found) is prefixed with a * character.

You must only use names of the ranks as specified in the filesystem. Each path must be relative and valid and contain the game directory name.

For example Rainbow 6 Siege Gold 3 will output:
r6/copper
r6/bronze
r6/silver
*r6/gold
r6/platinum
r6/emerald
r6/diamond
r6/champions

For example CSGO Gold Nova Master will output:
cs/silver
cs/silverelite
*cs/nova
cs/mg
cs/mge
cs/dmg
cs/lem
cs/supreme
cs/global

For example val plat will output:
val/iron
val/bronze
val/silver
val/gold
*val/platinum
val/diamond
val/ascendant
val/immortal
val/radiant

For example Overwatch Bronze 1 will output:
*ow/bronze
ow/silver
ow/gold
ow/platinum
ow/diamond
ow/master
ow/grandmaster
ow/top500

You don't add any boilerplate in the output as it breaks the configuration.
'''.strip()

    messages = [
        {'role': 'system', 'content': system},
        {'role': 'user', 'content': input},
    ]

    try:
        completion = await ChatCompletion.acreate(
            model='gpt-3.5-turbo',
            messages=messages,
            temperature=0,  # more randomness
            max_tokens=256,
            frequency_penalty=0,  # less repetition
            presence_penalty=0,  # more diversity
            timeout=10,
        )
    except:
        pprint(messages)
        traceback.print_exc()
        return 'Something went wrong'

    response = completion.choices[0].message.content

    return response
