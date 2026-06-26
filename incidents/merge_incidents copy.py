from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/processed/incidents_master.csv"
def main():
    files=[ROOT/"data/processed/incidents_from_raw_logs.csv", ROOT/"data/processed/synthetic_incidents.csv"]
    frames=[pd.read_csv(f) for f in files if f.exists()]
    if not frames: raise FileNotFoundError("No incident files found.")
    df=pd.concat(frames, ignore_index=True); df.to_csv(OUT,index=False)
    print(f"Created {OUT} with {len(df)} incidents.")
if __name__=="__main__":
    main()
