import re
import traceback
from pprint import pprint

from openai import ChatCompletion

from config import APP_NAME, MAX_STARS, N_TOP_USERS, OPENAI_KEY


class Commentator:
    def __init__(self):
        assert MAX_STARS == 2, 'Update the scoring system below if you change MAX_STARS'

        system = f'''
You provide joyful and fun insights for a guess-a-rank type of game called "{APP_NAME}" - the goal is to guess the competitive rank of a gamer in the clip.

You provide 2 - 3, short insights per clip from the given information.

You use easy to understand language.

You sometimes make subtle jokes.

Teo is the Twitch streamer and Chat is his Twitch chat. They compete against each other. Chat has its own leaderboard, to showcase the best individuals.

Each game consists of a number of clips. Your insights are displayed after each clip, alongside the scores.

The first line indicates the current game state.

If it's the end of the game, you congratulate the winner in a fun way.

The maximum possible score per clip is {MAX_STARS} stars. The maximum possible total score is N * {MAX_STARS} stars.

Scoring system: 2 stars for a correct guess, 1 star for a slightly incorrect guess, 0 stars for an incorrect guess.

It's possible to tie by having the same score.

You format your answer in this style, so it's easy to parse programmatically:
- insight 1
- insight 2
...
'''.strip()

        self._messages = [
            {'role': 'system', 'content': system},
        ]

    async def comment(self, vote) -> list[str] | None:
        from vote import Vote
        assert isinstance(vote, Vote)

        if not OPENAI_KEY:
            return None

        prompt = (f'''
Clip {vote.clip_idx + 1} of {len(vote.clips)}{' (start of the game)' if vote.clip_idx == 0 else ''}{' (end of the game)' if vote.clip_idx + 1 == len(vote.clips) else ''}

Teo total score: {vote.total_streamer_stars} stars
Teo clip score: {vote.result.streamer_stars} stars
Chat total score: {vote.total_users_stars} stars
Chat clip score: {vote.result.users_stars} stars

Top {N_TOP_USERS} leaderboard (total: {vote.total_users_votes} users):
''' + '\n'.join(
            f'#{n} "{score.username}" total score: {score.stars} stars'
            for n, score in vote.result.top_users
        )).strip()

        self._messages.append({'role': 'user', 'content': prompt})

        try:
            completion = await ChatCompletion.acreate(
                model='gpt-3.5-turbo',
                messages=self._messages,
                temperature=0.7,  # more randomness
                max_tokens=128,
                frequency_penalty=0.2,  # less repetition
                presence_penalty=0.2,  # more diversity
                timeout=10,
            )
        except:
            pprint(self._messages)
            traceback.print_exc()
            return None

        response = completion.choices[0].message.content

        self._messages.append({'role': 'assistant', 'content': response})

        result = [
            l.strip()
            for l in re.split(r'^\s*-\s+', response, flags=re.MULTILINE)
            if l.strip()
        ]

        if len(result) < 2:
            pprint(self._messages)
            return None

        return result
