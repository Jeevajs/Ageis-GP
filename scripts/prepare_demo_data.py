"""
Prepare Demo Data for AEGIS.

This script copies the bundled sample HDFS and BGL logs into the raw data
folders. You can also place real public log ZIP files under data/raw before
running the full setup.

Output folders:
- data/raw/hdfs
- data/raw/bgl
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Copy sample logs into data/raw for a reproducible demo."""
    hdfs_dir = ROOT / "data" / "raw" / "hdfs"
    bgl_dir = ROOT / "data" / "raw" / "bgl"
    hdfs_dir.mkdir(parents=True, exist_ok=True)
    bgl_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy(ROOT / "data" / "samples" / "hdfs_sample.log", hdfs_dir / "hdfs_sample.log")
    shutil.copy(ROOT / "data" / "samples" / "bgl_sample.log", bgl_dir / "bgl_sample.log")

    print("Demo raw logs prepared successfully.")


if __name__ == "__main__":
    main()
