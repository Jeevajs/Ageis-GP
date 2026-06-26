"""
AEGIS Raw Log Loader - Memory Safe Version
Writes directly to CSV without storing all rows in memory.
"""

from pathlib import Path
import zipfile
import tempfile
import json
import csv

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_FILE = ROOT / "data" / "processed" / "clean_logs.csv"

MAX_LINES_PER_FILE = 3000
MAX_ROWS_TOTAL = 50000

HEADERS = ["dataset", "source_file", "line_no", "service", "severity", "raw_log"]


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
    if any(x in text for x in ["FATAL", "ERROR", "FAILED", "FAILURE", "TIMEOUT", "EXCEPTION", "OOMKILLED", "CRASHLOOPBACKOFF"]):
        return "ERROR"
    if any(x in text for x in ["WARN", "WARNING", "DEGRADED", "UNDER REPLICATED", "RETRY"]):
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


def should_skip_path(path: Path) -> bool:
    name = path.name.lower()
    return "jira" in name or "publicjira" in name or "archive" in name


def iter_text_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f, start=1):
            if i > MAX_LINES_PER_FILE:
                break
            line = line.strip()
            if line:
                yield i, line


def iter_csv_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader, start=1):
            if i > MAX_LINES_PER_FILE:
                break
            text = " ".join(str(x) for x in row if x).strip()
            if text:
                yield i, text


def iter_json_file(file_path: Path):
    try:
        data = json.loads(file_path.read_text(encoding="utf-8", errors="ignore"))

        if isinstance(data, list):
            for i, item in enumerate(data[:MAX_LINES_PER_FILE], start=1):
                yield i, json.dumps(item)

        elif isinstance(data, dict):
            yield 1, json.dumps(data)

    except Exception:
        return


def iter_lines_from_file(file_path: Path):
    suffix = file_path.suffix.lower()

    if suffix in [".log", ".txt"]:
        yield from iter_text_file(file_path)
    elif suffix == ".csv":
        yield from iter_csv_file(file_path)
    elif suffix == ".json":
        yield from iter_json_file(file_path)


def write_row(writer, dataset, source_file, line_no, line):
    writer.writerow({
        "dataset": dataset,
        "source_file": source_file,
        "line_no": line_no,
        "service": infer_service(dataset, line),
        "severity": infer_severity(line),
        "raw_log": line.strip()
    })


def process_regular_file(path: Path, writer, total_rows: int) -> int:
    dataset = infer_dataset(str(path))

    for line_no, line in iter_lines_from_file(path):
        if total_rows >= MAX_ROWS_TOTAL:
            return total_rows

        write_row(
            writer=writer,
            dataset=dataset,
            source_file=str(path.relative_to(RAW_DIR)),
            line_no=line_no,
            line=line
        )
        total_rows += 1

    return total_rows


def process_zip(zip_path: Path, writer, total_rows: int) -> int:
    print(f"Reading ZIP: {zip_path}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)

        try:
            with zipfile.ZipFile(zip_path, "r") as z:
                z.extractall(tmp_dir)
        except Exception as e:
            print(f"Skipping ZIP {zip_path}: {e}")
            return total_rows

        for file in tmp_dir.rglob("*"):
            if total_rows >= MAX_ROWS_TOTAL:
                return total_rows

            if not file.is_file():
                continue

            if should_skip_path(file):
                continue

            if file.suffix.lower() not in [".log", ".txt", ".csv", ".json"]:
                continue

            dataset = infer_dataset(str(zip_path) + " " + str(file))

            for line_no, line in iter_lines_from_file(file):
                if total_rows >= MAX_ROWS_TOTAL:
                    return total_rows

                write_row(
                    writer=writer,
                    dataset=dataset,
                    source_file=f"{zip_path.name}/{file.name}",
                    line_no=line_no,
                    line=line
                )
                total_rows += 1

    return total_rows


def main():
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    dataset_counts = {}

    print(f"Reading raw logs from: {RAW_DIR}")
    print(f"MAX_LINES_PER_FILE = {MAX_LINES_PER_FILE}")
    print(f"MAX_ROWS_TOTAL = {MAX_ROWS_TOTAL}")

    with open(OUT_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()

        for path in RAW_DIR.rglob("*"):
            if total_rows >= MAX_ROWS_TOTAL:
                print(f"Reached MAX_ROWS_TOTAL={MAX_ROWS_TOTAL}. Stopping.")
                break

            if not path.is_file():
                continue

            if should_skip_path(path):
                print(f"Skipping large/non-demo file: {path.name}")
                continue

            before = total_rows

            if path.suffix.lower() == ".zip":
                total_rows = process_zip(path, writer, total_rows)
            else:
                total_rows = process_regular_file(path, writer, total_rows)

            added = total_rows - before
            if added > 0:
                dataset = infer_dataset(str(path))
                dataset_counts[dataset] = dataset_counts.get(dataset, 0) + added
                print(f"Added {added} rows from {path.name}. Total rows: {total_rows}")

    if total_rows == 0:
        raise RuntimeError("No readable raw logs found under data/raw.")

    print(f"\nCreated: {OUT_FILE}")
    print(f"Total rows: {total_rows}")
    print("Dataset counts:")
    for k, v in dataset_counts.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()