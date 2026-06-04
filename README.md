# GuiFiR Dataset

This repository provides dataset preparation scripts and metadata
for the GuiFiR dataset, a dataset for guitar finger reading and hand pose
estimation from guitar performance videos.

Large video files, extracted frames, generated outputs, and large archives are
not stored directly in this GitHub repository.

## Dataset Components

GuiFiR is organized around two dataset components described in the paper:

- GuiFiR-Synth: synthetic composite images with hand and guitar fretboard
  coordinate annotations.
- GuiFiR-Vid: real guitar performance video clips with ground-truth or
  pseudo-ground-truth tablature.

The released data archive contains 10-second clips, metadata, and annotation
files. The preparation scripts organize these files into train, validation, and
test folders and optionally extract image frames.

Expected inputs:

```text
GuiFiR.tar
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

System tools:

- `ffmpeg` is recommended for frame extraction and clip cutting.
- `yt-dlp` is required when downloading clips from source-video metadata.

## Quick Start

`GuiFiR.tar` should unpack into:

```text
GuiFiR/
├── raw_clips/
│   ├── AllOfMe_1.mp4
│   ├── AllOfMe_2.mp4
│   └── ...
├── metadata/
│   ├── split.csv
│   ├── yt_link.csv
│   └── start_end.csv
└── annotations/
    ├── guifir_train_coco_anno_box.jsonl
    ├── guifir_val_coco_anno_box_v5.jsonl
    └── guifir_test_coco_anno_box_final_100.jsonl
```

Each video filename stem must match a `clip_id` in `metadata/split.csv`.

### 1. Download with gdown

```bash
mkdir -p tmp
```

```bash
gdown --id 1Ri42XQnpwWQzjNLOPgZCR2XCx9YGrqxc -O tmp/GuiFiR.tar
```

### 2. Untar

```bash
tar -xf tmp/GuiFiR.tar -C tmp
```

### 3. Move Metadata

```bash
mkdir -p guifir_vid/metadata
```

```bash
cp -r tmp/GuiFiR/metadata/. guifir_vid/metadata/
```

### 4. Move Annotations

```bash
python scripts/move_annotations.py \
  --annotation_dir tmp/GuiFiR/annotations \
  --split_csv guifir_vid/metadata/split.csv \
  --output_dir guifir_vid
```

### 5. Download Clips from Metadata Optional

Skip this step if `tmp/GuiFiR/raw_clips/` already contains the released clips.

```bash
python scripts/download_clips_from_metadata.py \
  --yt_csv guifir_vid/metadata/yt_link.csv \
  --start_end_csv guifir_vid/metadata/start_end.csv \
  --output_dir tmp/GuiFiR/raw_clips \
  --source_dir tmp/GuiFiR/source_videos
```

### 6. Move Clips by Split

```bash
python scripts/split_clips.py \
  --raw_dir tmp/GuiFiR/raw_clips \
  --split_csv guifir_vid/metadata/split.csv \
  --output_dir guifir_vid
```

### 7. Remove Temporary Files

```bash
rm -rf tmp
```

### 8. Extract Frames

```bash
python scripts/extract_frames.py \
  --input guifir_vid/train/videos \
  --output guifir_vid/train/frames \
  --ext png
```

```bash
python scripts/extract_frames.py \
  --input guifir_vid/val/videos \
  --output guifir_vid/val/frames \
  --ext png
```

```bash
python scripts/extract_frames.py \
  --input guifir_vid/test/videos \
  --output guifir_vid/test/frames \
  --ext png
```

Frame extraction uses `scripts/extract_frames.py`. If `ffmpeg` is installed,
the script uses `ffmpeg`; otherwise it falls back to OpenCV. By default, frames
are extracted at each video's native FPS. Pass `--fps` only when you explicitly
want to resample videos to a target FPS.

Use `--help` on each script to see all supported arguments.

## Expected Output Structure

```text
guifir_vid/
├── train/
│   ├── videos/
│   ├── frames/
│   └── annotations/
├── val/
│   ├── videos/
│   ├── frames/
│   └── annotations/
└── test/
    ├── videos/
    ├── frames/
    └── annotations/
```

## Citation

If you use GuiFiR, please cite the GuiFiR paper. The official BibTeX entry will
be updated after publication.

## License and Data Usage

The source code and documentation in this repository are released under the MIT
License. See `LICENSE`.

Downloadable dataset assets, including video clips, annotations, metadata, and
extracted frames, are provided for non-commercial research, education, and
reproducibility. See `DATASET_TERMS.md`.
