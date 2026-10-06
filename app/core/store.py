import json, sqlite3, threading
from pathlib import Path

DB_PATH = Path("data/eki.db")
DB_PATH.parent.mkdir(exist_ok=True)
_lock = threading.Lock()

def conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _lock, conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS documents(
            id TEXT PRIMARY KEY, filename TEXT, access_level TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS chunks(
            id TEXT PRIMARY KEY, document_id TEXT, page INTEGER, text TEXT, modality TEXT,
            source TEXT, access_level TEXT, extraction_confidence REAL, metadata TEXT
        );
        CREATE TABLE IF NOT EXISTS audit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            user_role TEXT, agent TEXT, action TEXT, input_summary TEXT, output_summary TEXT
        );
        CREATE TABLE IF NOT EXISTS queries(
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            user_role TEXT, query TEXT, answer TEXT, iterations INTEGER
        );
        ''')

def save_document(doc_id, filename, access_level, chunks):
    with _lock, conn() as c:
        c.execute("INSERT OR REPLACE INTO documents(id,filename,access_level) VALUES(?,?,?)", (doc_id,filename,access_level))
        for ch in chunks:
            c.execute("INSERT OR REPLACE INTO chunks VALUES(?,?,?,?,?,?,?,?,?)", (
                ch.chunk_id,ch.document_id,ch.page,ch.text,ch.modality,ch.source,
                ch.access_level,ch.extraction_confidence,json.dumps(ch.metadata)
            ))

def log(user_role, agent, action, input_summary, output_summary):
    with _lock, conn() as c:
        c.execute("INSERT INTO audit_logs(user_role,agent,action,input_summary,output_summary) VALUES(?,?,?,?,?)",
                  (user_role,agent,action,input_summary[:1000],output_summary[:2000]))

def save_query(user_role, query, answer, iterations):
    with _lock, conn() as c:
        c.execute("INSERT INTO queries(user_role,query,answer,iterations) VALUES(?,?,?,?)", (user_role,query,answer,iterations))

def get_documents():
    with conn() as c:
        rows = c.execute('''
            SELECT d.id, d.filename, d.access_level, d.created_at, COUNT(c.id) as chunks
            FROM documents d
            LEFT JOIN chunks c ON d.id = c.document_id
            GROUP BY d.id
            ORDER BY d.created_at DESC
        ''').fetchall()
        return [dict(r) for r in rows]

def stats():
    with conn() as c:
        return {
            "documents": c.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "chunks": c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0],
            "audit_events": c.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0],
            "queries": c.execute("SELECT COUNT(*) FROM queries").fetchone()[0],
        }
