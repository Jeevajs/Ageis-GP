"""
AEGIS Raw Log Loader
--------------------
Reads raw logs from data/raw, including nested folders and ZIP archives, and
normalizes them into data/processed/clean_logs.csv.

Supported file types: .log, .txt, .csv, .json, .zip

Important:
This loader is demo-safe. It limits:
1. Maximum lines read per file
2. Maximum total rows written to clean_logs.csv

This prevents MemoryError when very large datasets such as HDFS/BGL/Jira ZIPs
contain millions of rows.
"""

from pathlib import Path
import zipfile
import tempfile
import json
import csv
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_FILE = ROOT / "data" / "processed" / "clean_logs.csv"

MAX_LINES_PER_FILE = 5000
MAX_ROWS_TOTAL = 50000


def infer_dataset(path_name: str) -> str:
    name = path_name.lower()

    if "hdfs" in name:
        return "hdfs"
    if "bgl" in name:
        return "bgl"
    if "jira" in name or "publicjira" in name:
        return "jira"
    if "archive" in name:
        return "archive"

    return "unknown"


def infer_severity(line: str) -> str:
    text = line.upper()

    if any(x in text for x in [
        "FATAL",
        "ERROR",
        "FAILED",
        "FAILURE",
        "TIMEOUT",
        "EXCEPTION",
        "OOMKILLED",
        "CRASHLOOPBACKOFF"
    ]):
        return "ERROR"

    if any(x in text for x in [
        "WARN",
        "WARNING",
        "DEGRADED",
        "UNDER REPLICATED",
        "RETRY"
    ]):
        return "WARN"

    return "INFO"


def infer_service(dataset: str, line: str) -> str:
    text = line.lower()

    if dataset == "hdfs":
        if "datanode" in text:
            return "hdfs-datanode"
        if "fsnamesystem" in text or "namenode" in text:
            return "hdfs-namenode"
        return "hdfs-cluster"

    if dataset == "bgl":
        if "kernel" in text:
            return "bgl-kernel"
        if "network" in text:
            return "bgl-network"
        return "bgl-node"

    if "payment" in text:
        return "payment-service"
    if "auth" in text:
        return "auth-service"
    if "cart" in text:
        return "cart-service"
    if "order" in text:
        return "order-service"
    if "inventory" in text:
        return "inventory-service"
    if "oomkilled" in text or "crashloopbackoff" in text:
        return "kubernetes-pod"

    return "unknown-service"


def read_text_file(file_path: Path):
    lines = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, start=1):
            if i > MAX_LINES_PER_FILE:
                break
            if line.strip():
                lines.append(line.strip())

    return lines


def read_csv_file(file_path: Path):
    lines = []

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)

        for i, row in enumerate(reader, start=1):
            if i > MAX_LINES_PER_FILE:
                break

            text = " ".join([str(x) for x in row if x])

            if text.strip():
                lines.append(text.strip())

    return lines


def read_json_file(file_path: Path):
    lines = []

    try:
        data = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))

        if isinstance(data, list):
            for item in data[:MAX_LINES_PER_FILE]:
                lines.append(json.dumps(item))

        elif isinstance(data, dict):
            lines.append(json.dumps(data))

    except Exception:
        pass

    return lines


def collect_lines_from_file(file_path: Path):
    suffix = file_path.suffix.lower()

    if suffix in [".log", ".txt"]:
        return read_text_file(file_path)

    if suffix == ".csv":
        return read_csv_file(file_path)

    if suffix == ".json":
        return read_json_file(file_path)

    return []


def should_skip_path(path: Path) -> bool:
    name = path.name.lower()

    # Jira/archive datasets are often very large and noisy for this demo.
    if "jira" in name or "publicjira" in name:
        return True

    if "archive" in name:
        return True

    return False


def collect_from_zip(zip_path: Path, remaining_capacity: int):
    """
    Extract ZIP temporarily and parse readable files inside it.
    Stops when remaining_capacity is reached.
    """
    rows = []

    if remaining_capacity <= 0:
        return rows

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(tmp_dir)
        except Exception as e:
            print(f"Skipping ZIP {zip_path}: {e}")
            return rows

        for file in tmp_dir.rglob("*"):
            if len(rows) >= remaining_capacity:
                return rows

            if not file.is_file():
                continue

            if should_skip_path(file):
                continue

            dataset = infer_dataset(str(zip_path) + " " + str(file))

            for line_no, line in enumerate(collect_lines_from_file(file), start=1):
                if len(rows) >= remaining_capacity:
                    return rows

                if line.strip():
                    rows.append({
                        "dataset": dataset,
                        "source_file": f"{zip_path.name}/{file.name}",
                        "line_no": line_no,
                        "service": infer_service(dataset, line),
                        "severity": infer_severity(line),
                        "raw_log": line.strip()
                    })

    return rows


def main():
    rows = []

    print(f"Reading raw logs from: {RAW_DIR}")
    print(f"MAX_LINES_PER_FILE = {MAX_LINES_PER_FILE}")
    print(f"MAX_ROWS_TOTAL = {MAX_ROWS_TOTAL}")

    for path in RAW_DIR.rglob("*"):

        if len(rows) >= MAX_ROWS_TOTAL:
            print(f"Reached MAX_ROWS_TOTAL={MAX_ROWS_TOTAL}. Stopping further raw log reading.")
            break

        if not path.is_file():
            continue

        if should_skip_path(path):
            print(f"Skipping large/non-demo file: {path.name}")
            continue

        if path.suffix.lower() == ".zip":
            print(f"Reading ZIP: {path}")
            remaining_capacity = MAX_ROWS_TOTAL - len(rows)
            zip_rows = collect_from_zip(path, remaining_capacity)
            rows.extend(zip_rows)
            print(f"Collected {len(zip_rows)} rows from {path.name}. Total rows: {len(rows)}")

        else:
            print(f"Reading file: {path}")
            dataset = infer_dataset(str(path))

            for line_no, line in enumerate(collect_lines_from_file(path), start=1):

                if len(rows) >= MAX_ROWS_TOTAL:
                    print(f"Reached MAX_ROWS_TOTAL={MAX_ROWS_TOTAL}. Stopping.")
                    break

                if line.strip():
                    rows.append({
                        "dataset": dataset,
                        "source_file": str(path.relative_to(RAW_DIR)),
                        "line_no": line_no,
                        "service": infer_service(dataset, line),
                        "severity": infer_severity(line),
                        "raw_log": line.strip()
                    })

    if not rows:
        raise RuntimeError("No readable raw logs found under data/raw.")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_FILE, index=False)

    print(f"\nCreated: {OUT_FILE}")
    print(f"Total rows: {len(df)}")
    print("\nDataset counts:")
    print(df["dataset"].value_counts())


if __name__ == "__main__":
    main()