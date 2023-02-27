from vote_state import VoteState


class ClipState(object):
    vote_state: VoteState
    clip_idx: int
    clip_ranks: list[tuple[str, str]]
    clip_answer: str | None
    clip_last: bool

    def __init__(self, vote):
        from vote import Vote
        assert isinstance(vote, Vote)

        self.vote_state = vote.state
        self.clip_idx = vote.clip_idx
        self.clip_ranks = [] if vote.clip_idx == -1 else [
            (r.text, r.image.name)
            for r in vote.clip.ranks
        ]
        self.clip_answer = vote.clip.answer.text if self.vote_state == VoteState.RESULTS else None
        self.clip_last = not vote.has_next_clip
