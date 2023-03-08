from pathlib import Path

from PIL import Image

from config import RANK_FILE_CONVERT_EXT, RANK_FILE_EXT, RANKS_DIR


class RankImage:
    name: str
    path: Path
    width: int = 0
    height: int = 0

    def __init__(self, name: str):
        if '.' not in name:
            files = list(RANKS_DIR.glob(f'{name}.*'))

            if file := next((f for f in files if f.suffix == RANK_FILE_EXT), None):
                name += file.suffix
            elif file := next((f for f in files if f.suffix in RANK_FILE_CONVERT_EXT), None):
                dest = file.with_suffix(RANK_FILE_EXT)

                with Image.open(file) as im:
                    # method: 0 is fastest, 6 is slowest
                    im.save(dest, RANK_FILE_EXT[1:], quality=95, method=6)

                name += dest.suffix
                print(f'[RANK] Optimized {name} file')

        self.name = name
        self.path = RANKS_DIR / name

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
