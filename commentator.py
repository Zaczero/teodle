import re
import traceback
from pprint import pprint

from openai import ChatCompletion

from config import APP_NAME, MAX_STARS, OPENAI_KEY


class Commentator:
    def __init__(self):
        system = f"""
You provide interesting and joyful commentary for a guess-a-rank type of game called "{APP_NAME}".

Your say no more than 3 sentences.

What you say is logically correct.

Teo is the Twitch streamer and Chat is his Twitch chat. They compete against each other.

Each game consists of a number of clips. Your commentary is displayed after each clip, alongside the leaderboard.

The first line indicates the current game state, if it's clip N of N, it means it's the end of the game.

The maximum possible score per clip is {MAX_STARS} stars.
""".strip()

        self._story = [
            {'role': 'system', 'content': system},
        ]

    async def comment(self, vote) -> list[str] | None:
        from vote import Vote
        assert isinstance(vote, Vote)

        if not OPENAI_KEY:
            return None

        prompt = f"""
Clip {vote.clip_idx + 1} of {len(vote.clips)}
Teo total score: {vote.total_streamer_stars} stars
Teo clip score: {vote.result.streamer_stars} stars
Chat total score: {vote.total_users_stars} stars
Chat clip score: {vote.result.users_stars} stars
""".strip()

        self._story.append({'role': 'user', 'content': prompt})

        try:
            completion = await ChatCompletion.acreate(
                model='gpt-3.5-turbo',
                messages=self._story,
                temperature=1.0,
                max_tokens=256,
                timeout=10,
            )
        except:
            pprint(self._story)
            traceback.print_exc()
            return None

        response = completion.choices[0].message.content

        self._story.append({'role': 'assistant', 'content': response})

        # format for HTML: after each sentence add a new line
        return re.sub(r'([.?!])\s', r'\1<SEP>', response).split('<SEP>')
