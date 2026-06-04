from __future__ import annotations

import argparse
from pathlib import Path

from utils import copy_or_symlink, make_split_dirs, read_split_csv


VIDEO_SUFFIXES = {".mp4", ".avi", ".mov", ".mkv"}


def collect_raw_clips(raw_dir: Path) -> dict[str, Path]:
    clips: dict[str, Path] = {}
    duplicates: set[str] = set()

    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in VIDEO_SUFFIXES:
            continue
        if path.name.startswith("._"):
            continue
        if path.stem in clips:
            duplicates.add(path.stem)
            continue
        clips[path.stem] = path

    if duplicates:
        preview = ", ".join(sorted(duplicates)[:20])
        raise RuntimeError(f"Duplicate clip filenames found: {preview}")

    return clips


def ensure_video_outputs(output_dir: Path, overwrite: bool) -> None:
    make_split_dirs(output_dir)
    if overwrite:
        return
    existing = []
    for split in ("train", "val", "test"):
        video_dir = output_dir / split / "videos"
        existing.extend(path for path in video_dir.iterdir() if path.is_file())
    if existing:
        raise FileExistsError(f"{output_dir} already contains split video files. Use --overwrite.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split raw GuiFiR clips into train/val/test folders.")
    parser.add_argument("--raw_dir", required=True, type=Path, help="Directory containing raw 10-second clips.")
    parser.add_argument("--split_csv", required=True, type=Path, help="CSV with clip_id,split columns.")
    parser.add_argument("--output_dir", default=Path("guifir_vid"), type=Path)
    parser.add_argument("--use_symlink", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument(
        "--allow_missing",
        action="store_true",
        help="Continue even if raw_dir does not contain every clip_id in split_csv.",
    )
    args = parser.parse_args()

    ensure_video_outputs(args.output_dir, args.overwrite)

    split_map = read_split_csv(args.split_csv)
    raw_clips = collect_raw_clips(args.raw_dir)

    extra = sorted(set(raw_clips) - set(split_map))
    if extra:
        print(f"Warning: {len(extra)} raw clip(s) are not listed in split CSV; first entries: {', '.join(extra[:20])}")

    missing = sorted(set(split_map) - set(raw_clips))
    if missing and not args.allow_missing:
        raise RuntimeError(
            f"Missing {len(missing)} split-listed clip(s); first entries: {', '.join(missing[:30])}. "
            "Use --allow_missing to continue anyway."
        )
    if missing:
        print(f"Warning: missing {len(missing)} split-listed clip(s); first entries: {', '.join(missing[:30])}")

    counts = {split: 0 for split in ("train", "val", "test")}
    missing_counts = {split: 0 for split in ("train", "val", "test")}

    for clip_id, split in split_map.items():
        src = raw_clips.get(clip_id)
        if src is None:
            missing_counts[split] += 1
            continue
        copy_or_symlink(src, args.output_dir / split / "videos" / src.name, args.use_symlink)
        counts[split] += 1

    for split in ("train", "val", "test"):
        print(f"{split}: {counts[split]} videos, {missing_counts[split]} missing")


if __name__ == "__main__":
    main()
