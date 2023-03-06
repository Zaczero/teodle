import re
import traceback
from pprint import pprint

from openai import ChatCompletion

from config import APP_NAME, MAX_STARS, N_TOP_USERS, OPENAI_KEY


class Commentator:
    def __init__(self):
        assert MAX_STARS == 2, 'Update the scoring system below if you change MAX_STARS'

        system = f'''
You provide joyful insights for a guess-a-rank type of game called "{APP_NAME}" - the goal is to guess the competitive rank of a gamer in the clip.

You provide 2-3 insights at a time from the given information. Your insights are quick to read.

You use easy to understand language. What you say is logically correct.

Teo is the Twitch streamer and Chat is his Twitch chat. They compete against each other. Chat has its own leaderboard, to showcase the best individuals.

It's okay to make subtle jokes about Teo's performance.

Each game consists of a number of clips. Your insights are displayed after each clip, alongside the scores.

The first line indicates the current game state, if it's clip N of N, it means it's the end of the game.

The maximum possible score per clip is {MAX_STARS} stars. The maximum possible total score is N * {MAX_STARS} stars.

Scoring system: 2 stars for a correct guess, 1 star for a slightly incorrect guess, 0 stars for an incorrect guess.

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

        prompt = f'''
Clip {vote.clip_idx + 1} of {len(vote.clips)}

Teo total score: {vote.total_streamer_stars} stars
Teo clip score: {vote.result.streamer_stars} stars
Chat total score: {vote.total_users_stars} stars
Chat clip score: {vote.result.users_stars} stars

Top {N_TOP_USERS} leaderboard (total: {vote.total_users_votes} users):
''' + '\n'.join(
            f'#{n} "{score.username}" total score: {score.stars} stars'
            for n, score in vote.result.top_users
        ).strip()

        self._messages.append({'role': 'user', 'content': prompt})

        try:
            completion = await ChatCompletion.acreate(
                model='gpt-3.5-turbo',
                messages=self._messages,
                temperature=1.0,
                max_tokens=128,
                timeout=10,
            )
        except:
            pprint(self._messages)
            traceback.print_exc()
            return None

        response = completion.choices[0].message.content

        self._messages.append({'role': 'assistant', 'content': response})

        return [
            l.strip()
            for l in re.split(r'^\s*-\s+', response, flags=re.MULTILINE)
            if l.strip()
        ]
