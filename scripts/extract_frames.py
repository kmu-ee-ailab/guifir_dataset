from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}


def video_inputs(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*") if p.suffix.lower() in VIDEO_SUFFIXES and not p.name.startswith("._"))


def extract_with_ffmpeg(video: Path, output_root: Path, fps: float | None, ext: str) -> None:
    out_dir = output_root / video.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern = out_dir / f"%06d.{ext}"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video),
    ]
    if fps is not None:
        cmd.extend(["-vf", f"fps={fps}"])
    else:
        cmd.extend(["-vsync", "0"])
    cmd.append(str(pattern))
    subprocess.run(cmd, check=True)


def extract_with_opencv(video: Path, output_root: Path, fps: float | None, ext: str) -> None:
    import cv2

    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video}")
    if fps is None:
        stride = 1
    else:
        source_fps = capture.get(cv2.CAP_PROP_FPS) or fps
        stride = max(int(round(source_fps / fps)), 1)
    out_dir = output_root / video.stem
    out_dir.mkdir(parents=True, exist_ok=True)
    frame_index = 0
    saved_index = 1
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % stride == 0:
            cv2.imwrite(str(out_dir / f"{saved_index:06d}.{ext}"), frame)
            saved_index += 1
        frame_index += 1
    capture.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract frames from one video or a directory of videos.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--fps",
        default=None,
        type=float,
        help="Optional target FPS. Omit this to extract frames at each video's native FPS.",
    )
    parser.add_argument("--ext", default="png", choices=["png", "jpg", "jpeg"])
    args = parser.parse_args()

    videos = video_inputs(args.input)
    args.output.mkdir(parents=True, exist_ok=True)
    use_ffmpeg = shutil.which("ffmpeg") is not None
    for video in videos:
        if use_ffmpeg:
            extract_with_ffmpeg(video, args.output, args.fps, args.ext)
        else:
            extract_with_opencv(video, args.output, args.fps, args.ext)
    print(f"Extracted frames from {len(videos)} video(s) into {args.output}")


if __name__ == "__main__":
    main()
