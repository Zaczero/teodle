import asyncio
import sys
import traceback
from asyncio import Event
from pathlib import Path

from werkzeug.utils import secure_filename

from config import DOWNLOAD_DIR
from vote import Vote


def find_file(url: str) -> tuple[Path, Path | None]:
    prefix = DOWNLOAD_DIR / Path(secure_filename(url))

    for match in prefix.parent.glob(prefix.name + '.*'):
        if match.suffix in {'.mp4'}:
            return prefix, match

    return prefix, None


def cleanup(whitelist_files: set[Path]) -> None:
    for match in DOWNLOAD_DIR.glob('*.*'):
        if match not in whitelist_files:
            print(f'[DL] Cleanup file: {match}')
            match.unlink()


class Downloader:
    processing = 1

    _load_event = Event()
    _vote: Vote

    def load(self, vote: Vote) -> None:
        self._vote = vote
        self._load_event.set()

    async def loop(self) -> None:
        while True:
            await self._load_event.wait()
            self._load_event.clear()
            self.processing = 0

            i_max = len(self._vote.clips)
            clip_paths: set[Path] = set()

            for i, clip in enumerate(self._vote.clips):
                self.processing = i / i_max

                try:
                    clip_prefix, clip_path = find_file(clip.url)

                    if clip_path is None:
                        print(f'[DL] Downloading clip: {clip.url} …')

                        extra_args = []
                        ffmpeg_args = []

                        if 'mute' in clip.modifiers:
                            ffmpeg_args.append('-an')

                        if ffmpeg_args:
                            extra_args += [
                                '--postprocessor-args',
                                f'ffmpeg: {" ".join(ffmpeg_args)}'
                            ]

                        proc = await asyncio.create_subprocess_exec(
                            'yt-dlp',
                            '--verbose',
                            '--prefer-free-formats',
                            '--output',
                            f'{clip_prefix}.%(ext)s',
                            '--prefer-ffmpeg',
                            '--recode-video',
                            'mp4',  # Teo uses Firefox (no matroska)
                            *extra_args,
                            clip.url,
                            stdout=sys.stdout,
                            stderr=sys.stderr
                        )

                        await proc.wait()

                        _, clip_path = find_file(clip.url)

                    if clip_path is not None:
                        clip.use_local_file(clip_path)
                        clip_paths.add(clip_path)

                except Exception:
                    traceback.print_exc()

            cleanup(clip_paths)

            self.processing = 1
