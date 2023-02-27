class UserVoteState:
    vote: str
    clip_idx: int

    def __init__(self, vote: str, clip_idx: int):
        self.vote = vote
        self.clip_idx = clip_idx
