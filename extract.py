from pypdf import PdfReader

def read_pdf(file) -> str:
    reader = PdfReader(file)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()

def read_pdf_pages(file) -> list:
    """Returns [(page_number, text), ...] with pages starting at 1."""
    reader = PdfReader(file)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]