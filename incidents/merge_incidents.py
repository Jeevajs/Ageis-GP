from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_FILE = ROOT / "data" / "processed" / "incidents_master.csv"

MAX_MASTER_INCIDENTS = 10000


def main():
    files = [
        ROOT / "data" / "processed" / "incidents_from_raw_logs.csv",
        ROOT / "data" / "processed" / "synthetic_incidents.csv"
    ]

    frames = []

    for file in files:
        if file.exists():
            df = pd.read_csv(file)

            # Keep demo dataset small and balanced
            if "source" in df.columns:
                sample_size = min(len(df), MAX_MASTER_INCIDENTS // 2)
            else:
                sample_size = min(len(df), MAX_MASTER_INCIDENTS)

            df = df.sample(n=sample_size, random_state=42) if len(df) > sample_size else df
            frames.append(df)

    if not frames:
        raise FileNotFoundError("No incident files found.")

    master = pd.concat(frames, ignore_index=True)

    if len(master) > MAX_MASTER_INCIDENTS:
        master = master.sample(n=MAX_MASTER_INCIDENTS, random_state=42)

    master.to_csv(OUT_FILE, index=False)

    print(f"Created {OUT_FILE} with {len(master)} incidents.")


if __name__ == "__main__":
    main()