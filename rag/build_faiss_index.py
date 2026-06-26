import json
from pathlib import Path
import pandas as pd, numpy as np, faiss
from sentence_transformers import SentenceTransformer
ROOT=Path(__file__).resolve().parents[1]
INC=ROOT/"data/processed/incidents_master.csv"; RUN=ROOT/"runbooks"; VEC=ROOT/"vector_db"
MODEL="sentence-transformers/all-MiniLM-L6-v2"
def docs():
    out=[]; df=pd.read_csv(INC)
    for _,r in df.iterrows():
        text=f"Incident ID:{r.incident_id}\nService:{r.service}\nSeverity:{r.severity}\nAlert:{r.alert}\nLogs:{r.logs}\nMetrics:{r.metrics}\nRoot Cause:{r.root_cause}\nResolution:{r.resolution}"
        out.append({"source":"incident","id":r.incident_id,"title":r.alert,"root_cause":r.root_cause,"text":text})
    for f in RUN.glob("*.md"):
        out.append({"source":"runbook","id":f.name,"title":f.stem.replace('_',' ').title(),"root_cause":"","text":f.read_text()})
    return out
def main():
    VEC.mkdir(parents=True, exist_ok=True); d=docs()
    model=SentenceTransformer(MODEL); emb=model.encode([x["text"] for x in d], normalize_embeddings=True, show_progress_bar=True)
    emb=np.asarray(emb,dtype="float32"); index=faiss.IndexFlatIP(emb.shape[1]); index.add(emb)
    faiss.write_index(index, str(VEC/"aegis.faiss")); (VEC/"documents.json").write_text(json.dumps(d,indent=2))
    print(f"Indexed {len(d)} documents.")
if __name__=="__main__":
    main()
