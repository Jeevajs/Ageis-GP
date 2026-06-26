import json
from pathlib import Path
import numpy as np, faiss
from sentence_transformers import SentenceTransformer
ROOT=Path(__file__).resolve().parents[1]; VEC=ROOT/"vector_db"; MODEL="sentence-transformers/all-MiniLM-L6-v2"
class AegisRetriever:
    def __init__(self):
        self.model=SentenceTransformer(MODEL)
        self.index=faiss.read_index(str(VEC/"aegis.faiss"))
        self.docs=json.loads((VEC/"documents.json").read_text())
    def search(self, query, top_k=5, source=None):
        q=self.model.encode([query], normalize_embeddings=True); q=np.asarray(q,dtype="float32")
        scores,ids=self.index.search(q, min(top_k*3, len(self.docs))); out=[]
        for score,idx in zip(scores[0],ids[0]):
            doc=self.docs[idx]
            if source and doc["source"]!=source: continue
            out.append({"score":float(score), **doc})
            if len(out)>=top_k: break
        return out
