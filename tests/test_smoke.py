from app.ingestion.parsers import parse_file

def test_txt():
    chunks=parse_file(b"Hello enterprise world", "x.txt", "public")
    assert chunks and chunks[0].modality=="text"
