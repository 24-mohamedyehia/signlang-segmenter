# signlang-segmenter

A Python library for sign language segmentation.

## Optical Flow
![motion curve with segments](./public/image.png)

## Important Naming Note

- Distribution/package name: `signlang-segmenter`
- Python import name: `signlang_segmenter`

Python imports use underscores, not dashes.

## Current Layout

```text
signlang-segmenter/
├── signlang_segmenter/
│   ├── __init__.py
│   ├── video/
│   │   ├── __init__.py
│   │   └── optical_flow/
│   │       ├── __init__.py
│   │       ├── segmenter.py
│   │       ├── motion_analyzer.py
│   │       ├── models.py
│   │       ├── utils.py
│   │       ├── exporter.py
│   │       └── visualization.py
│   └── pose/
│       └── __init__.py
├── examples/
│   └── basic_pipeline.ipynb
├── setup.py
└── README.md
```

## Installation

### Option 1: Install the library to use it

If you only want to use the package in your own project, install it directly from GitHub:

```bash
python -m pip install "git+https://github.com/24-mohamedyehia/signlang-segmenter.git"
```

### Option 2: Install the project for development

If you want to modify the code and contribute, use an isolated environment and editable install:

1. Install Miniconda if needed.
2. Run:

```bash
git clone https://github.com/24-mohamedyehia/signlang-segmenter.git
cd signlang-segmenter
conda create -n signlang-segmenter python=3.11 -y
conda activate signlang-segmenter
python -m pip install --upgrade pip
python -m pip install -e .

```

## Quick Import Check

```python
import signlang_segmenter
import signlang_segmenter.video
import signlang_segmenter.pose
```

## Segmentation API (MVP)

```python
from signlang_segmenter.video import VideoSegmenter, SegmentExporter

segmenter = VideoSegmenter(
	roi_mode="full",
	smooth_window=11,
	min_len_sec=0.30,
	merge_gap_sec=0.45,
	pad_before_frames=10,
	pad_after_frames=12,
)

segments, info = segmenter.segment(VIDEO_PATH)
print(f"Found {len(segments)} segments: {segments}")

exporter = SegmentExporter(out_dir="../output/segments_out")
exporter.export(VIDEO_PATH, segments)
```

## Visualization

```python
from signlang_segmenter.video import plot_motion_segments

plot_motion_segments(segments, info)
```

The plot includes:

- motion raw curve
- motion smooth curve
- adaptive high/low thresholds
- shaded spans for detected segments

The `info` dict returned by `VideoSegmenter.segment` must include:

- `motion_raw`
- `motion_smooth`
- `fps`
- `frame_idx`
- `th_high_arr`
- `th_low_arr`
