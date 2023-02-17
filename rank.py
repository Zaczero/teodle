from pathlib import Path

from PIL import Image

from config import RANK_FILE_DEFAULT_EXT, RANKS_DIR


class RankImage:
    path: Path
    width: int = 0
    height: int = 0

    def __init__(self, path: str):
        self.path = Path(f'{RANKS_DIR}/{path}')

        if not self.path.suffix:
            self.path = self.path.with_suffix(RANK_FILE_DEFAULT_EXT)

        if self.path.exists():
            with Image.open(self.path) as im:
                self.width = 80
                self.height = int(im.height / (im.width / self.width))


class Rank:
    raw: str
    text: str
    title: str
    image: RankImage

    def __init__(self, raw: str):
        self.raw = raw
        self.image = RankImage(raw)

        if '/' in raw:
            parts = raw.split('/')
            assert len(parts) == 2, f'Invalid rank format: {raw}'
            game, rank = parts
            assert self.image.path.exists(), f'Rank image not found: {self.image.path}'
        else:
            rank = raw

        self.text = rank
        self.title = rank.title()
