import argparse
from pathlib import Path
from logging import getLogger
import subprocess as sp

logger = getLogger(__name__)


def get_timecode(p: Path):
    process = sp.run(
        f"ffprobe -v error -show_entries format^=duration -of default^=noprint_wrappers^=1:nokey^=1 {p.absolute()}",
        shell=True,
        capture_output=True,
        text=True)

    return process.stdout.strip()


def trim_video(p: Path, duration: str, delete=True):
    temp_mp4 = p.with_name(p.name + "_tmp")
    p.rename(temp_mp4)
    sp.run(f"ffmpeg -i {temp_mp4.absolute()} -t {duration} -c copy {p.absolute()}", capture_output=False)
    if delete:
        temp_mp4.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", help="directory of assets", type=Path)

    args = parser.parse_args()

    d: Path = args.directory
    mp4 = list(d.glob("*.mp4"))

    logger.info(f"Found {len(mp4)} mp4 files")

    # Create the proxy folder for lrf files
    proxy_dir = d / "Proxy"
    proxy_dir.mkdir(exist_ok=True)

    lrf_files_root = list(d.glob("*.lrf"))
    lrf_files_root = {v.name: v for v in lrf_files_root}

    mp4_files_proxy = list(proxy_dir.glob("*.mp4"))
    mp4_files_proxy = {v.name: v for v in mp4_files_proxy}

    for mp4_orig in mp4:
        name = mp4_orig.name
        tc_orig = get_timecode(mp4_orig)

        # check if the lrf file is in the same directory
        if name in lrf_files_root:
            # if the file is stored in the same directory as the mp4 files, copy it to the Proxy folder
            tgt = proxy_dir / name
            lrf_files_root[name].rename(proxy_dir / name)
            lrf_files_root.pop(name)
            mp4_files_proxy[name] = tgt

        # slow motion videos does not generate lrf file
        if name not in mp4_files_proxy:
            logger.warning("{} does not have proxy video", name)
            continue

        # all files are copied to the Proxy folder and renamed to .mp4
        proxy_file = mp4_files_proxy[name]

        # check if the timecode (length) of the video matches the proxy
        tc_proxy = get_timecode(proxy_file)

        if tc_proxy != tc_orig:
            logger.warning("{}: timecode does not match. trimming", name)
            trim_video(mp4_orig, tc_proxy)
            logger.info("{}: trimmed from {} to {}", name, tc_orig, tc_proxy)
        else:
            logger.info("{}: proxy timecode matching", name)


if __name__ == '__main__':
    main()
