from rag.retriever import AegisRetriever
_R=None
def retriever():
    global _R
    if _R is None: _R=AegisRetriever()
    return _R
def query_logs(log_text):
    t=log_text.lower(); findings=[]
    patterns={"timeout":"Timeout pattern found.","under replicated":"HDFS replication issue found.","connection reset":"Network reset pattern found.","machine check":"Hardware machine check found.","not responding":"Node not responding pattern found.","connection pool":"Database pool exhaustion found.","oomkilled":"Memory/OOM issue found.","consumer lag":"Kafka consumer lag found.","http 500":"Application HTTP 500 failure found."}
    for k,v in patterns.items():
        if k in t: findings.append(v)
    return findings or ["No strong known log pattern detected."]
def search_incidents(query, top_k=5): return retriever().search(query, top_k, source="incident")
def search_runbooks(query, top_k=5): return retriever().search(query, top_k, source="runbook")
