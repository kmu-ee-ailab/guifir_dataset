# GuiFiR: Weakly-Supervised Learning of Hand Pose Estimation for Guitar Finger Reading

[![Paper](https://img.shields.io/badge/IEEE%20Access-2026-00629B)](https://doi.org/10.1109/ACCESS.2026.3713562)
[![DOI](https://img.shields.io/badge/DOI-10.1109%2FACCESS.2026.3713562-blue)](https://doi.org/10.1109/ACCESS.2026.3713562)
[![Code License: MIT](https://img.shields.io/badge/code-MIT-green)](LICENSE)
[![Data: Non-commercial](https://img.shields.io/badge/data-non--commercial-orange)](DATASET_TERMS.md)

Official dataset release for **GuiFiR** (IEEE Access, 2026), a guitar finger
reading dataset for **hand pose estimation**, **fretboard pose estimation**, and
**guitar tablature / fingering recognition** from guitar performance videos.

**Subin An, Seungeun Chung, Minyoung Park, Soochahn Lee\***<br>
[AI Lab](https://ailab.kookmin.ac.kr/), Department of Electrical Engineering, Kookmin University<br>
\*Corresponding author

[Paper (IEEE Xplore)](https://ieeexplore.ieee.org/document/11611142) |
[DOI](https://doi.org/10.1109/ACCESS.2026.3713562) |
[Lab page](https://ailab.kookmin.ac.kr/publications/2026-07-15-guifir-weakly-supervised-learning-of-han/) |
[Citation](#citation)

Guitar finger reading is the task of recognizing which finger presses which
string at which fret from an image. GuiFiR jointly estimates the hand pose and
the guitar fretboard pose, and is trained with weak supervision from sparse
tablature instead of dense per-frame hand keypoint labels.

This repository provides dataset preparation scripts and metadata
for the GuiFiR dataset. Large video files, extracted frames, generated outputs,
and large archives are not stored directly in this GitHub repository.

## Dataset Components

GuiFiR is organized around two dataset components described in the paper:

- GuiFiR-Synth: synthetic composite images with hand and guitar fretboard
  coordinate annotations.
- GuiFiR-Vid: real guitar performance video clips with ground-truth or
  pseudo-ground-truth tablature.

The released data archive contains 10-second clips, metadata, and annotation
files. The preparation scripts organize these files into train, validation, and
test folders and optionally extract image frames.

| Split | Clips | Annotated frames | Keypoint GT (`frame_gt_pose`) |
| ----- | ----: | ---------------: | :---------------------------: |
| train |   900 |           29,051 |              -                |
| val   |    30 |              543 |              yes              |
| test  |   100 |            2,048 |              yes              |

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
    ├── guifir_val_coco_anno_box.jsonl
    └── guifir_test_coco_anno_box.jsonl
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

## Annotation Format

Each line of `guifir_{train,val,test}_coco_anno_box.jsonl` is one annotated frame:

| Field | Description |
| ----- | ----------- |
| `frame_id` | Frame index within the annotation file |
| `filename` | `<clip_id>/<clip_id>_<frame>.png` |
| `frame_width`, `frame_height` | Resolution of the source clip |
| `frame_tab` | Fret per string (6 values). `0` = open string, `20` = string not played |
| `frame_capo` | Capo position (`0` = no capo) |
| `hand_annotation`, `neck_annotation` | Detected hand / fretboard box (`boxes` = `[x1, y1, x2, y2]`), detector phrase and score (`pred_phrases`), box center (`xc`, `yc`), crop `scale`, and `theta` |
| `frame_gt_pose` | val/test only. Fretboard corners `lt`, `lb`, `rt`, `rb` (`[x, y]`) and fingertips `4`, `8`, `12`, `16`, `20` (`[x, y, visibility]`, MediaPipe hand keypoint indices) |

Note: `frame_gt_pose` coordinates are given in 640x360 space. For clips with a
higher resolution (1920x1080 or 3840x2160 in the test split), multiply them by
`frame_width / 640` to match the box coordinates.

## Citation

If you use the GuiFiR dataset or code, please cite:

```bibtex
@article{an2026guifir,
  title     = {GuiFiR: Weakly-Supervised Learning of Hand Pose Estimation for Guitar Finger Reading},
  author    = {An, Subin and Chung, Seungeun and Park, Minyoung and Lee, Soochahn},
  journal   = {IEEE Access},
  volume    = {14},
  pages     = {113417--113427},
  year      = {2026},
  publisher = {IEEE},
  doi       = {10.1109/ACCESS.2026.3713562}
}
```

## Contact

For questions about the dataset, licensing, or commercial use requests, please
contact:

- **Subin An** (primary contact): nesquiq@kookmin.ac.kr
- **Soochahn Lee** (corresponding author)
- Lab homepage: https://ailab.kookmin.ac.kr/

## License and Data Usage

The source code and documentation in this repository are released under the MIT
License. See `LICENSE`.

Downloadable dataset assets, including video clips, annotations, metadata, and
extracted frames, are provided for non-commercial research, education, and
reproducibility. See `DATASET_TERMS.md`.
