from pathlib import Path

from config import MAX_STARS


def normalize_username(username: str) -> str:
    return username.strip().lower()


def calculate_stars(vote_idx: int, answer_idx: int) -> int:
    return MAX_STARS - min(abs(vote_idx - answer_idx), MAX_STARS)


# prefix components:
space = '    '
branch = '│   '
# pointers:
tee = '├── '
last = '└── '


# https://stackoverflow.com/a/59109706
# https://creativecommons.org/licenses/by-sa/4.0/
def tree(dir_path: Path, prefix: str = ''):
    """A recursive generator, given a directory Path object
    will yield a visual tree structure line by line
    with each line prefixed by the same characters
    """
    contents = list(dir_path.iterdir())
    # contents each get pointers that are ├── with a final └── :
    pointers = [tee] * (len(contents) - 1) + [last]
    for pointer, path in zip(pointers, contents):
        if path.suffix != '.md':
            yield prefix + pointer + path.name
        if path.is_dir():  # extend the prefix and recurse:
            extension = branch if pointer == tee else space
            # i.e. space because last, └── , above so no more |
            yield from tree(path, prefix=prefix+extension)
