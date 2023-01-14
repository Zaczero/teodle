from pathlib import Path

from PIL import Image

from config import RANK_FILE_DEFAULT_EXT


class RankImage:
    path: Path
    width: int = 0
    height: int = 0

    def __init__(self, path: str):  # TODO: check usage
        self.path = Path(f'ranks/{path}')

        if not self.path.suffix:
            self.path = self.path.with_suffix(RANK_FILE_DEFAULT_EXT)

        if self.path.exists():
            with Image.open(self.path) as im:
                self.width = im.width
                self.height = im.height


class Rank:
    raw: str
    text: str
    title: str
    image: RankImage

    def __init__(self, raw: str):
        self.raw = raw

        if '/' in raw:
            parts = raw.split('/')
            assert len(parts) == 2, f'Invalid rank format: {raw}'
            rank = parts[1]
        else:
            rank = raw

        self.text = rank
        self.title = rank.title()
        self.image = RankImage(raw)
