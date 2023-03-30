import asyncio
import sys
import traceback
from asyncio import Event
from pathlib import Path

from werkzeug.utils import secure_filename

from clip import Clip
from config import DOWNLOAD_DIR, NO_DOWNLOAD
from vote import Vote


def find_file(clip: Clip, variant: str | None = None) -> tuple[Path, Path | None]:
    assert variant is None or variant.startswith('.'), variant

    prefix = DOWNLOAD_DIR / Path(secure_filename(
        clip.url + (('-' + '-'.join(clip.modifiers)) if clip.modifiers else '')
    ).replace('.', '_'))

    for match in prefix.parent.glob(prefix.name + '.*'):
        # skip if file is empty (possibly corrupted)
        if match.stat().st_size == 0:
            continue

        if variant is not None:
            if len(match.suffixes) == 2 and match.suffixes[0] == variant:
                return prefix, match

        else:
            if len(match.suffixes) == 1:
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
        if NO_DOWNLOAD:
            return

        while True:
            await self._load_event.wait()
            self._load_event.clear()
            self.processing = 0

            i_max = len(self._vote.clips)
            clip_paths: set[Path] = set()

            for i, clip in enumerate(self._vote.clips):
                self.processing = i / i_max

                try:
                    clip_prefix, clip_path = find_file(clip)

                    if clip_path is None:
                        print(f'[DL] Processing clip: {clip.url}')

                        print(f'[DL] Downloading')
                        await (await asyncio.create_subprocess_exec(
                            'yt-dlp',
                            '--verbose',
                            '--force-overwrites',
                            '--output',
                            f'{clip_prefix}.dl.%(ext)s',
                            clip.url,
                            stdout=sys.stdout,
                            stderr=sys.stderr
                        )).wait()

                        _, dl_clip_path = find_file(clip, '.dl')
                        assert dl_clip_path is not None

                        if 'mute' in clip.modifiers:
                            norm_clip_path = None
                        else:
                            print(f'[DL] Normalizing audio')
                            await (await asyncio.create_subprocess_exec(
                                'ffmpeg-normalize',
                                '--verbose',
                                '--force',  # overwrite
                                '--output',
                                f'{clip_prefix}.norm.opus',
                                '--keep-loudness-range-target',
                                '-c:a',
                                'libopus',
                                '-b:a',
                                '64k',
                                dl_clip_path,
                                stdout=sys.stdout,
                                stderr=sys.stderr
                            )).wait()

                            _, norm_clip_path = find_file(clip, '.norm')

                        ffmpeg_i_args = []
                        ffmpeg_o_args = []

                        if norm_clip_path is None:  # clip has no audio / is muted
                            ffmpeg_o_args.extend([
                                '-an',
                            ])
                        else:
                            ffmpeg_i_args.extend([
                                '-i',
                                norm_clip_path,
                            ])
                            ffmpeg_o_args.extend([
                                '-c:a',
                                'copy',

                                '-map',
                                '0:v:0',
                                '-map',
                                '1:a:0',
                            ])

                        print(f'[DL] Re-encoding')
                        await (await asyncio.create_subprocess_exec(
                            'ffmpeg',
                            '-hide_banner',
                            '-y',  # overwrite
                            '-i',
                            dl_clip_path,
                            *ffmpeg_i_args,

                            '-c:v',
                            'libx264',
                            '-preset',
                            'slow',
                            '-crf',
                            '18',
                            '-vf',
                            'deblock,hqdn3d,'
                            "scale='min(1920,iw)':'min(1080,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1,"
                            'unsharp=5:5:0.2',
                            *ffmpeg_o_args,

                            # optimize for streaming
                            '-movflags',
                            '+faststart',
                            f'{clip_prefix}.fin.mp4',  # must be Firefox compatible
                            stdout=sys.stdout,
                            stderr=sys.stderr
                        )).wait()

                        _, fin_clip_path = find_file(clip, '.fin')
                        assert fin_clip_path is not None

                        clip_path = clip_prefix.with_suffix(fin_clip_path.suffix)
                        fin_clip_path.rename(clip_path)

                    if clip_path is not None:
                        clip.use_local_file(clip_path)
                        clip_paths.add(clip_path)

                except Exception:
                    traceback.print_exc()

            cleanup(clip_paths)

            print(f'[DL] Processing finished ✅')

            self.processing = 1
