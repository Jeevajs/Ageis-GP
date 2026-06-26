from pathlib import Path
import pandas as pd, random
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"data/processed/synthetic_incidents.csv"
SCENARIOS=[
("High latency detected","timeout while calling downstream service","Downstream dependency latency spike","Check downstream latency, scale service, restart unhealthy pods."),
("Database connection failure","connection pool exhausted; JDBC timeout","Database connection pool exhaustion","Increase connection pool, kill stale sessions, check slow queries."),
("HTTP 500 error rate increased","HTTP 500 due to NullPointerException after deployment","Application exception after deployment","Rollback deployment and validate config."),
("Pod restart loop","CrashLoopBackOff; OOMKilled; memory limit exceeded","Pod memory exhaustion","Increase memory limit, capture heap dump, rollback if required."),
("Queue backlog increasing","Kafka consumer lag increasing; messages pending","Consumer processing bottleneck","Scale consumers and check downstream API latency.")
]
SERVICES=["auth-service","payment-service","cart-service","order-service","inventory-service"]
def main(n=120):
    rows=[]
    for i in range(n):
        a,l,rc,res=random.choice(SCENARIOS); svc=random.choice(SERVICES)
        rows.append({"incident_id":f"SYN-INC-{i+1:04d}","dataset":"synthetic","service":svc,
        "severity":random.choice(["P1","P2","P3"]),"alert":a,"logs":f"{svc}: {l}",
        "metrics":random.choice(["cpu=92%,memory=78%","db_connections=98%","consumer_lag=18000","error_rate=12%"]),
        "root_cause":rc,"resolution":res,"mttr_minutes_baseline":random.randint(45,90),"source":"synthetic"})
    OUT.parent.mkdir(parents=True, exist_ok=True); pd.DataFrame(rows).to_csv(OUT,index=False)
    print(f"Created {OUT} with {len(rows)} synthetic incidents.")
if __name__=="__main__":
    main()
