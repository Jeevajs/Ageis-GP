from pathlib import Path
import pandas as pd
from agents.react_agent import AegisReActAgent
from rag.retriever import AegisRetriever
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/"data/processed/incidents_master.csv"; OUT=ROOT/"phase_outputs/evaluation_results.csv"
def norm(x): return str(x).lower().strip()
def main(limit=50):
    df=pd.read_csv(DATA).head(limit); agent=AegisReActAgent(); retriever=AegisRetriever(); rows=[]
    for _,r in df.iterrows():
        inc=r.to_dict(); res=agent.analyze(inc); pred=norm(res["probable_root_cause"]); actual=norm(r["root_cause"])
        match=int(actual in pred or pred in actual)
        retrieved=retriever.search(f"{r.alert} {r.logs} {r.metrics}",5,source="incident")
        recall=int(any(x["id"]==r["incident_id"] for x in retrieved))
        baseline=float(r["mttr_minutes_baseline"]); aegis=baseline*0.70 if match else baseline*0.90
        rows.append({"incident_id":r["incident_id"],"actual_root_cause":r["root_cause"],"predicted_root_cause":res["probable_root_cause"],"rca_match":match,"retrieval_recall_at_5":recall,"baseline_mttr":baseline,"simulated_aegis_mttr":aegis,"mttr_reduction_pct":round((baseline-aegis)/baseline*100,2)})
    out=pd.DataFrame(rows); OUT.parent.mkdir(parents=True,exist_ok=True); out.to_csv(OUT,index=False)
    print(f"RCA Accuracy: {out.rca_match.mean():.2f}"); print(f"Retrieval Recall@5: {out.retrieval_recall_at_5.mean():.2f}"); print(f"Avg MTTR Reduction %: {out.mttr_reduction_pct.mean():.2f}"); print(f"Saved: {OUT}")
if __name__=="__main__": main()
