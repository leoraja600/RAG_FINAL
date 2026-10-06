# EKI-Agent — runnable same-day MVP

Enterprise-focused Agentic Multimodal RAG prototype based on the supplied second-review architecture.

## Implemented
- PDF/TXT/CSV/XLSX/PPTX/image ingestion
- Multimodal chunk metadata: text/table/image/scan
- Sentence-transformer embeddings
- Qdrant vector retrieval
- BM25 sparse retrieval
- Lightweight knowledge-graph signal using NetworkX entity links
- Hybrid score fusion with extraction-confidence weighting
- Planner → Researcher → Writer → Critic pipeline
- Critic-driven bounded self-correction/re-retrieval
- Role-based document filtering
- Citation/provenance metadata
- SQLite audit/query logs
- FastAPI backend
- Streamlit frontend
- Docker Compose

## Important research-status note
This is a working prototype/MVP, not proof of research performance. The supplied PPT states that experimental validation is ongoing and no measured results are reported yet. Run the evaluation script and report measured results separately.

## 1. Local run
```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
In another terminal:
```bash
streamlit run frontend/streamlit_app.py
```
Open http://localhost:8501

## 2. Optional LLM
Without an API key the system still runs, but the Writer returns retrieved evidence rather than a generated answer. For an OpenAI-compatible endpoint set in `.env`:
```env
LLM_PROVIDER=openai_compatible
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini
```

## 3. Docker
```bash
cp .env.example .env
docker compose up --build
```
Frontend: http://localhost:8501
API docs: http://localhost:8000/docs

## 4. API examples
Upload:
```bash
curl -X POST http://localhost:8000/documents/upload -F "file=@your.pdf" -F "access_level=finance"
```
Query:
```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"query":"What are the major financial risks?","user_role":"finance"}'
```

## Architecture
```text
Files → multimodal parsing → chunk/metadata → dense + BM25 + graph → hybrid retrieval
      → Planner → Researcher → Writer → Critic → (re-retrieve if insufficient) → answer + citations + audit
```
