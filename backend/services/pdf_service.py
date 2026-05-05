"""
NyayaSetu — PDF Service
Extracts text from court judgment PDFs using PyMuPDF.
Returns per-page content for source highlighting.
"""
import fitz  # PyMuPDF
import re
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class PageContent:
    page_num: int   # 1-indexed
    text: str
    word_count: int


@dataclass
class PDFExtractionResult:
    pages: list[PageContent] = field(default_factory=list)
    full_text: str = ""
    page_count: int = 0
    is_scanned: bool = False
    metadata: dict = field(default_factory=dict)
    error: str = ""


def extract_pdf(pdf_path: str | Path) -> PDFExtractionResult:
    """
    Extract text from a PDF file, page by page.
    Returns structured content with page references for citation.
    """
    result = PDFExtractionResult()
    try:
        doc = fitz.open(str(pdf_path))
        result.page_count = len(doc)
        result.metadata = {
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
        }

        all_text_parts = []
        total_words = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text", sort=True)  # sorted for reading order
            text = _clean_text(text)
            words = len(text.split())
            total_words += words

            pc = PageContent(
                page_num=page_num + 1,
                text=text,
                word_count=words,
            )
            result.pages.append(pc)
            all_text_parts.append(f"[PAGE {page_num + 1}]\n{text}")

        result.full_text = "\n\n".join(all_text_parts)

        # Heuristic: if avg words per page is < 30, likely scanned
        avg_words = total_words / max(result.page_count, 1)
        result.is_scanned = avg_words < 30

        doc.close()
    except Exception as e:
        result.error = str(e)

    return result


def _clean_text(text: str) -> str:
    """Normalize whitespace and remove junk characters."""
    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove null bytes and other control chars (except newline/tab)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", text)
    return text.strip()


def get_relevant_pages(full_text: str, keyword: str, context_chars: int = 300) -> list[dict]:
    """
    Find pages containing a keyword and return snippets with page references.
    Used for UI source highlighting.
    """
    results = []
    pages = full_text.split("[PAGE ")
    for section in pages[1:]:  # skip empty first split
        try:
            page_num_end = section.index("]")
            page_num = int(section[:page_num_end])
            content = section[page_num_end + 1:]
        except (ValueError, IndexError):
            continue

        lower_content = content.lower()
        lower_keyword = keyword.lower()
        idx = lower_content.find(lower_keyword)
        if idx != -1:
            start = max(0, idx - context_chars // 2)
            end = min(len(content), idx + len(keyword) + context_chars // 2)
            snippet = content[start:end].strip()
            results.append({
                "page": page_num,
                "snippet": snippet,
                "keyword": keyword,
            })
    return results
