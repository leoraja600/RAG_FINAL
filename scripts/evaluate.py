"""Small reproducible smoke evaluation. Replace the questions/expected keywords with your dataset."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.main import pipeline, retriever
from app.ingestion.parsers import parse_file
from app.core.store import save_document

# Setup: ingest test documents
retriever.clear()
doc_path = os.path.join(os.path.dirname(__file__), "../data/documents/sample_enterprise.txt")
with open(doc_path, "rb") as f:
    data = f.read()
chunks = parse_file(data, "sample_enterprise.txt", "public")
if chunks:
    save_document(chunks[0].document_id, "sample_enterprise.txt", "public", chunks)
    retriever.add(chunks)

TESTS=[
 {"q":"What was the revenue in 2025?","keywords":["revenue","2025"]},
 {"q":"Which department owns the revenue report?","keywords":["finance","revenue"]},
]

results=[]
for t in TESTS:
    r=pipeline.run(t["q"],"admin")
    text=r.answer.lower()
    hit=sum(k.lower() in text for k in t["keywords"])/len(t["keywords"])
    results.append({"question":t["q"],"keyword_coverage":round(hit,3),"iterations":r.iterations,"citations":len(r.citations),"critic":r.critic})
print(json.dumps(results,indent=2))
