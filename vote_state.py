from enum import Enum


class VoteState(Enum):
    IDLE = 0
    VOTING = 1
    RESULTS = 2
