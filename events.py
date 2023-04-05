from asyncio import Event
from collections import defaultdict
from functools import cache
from typing import Any, NewType

EventType = NewType('EventType', str)

TYPE_TOTAL_VOTES = EventType('TOTAL_VOTES')


@cache
def TYPE_CLIP_STATE(channel: str) -> EventType:
    return EventType(f'CLIP_STATE_{channel}')


@cache
def TYPE_USER_VOTE_STATE(channel: str, username: str) -> EventType:
    return EventType(f'USER_VOTE_STATE_{channel}_{username}')


@cache
def TYPE_USER_SCORE(channel: str, username: str) -> EventType:
    return EventType(f'USER_SCORE_{channel}_{username}')


_subscriptions: dict[EventType, set['Subscription']] = defaultdict(set)
_subscriptions_enabled: bool = True
_publish_cache: dict[EventType, Any] = {}


def toggle_subscriptions(*, enabled: bool) -> None:
    global _subscriptions_enabled
    _subscriptions_enabled = enabled
    print(f'[EVENTS] Subscriptions {"enabled" if enabled else "disabled"}')


def publish(type: EventType, args: Any = None) -> None:
    if not _subscriptions_enabled:
        return

    _publish_cache[type] = args

    for subscription in _subscriptions[type]:
        subscription.notify(args)


def empty_user_state() -> None:
    target = [e for e in _publish_cache.keys() if e.startswith('USER_')]

    for event_type in target:
        publish(event_type, None)

    print(f'[EVENTS] Cleared {len(target)} user states')


class Subscription:
    type: EventType
    _event: Event
    _args: Any

    def __init__(self, type: EventType) -> None:
        self.type = type
        self._event = Event()

        if self.type in _publish_cache:
            self.notify(_publish_cache[self.type])

    def __enter__(self) -> 'Subscription':
        _subscriptions[self.type].add(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        _subscriptions[self.type].remove(self)

    def notify(self, args: Any) -> None:
        self._args = args
        self._event.set()

    async def wait(self) -> Any:
        await self._event.wait()
        self._event.clear()
        return self._args
