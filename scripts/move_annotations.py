from __future__ import annotations

import argparse
from pathlib import Path

from utils import copy_or_symlink, make_split_dirs, read_split_csv


ANNOTATION_SUFFIXES = {".jsonl", ".json", ".csv"}


def annotation_files(annotation_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in annotation_dir.rglob("*")
        if path.is_file()
        and path.suffix.lower() in ANNOTATION_SUFFIXES
        and not path.name.startswith("._")
    )


def infer_split(path: Path, split_map: dict[str, str]) -> str | None:
    name = path.name.lower()
    if "train" in name:
        return "train"
    if "val" in name:
        return "val"
    if "test" in name:
        return "test"
    return split_map.get(path.stem)


def main() -> None:
    parser = argparse.ArgumentParser(description="Move GuiFiR annotation files into split folders.")
    parser.add_argument("--annotation_dir", required=True, type=Path)
    parser.add_argument("--split_csv", required=True, type=Path)
    parser.add_argument("--output_dir", default=Path("guifir_vid"), type=Path)
    parser.add_argument("--use_symlink", action="store_true")
    args = parser.parse_args()

    make_split_dirs(args.output_dir)
    split_map = read_split_csv(args.split_csv)
    counts = {split: 0 for split in ("train", "val", "test")}
    skipped: list[str] = []

    for annotation in annotation_files(args.annotation_dir):
        split = infer_split(annotation, split_map)
        if split is None:
            skipped.append(annotation.name)
            continue
        copy_or_symlink(annotation, args.output_dir / split / "annotations" / annotation.name, args.use_symlink)
        counts[split] += 1

    for split in ("train", "val", "test"):
        print(f"{split}: {counts[split]} annotation file(s)")
    if skipped:
        print(f"Warning: skipped {len(skipped)} annotation file(s); first entries: {', '.join(skipped[:20])}")


if __name__ == "__main__":
    main()
