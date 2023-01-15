from rank import Rank


class Clip:
    embed: bool
    url: str
    credits: str
    ranks: list[Rank]
    answer_idx: int = -1

    def __init__(self, text: str):
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        assert len(lines) >= 3, 'Clip must contain at least 3 lines: url, credits, rank'

        self.embed = lines[0].startswith('embed')

        if self.embed:
            self.url = lines[0][len('embed'):].strip()
        else:
            self.url = lines[0]

        assert self.url.startswith('http'), f'Invalid URL: {self.url}'

        self.credits = lines[1]
        self.ranks = []

        for i, line in enumerate(lines[2:]):
            line = line.lower().strip().replace(' ', '_')

            rank = Rank(line.lstrip('*_').lstrip())
            self.ranks.append(rank)

            if line.startswith('*'):
                assert self.answer_idx < 0, f'Found multiple answers for {self.url}'
                self.answer_idx = i

        assert self.ranks, f'No ranks were provided for {self.url}'
        assert self.answer_idx > -1, f'No answer was provided for {self.url}'
        assert len(set(self.ranks)) == len(self.ranks), f'Duplicate ranks for {self.url}'

    @property
    def answer(self) -> Rank:
        return self.ranks[self.answer_idx]