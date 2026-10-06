import os, uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.core.store import init_db, save_document, stats, get_documents
from app.ingestion.parsers import parse_file
from app.retrieval.engine import RetrievalEngine
from app.agents.pipeline import AgentPipeline

init_db()
retriever=RetrievalEngine()
pipeline=AgentPipeline(retriever)
app=FastAPI(title="EKI-Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query:str
    user_role:str="admin"

@app.get("/")
def root(): return {"name":"EKI-Agent","status":"running","stats":stats()}

@app.get("/health")
def health(): return {"status":"ok","stats":stats()}

@app.get("/documents")
def list_documents(): return get_documents()

@app.post("/documents/upload")
async def upload(file:UploadFile=File(...),access_level:str=Form("public")):
    data=await file.read()
    try: chunks=parse_file(data,file.filename,access_level)
    except Exception as e: raise HTTPException(400,str(e))
    if not chunks: raise HTTPException(400,"No extractable content found")
    doc_id=chunks[0].document_id
    save_document(doc_id,file.filename,access_level,chunks)
    retriever.add(chunks)
    return {"document_id":doc_id,"filename":file.filename,"chunks":len(chunks),"access_level":access_level}

@app.post("/query")
def query(req:QueryRequest):
    result=pipeline.run(req.query,req.user_role)
    return {"answer":result.answer,"citations":result.citations,"iterations":result.iterations,"critic":result.critic,"traces":[t.__dict__ for t in result.traces]}
