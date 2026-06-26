from pathlib import Path
import pandas as pd, random
ROOT = Path(__file__).resolve().parents[1]
IN_FILE = ROOT/"data/processed/clean_logs.csv"
OUT_FILE = ROOT/"data/processed/incidents_from_raw_logs.csv"

def alert(log):
    t=log.lower()
    if "under replicated" in t or "replicate" in t: return "HDFS block replication issue"
    if "timeout" in t: return "Timeout detected"
    if "connection reset" in t: return "Network connection reset"
    if "machine check" in t: return "Hardware machine check error"
    if "not responding" in t: return "Node not responding"
    if "degraded" in t: return "Degraded system performance"
    return "Operational event"

def root_cause(log):
    t=log.lower()
    if "under replicated" in t: return "Insufficient HDFS block replicas"
    if "timeout" in t: return "Network or downstream timeout"
    if "connection reset" in t: return "Transient network failure"
    if "machine check" in t: return "Hardware fault detected"
    if "not responding" in t: return "Compute node failure"
    if "degraded" in t: return "Network or hardware performance degradation"
    return "No strong failure pattern detected"

def resolution(rc):
    t=rc.lower()
    if "hdfs" in t or "replicas" in t: return "Check DataNode health, trigger block re-replication, validate NameNode block reports."
    if "network" in t or "timeout" in t: return "Check latency, retry failed operation, validate downstream dependency health."
    if "hardware" in t or "node" in t: return "Drain affected node, inspect hardware logs, restart or replace node if needed."
    return "Monitor logs, correlate with related alerts, and escalate if repeated."

def main():
    logs=pd.read_csv(IN_FILE)
    candidates=logs[logs["severity"].isin(["ERROR","WARN"])].copy()
    rows=[]
    for _,r in candidates.iterrows():
        rc=root_cause(r["raw_log"])
        rows.append({"incident_id":f"RAW-INC-{len(rows)+1:04d}","dataset":r["dataset"],
                     "service":r["service"],"severity":"P1" if r["severity"]=="ERROR" else "P2",
                     "alert":alert(r["raw_log"]),"logs":r["raw_log"],
                     "metrics":random.choice(["cpu=85%, memory=70%","latency_p95=2200ms","node_health=degraded","replication_factor=1,target=3"]),
                     "root_cause":rc,"resolution":resolution(rc),
                     "mttr_minutes_baseline":random.randint(45,90),"source":"public_raw_logs"})
    df=pd.DataFrame(rows); OUT_FILE.parent.mkdir(parents=True, exist_ok=True); df.to_csv(OUT_FILE,index=False)
    print(f"Created {OUT_FILE} with {len(df)} incidents.")
if __name__=="__main__":
    main()
