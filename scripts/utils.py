from __future__ import annotations

import csv
import json
import shutil
import tarfile
from pathlib import Path
from typing import Iterable


VALID_SPLITS = {"train", "val", "test"}


def ensure_empty_or_overwrite(path: Path, overwrite: bool) -> None:
    if path.exists() and any(child.is_file() for child in path.rglob("*")) and not overwrite:
        raise FileExistsError(f"{path} contains files. Use --overwrite.")
    path.mkdir(parents=True, exist_ok=True)


def make_split_dirs(output_dir: Path) -> None:
    for split in sorted(VALID_SPLITS):
        for child in ("videos", "frames", "annotations"):
            (output_dir / split / child).mkdir(parents=True, exist_ok=True)


def read_split_csv(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = {"clip_id", "split"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{path} must contain columns: clip_id,split")
        for row in reader:
            clip_id = (row.get("clip_id") or "").strip()
            split = (row.get("split") or "").strip()
            if not clip_id or clip_id.startswith("TODO"):
                continue
            if split not in VALID_SPLITS:
                raise ValueError(f"Invalid split for {clip_id}: {split}")
            mapping[clip_id] = split
    return mapping


def iter_files(root: Path, suffixes: Iterable[str]) -> Iterable[Path]:
    suffix_set = {s.lower() for s in suffixes}
    if root.is_file():
        if root.suffix.lower() in suffix_set and not root.name.startswith("._"):
            yield root
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in suffix_set and not path.name.startswith("._"):
            yield path


def safe_extract_tar(tar_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path) as tar:
        base = output_dir.resolve()
        for member in tar.getmembers():
            target = (output_dir / member.name).resolve()
            if not str(target).startswith(str(base)):
                raise RuntimeError(f"Refusing unsafe tar member: {member.name}")
        tar.extractall(output_dir)


def copy_or_symlink(src: Path, dst: Path, use_symlink: bool) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() or dst.is_symlink():
        return
    if use_symlink:
        dst.symlink_to(src.resolve())
    else:
        shutil.copy2(src, dst)


def jsonl_clip_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            filename = str(item.get("filename", ""))
            clip = filename.split("/", 1)[0]
            if clip:
                ids.add(clip)
    return ids


def validate_required_csv_values(path: Path, required_columns: set[str]) -> list[str]:
    missing: list[str] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not required_columns.issubset(reader.fieldnames or []):
            missing.append(f"{path} must contain columns: {', '.join(sorted(required_columns))}")
            return missing
        for index, row in enumerate(reader, start=2):
            for column in required_columns:
                value = (row.get(column) or "").strip()
                if not value or value.startswith("TODO"):
                    missing.append(f"{path}:{index} missing {column}")
    return missing
