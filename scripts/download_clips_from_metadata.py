from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
from pathlib import Path


def read_yt_csv(path: Path) -> dict[str, str]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"source_id", "youtube_url"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path} must contain columns: source_id,youtube_url")
        return {
            row["source_id"].strip(): row["youtube_url"].strip()
            for row in reader
            if row.get("source_id") and row.get("youtube_url")
        }


def read_start_end_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"clip_id", "source_id", "start_time", "end_time"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path} must contain columns: clip_id,source_id,start_time,end_time")
        return [
            {
                "clip_id": row["clip_id"].strip(),
                "source_id": row["source_id"].strip(),
                "start_time": row["start_time"].strip(),
                "end_time": row["end_time"].strip(),
            }
            for row in reader
            if row.get("clip_id") and row.get("source_id")
        ]


def require_command(command: str) -> None:
    if shutil.which(command) is None:
        raise RuntimeError(f"{command} is required but was not found in PATH.")


def downloaded_source_path(source_id: str, download_dir: Path) -> Path | None:
    matches = sorted(download_dir.glob(f"{source_id}.*"))
    for path in matches:
        if path.is_file() and not path.name.endswith(".part"):
            return path
    return None


def download_source(source_id: str, url: str, download_dir: Path, overwrite: bool) -> Path:
    existing = downloaded_source_path(source_id, download_dir)
    if existing is not None and not overwrite:
        return existing

    download_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(download_dir / f"{source_id}.%(ext)s")
    subprocess.run(
        [
            "yt-dlp",
            "--no-playlist",
            "-f",
            "bv*+ba/b",
            "-o",
            output_template,
            url,
        ],
        check=True,
    )

    downloaded = downloaded_source_path(source_id, download_dir)
    if downloaded is None:
        raise RuntimeError(f"yt-dlp completed but no file was found for source_id={source_id}")
    return downloaded


def cut_clip(source_video: Path, output_path: Path, start_time: str, end_time: str, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if overwrite else "-n",
        "-ss",
        start_time,
        "-to",
        end_time,
        "-i",
        str(source_video),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download source videos and cut GuiFiR clips from metadata.")
    parser.add_argument("--yt_csv", required=True, type=Path)
    parser.add_argument("--start_end_csv", required=True, type=Path)
    parser.add_argument("--output_dir", default=Path("GuiFiR/raw_clips"), type=Path)
    parser.add_argument("--source_dir", default=Path("GuiFiR/source_videos"), type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--keep_source_videos", action="store_true")
    args = parser.parse_args()

    require_command("yt-dlp")
    require_command("ffmpeg")

    yt_urls = read_yt_csv(args.yt_csv)
    clips = read_start_end_csv(args.start_end_csv)

    source_cache: dict[str, Path] = {}
    for index, clip in enumerate(clips, start=1):
        source_id = clip["source_id"]
        if source_id not in yt_urls:
            raise RuntimeError(f"No youtube_url found for source_id={source_id}")
        if source_id not in source_cache:
            print(f"Downloading source {source_id}")
            source_cache[source_id] = download_source(source_id, yt_urls[source_id], args.source_dir, args.overwrite)

        output_path = args.output_dir / f"{clip['clip_id']}.mp4"
        print(f"[{index}/{len(clips)}] Cutting {output_path.name}")
        cut_clip(source_cache[source_id], output_path, clip["start_time"], clip["end_time"], args.overwrite)

    if not args.keep_source_videos and args.source_dir.exists():
        shutil.rmtree(args.source_dir)

    print(f"Created {len(list(args.output_dir.glob('*.mp4')))} clip(s) in {args.output_dir}")


if __name__ == "__main__":
    main()
