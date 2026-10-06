import io, os, re, uuid
from pathlib import Path
from typing import BinaryIO
from PIL import Image
import fitz
from openpyxl import load_workbook
from pptx import Presentation
from app.core.models import Chunk

SUPPORTED = {".pdf", ".txt", ".csv", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def _chunks(text, size=900, overlap=120):
    text = re.sub(r"\s+", " ", text).strip()
    if not text: return []
    out=[]; start=0
    while start < len(text):
        end=min(len(text), start+size)
        if end < len(text):
            cut=text.rfind(" ", start, end)
            if cut > start+300: end=cut
        out.append(text[start:end])
        if end == len(text): break
        start=max(0,end-overlap)
    return out


def parse_file(data: bytes, filename: str, access_level="public") -> list[Chunk]:
    ext=Path(filename).suffix.lower(); doc_id=str(uuid.uuid4())
    if ext not in SUPPORTED: raise ValueError(f"Unsupported file type: {ext}")
    chunks=[]
    if ext == ".pdf":
        doc=fitz.open(stream=data, filetype="pdf")
        for pno,page in enumerate(doc,1):
            text=page.get_text("text") or ""
            for i,t in enumerate(_chunks(text)):
                chunks.append(Chunk(f"{doc_id}-p{pno}-{i}",doc_id,t,pno,"text",filename,access_level,0.99))
            # Extract images as evidence metadata. OCR is attempted if available.
            for i,img in enumerate(page.get_images(full=True)):
                try:
                    pix=fitz.Pixmap(doc,img[0]); img_bytes=pix.tobytes("png")
                    desc=f"Image extracted from {filename}, page {pno}. Visual evidence is available but OCR/vision interpretation may be incomplete."
                    chunks.append(Chunk(f"{doc_id}-p{pno}-img{i}",doc_id,desc,pno,"image",filename,access_level,0.70,{"image_bytes":len(img_bytes)}))
                except Exception: pass
    elif ext == ".xlsx":
        wb=load_workbook(io.BytesIO(data), data_only=True, read_only=True)
        for ws in wb.worksheets:
            rows=list(ws.iter_rows(values_only=True))
            text="\n".join(" | ".join("" if v is None else str(v) for v in row) for row in rows)
            for i,t in enumerate(_chunks(text)):
                chunks.append(Chunk(f"{doc_id}-{ws.title}-{i}",doc_id,t,None,"table",filename,access_level,0.96,{"sheet":ws.title}))
    elif ext == ".pptx":
        prs=Presentation(io.BytesIO(data))
        for pno,slide in enumerate(prs.slides,1):
            texts=[]
            for shape in slide.shapes:
                if hasattr(shape,"text") and shape.text.strip(): texts.append(shape.text)
            text="\n".join(texts)
            for i,t in enumerate(_chunks(text)):
                chunks.append(Chunk(f"{doc_id}-s{pno}-{i}",doc_id,t,pno,"text",filename,access_level,0.97,{"slide":pno}))
    elif ext == ".csv":
        text=data.decode("utf-8", errors="ignore")
        for i,t in enumerate(_chunks(text)):
            chunks.append(Chunk(f"{doc_id}-{i}",doc_id,t,None,"table",filename,access_level,0.98))
    elif ext == ".txt":
        text=data.decode("utf-8", errors="ignore")
        for i,t in enumerate(_chunks(text)):
            chunks.append(Chunk(f"{doc_id}-{i}",doc_id,t,None,"text",filename,access_level,1.0))
    else:
        # Image artifact: keep metadata; optional OCR if tesseract is installed.
        try:
            im=Image.open(io.BytesIO(data))
            text=""
            try:
                import pytesseract
                text=pytesseract.image_to_string(im).strip()
            except Exception: pass
            if text:
                for i,t in enumerate(_chunks(text)):
                    chunks.append(Chunk(f"{doc_id}-ocr-{i}",doc_id,t,None,"scan",filename,access_level,0.72))
            else:
                chunks.append(Chunk(f"{doc_id}-image",doc_id,f"Image document: {filename}. No OCR text was extracted.",None,"image",filename,access_level,0.55))
        except Exception as e:
            raise ValueError(str(e))
    return chunks
