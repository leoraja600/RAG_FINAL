import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app.core.store import init_db
from app.ingestion.parsers import parse_file
init_db()
chunks=parse_file(b"Revenue increased 14 percent in 2025. Finance owns the revenue report.","demo.txt","finance")
print("Parsed chunks:",len(chunks),chunks[0].text[:80])
print("OK")
