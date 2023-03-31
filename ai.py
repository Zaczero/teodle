import asyncio
import traceback
from hashlib import blake2b
from pprint import pprint

from openai import ChatCompletion
from tenacity import retry, stop_after_attempt, wait_exponential

from config import CACHE_DIR, OPENAI_KEY

lock = asyncio.Lock()


@retry(wait=wait_exponential(), stop=stop_after_attempt(5))
async def _complete(messages: list, **kwargs) -> str:
    messages_hash = blake2b(str(messages).encode(), digest_size=4, usedforsecurity=False).hexdigest()
    cache_file = CACHE_DIR / f'{messages_hash}.txt'

    if cache_file.exists():
        return cache_file.read_text()

    try:
        completion = await ChatCompletion.acreate(
            model='gpt-3.5-turbo',
            messages=messages,
            **({
                'temperature': 0,  # more randomness
                'max_tokens': 1024,
                'frequency_penalty': 0,  # less repetition
                'presence_penalty': 0,  # more diversity
                'timeout': 10,
            } | kwargs)
        )

        response: str = completion.choices[0].message.content.strip()
        pprint(response)
    except Exception as e:
        pprint(messages)
        traceback.print_exc()
        raise e

    cache_file.write_text(response)

    return response


async def complete(system: str, *conversation: str, **kwargs) -> str:
    assert len(conversation) % 2 == 1, 'Conversation must be of odd length'

    if not OPENAI_KEY:
        return 'Not configured'

    messages = [{
        'role': 'system',
        'content': system
    }]

    for i, message in enumerate(conversation):
        messages.append({
            'role': 'user' if i % 2 == 0 else 'assistant',
            'content': message
        })

    async with lock:
        return (await _complete(messages, **kwargs)).strip()
