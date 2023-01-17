from config import MAX_STARS


def calculate_stars(vote_idx: int, answer_idx: int) -> int:
    return MAX_STARS - min(abs(vote_idx - answer_idx), MAX_STARS)
