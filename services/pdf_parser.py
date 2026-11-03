"""PDF and text extraction service for WAT words and SRT situations."""

import io
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional, Tuple
from PIL import Image

# Ensure PyMuPDF 2.0+ does not attempt to load optional ONNX layout models
# which require external ONNX/YAML weights that cause FileNotFoundError
if "pymupdf.layout" not in sys.modules:
    sys.modules["pymupdf.layout"] = None

logger = logging.getLogger(__name__)

# Serial number regex patterns for SRT questions:
# Matches: '1. Text', '1) Text', '(1) Text', '1- Text', '1: Text', '14a. Text', 'Q1. Text', 'Q. 1 Text'
SRT_SERIAL_PATTERNS = [
    re.compile(r"^\s*\(?(\d+[a-zA-Z]?)\)?[\.\:\-\)]\s*(.+)$"),
    re.compile(r"^\s*Q(?:uestion)?[\.\:\s]*(\d+[a-zA-Z]?)\s*[\.\:\-\)]\s*(.+)$", re.IGNORECASE),
    re.compile(r"^\s*(\d+[a-zA-Z]?)\s{2,}(.+)$"),  # Number followed by multi-space
]


def _get_fitz():
    """
    Safely import and return PyMuPDF (fitz) with optional layout analysis disabled.
    """
    if "pymupdf.layout" not in sys.modules:
        sys.modules["pymupdf.layout"] = None
    try:
        import fitz
        return fitz
    except Exception as e:
        logger.error(f"Failed to load PyMuPDF library: {e}")
        raise RuntimeError(f"PyMuPDF engine could not be loaded: {e}") from e


def _read_text_file_safely(path: Path) -> Tuple[str, List[str]]:
    """
    Read text file attempting UTF-8-SIG (handling BOM), standard UTF-8,
    Windows-1252, and Latin-1 fallbacks.
    """
    warnings: List[str] = []
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
    content: Optional[str] = None
    last_err: Optional[Exception] = None

    for enc in encodings:
        try:
            content = path.read_text(encoding=enc)
            if enc not in ("utf-8-sig", "utf-8"):
                warnings.append(f"Decoded using {enc} fallback encoding.")
            break
        except Exception as e:
            last_err = e
            continue

    if content is None:
        raise ValueError(f"Unable to decode text file: {last_err}")

    return content, warnings


@dataclass
class SRTParseResult:
    items: List[Tuple[str, str]]  # [(serial, situation_text)]
    total_pages: int
    scanned_pages_detected: List[int]
    ocr_applied_pages: List[int]
    warnings: List[str]


@dataclass
class WATParseResult:
    words: List[str]
    total_words: int
    source_type: str
    warnings: List[str]


class DocumentParser:
    """Extracts test items from PDF and plain text documents."""

    def __init__(self, ocr_service: Optional[Any] = None) -> None:
        self.ocr_service = ocr_service

    # -------------------------------------------------------------
    # WAT Word Parsing
    # -------------------------------------------------------------
    def parse_wat_file(self, file_path: Path | str) -> WATParseResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".txt":
            return self._parse_wat_txt(path)
        elif suffix == ".pdf":
            return self._parse_wat_pdf(path)
        else:
            raise ValueError(f"Unsupported file format for WAT: {suffix}. Supported: .txt, .pdf")

    def _parse_wat_txt(self, path: Path) -> WATParseResult:
        content, warnings = _read_text_file_safely(path)
        raw_words = self._extract_words_from_text(content)
        if not raw_words:
            warnings.append("No valid words extracted from text file.")

        return WATParseResult(
            words=raw_words,
            total_words=len(raw_words),
            source_type="txt",
            warnings=warnings,
        )

    def _parse_wat_pdf(self, path: Path) -> WATParseResult:
        fitz = _get_fitz()

        warnings = []
        doc = fitz.open(str(path))
        extracted_text_chunks: List[str] = []
        scanned_pages: List[int] = []

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            page_text = page.get_text()
            if len(page_text.strip()) < 5:
                # Potential scanned page
                scanned_pages.append(page_idx + 1)
                if self.ocr_service and self.ocr_service.is_available:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    try:
                        ocr_text = self.ocr_service.extract_text_from_image(img)
                        extracted_text_chunks.append(ocr_text)
                    except Exception as err:
                        warnings.append(f"OCR failed on page {page_idx + 1}: {err}")
                else:
                    warnings.append(
                        f"Page {page_idx + 1} appears to be a scanned image with no extractable text. OCR is not available."
                    )
            else:
                extracted_text_chunks.append(page_text)

        doc.close()
        full_text = "\n".join(extracted_text_chunks)
        words = self._extract_words_from_text(full_text)

        if not words:
            warnings.append("No words extracted from PDF.")

        return WATParseResult(
            words=words,
            total_words=len(words),
            source_type="pdf",
            warnings=warnings,
        )

    def _extract_words_from_text(self, text: str) -> List[str]:
        """
        Extracts words in exact source order.
        Cleans leading/trailing punctuation, quotes, brackets, and line numbering.
        Preserves single words and hyphenated compounds (e.g. 'SELF-RELIANCE').
        """
        words: List[str] = []
        lines = text.splitlines()

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            # If line is numbered like "1. BRAVE" or "1) RESPONSIBLE", remove serial prefix
            num_match = re.match(r"^\s*\(?\d+[a-zA-Z]?\)?[\.\:\-\)]\s*(.+)$", line_str)
            if num_match:
                line_str = num_match.group(1).strip()

            # Split line tokens by comma, tab, or spaces if multiple
            tokens = re.split(r"[,\t]+", line_str)
            for token in tokens:
                token = token.strip()
                if not token:
                    continue
                # Split whitespace words
                sub_tokens = token.split()
                for sub in sub_tokens:
                    # Strip outer punctuation quotes etc but keep hyphen in middle
                    clean = re.sub(r"^[^\w]+|[^\w]+$", "", sub, flags=re.UNICODE)
                    if clean and not clean.isdigit():
                        words.append(clean.upper())

        return words

    # -------------------------------------------------------------
    # SRT Question Parsing
    # -------------------------------------------------------------
    def parse_srt_file(self, file_path: Path | str) -> SRTParseResult:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".txt":
            return self._parse_srt_txt(path)
        elif suffix == ".pdf":
            return self._parse_srt_pdf(path)
        else:
            raise ValueError(f"Unsupported file format for SRT: {suffix}. Supported: .txt, .pdf")

    def _parse_srt_txt(self, path: Path) -> SRTParseResult:
        content, warnings = _read_text_file_safely(path)
        items = self._extract_srt_situations(content)
        if not items:
            warnings.append("No situations found matching standard question numbering formats.")

        return SRTParseResult(
            items=items,
            total_pages=1,
            scanned_pages_detected=[],
            ocr_applied_pages=[],
            warnings=warnings,
        )

    def _parse_srt_pdf(self, path: Path) -> SRTParseResult:
        fitz = _get_fitz()

        warnings: List[str] = []
        scanned_pages: List[int] = []
        ocr_applied_pages: List[int] = []
        text_pages: List[str] = []

        doc = fitz.open(str(path))
        total_pages = len(doc)

        for page_idx in range(total_pages):
            page_num = page_idx + 1
            page = doc[page_idx]

            # Prefer block-by-block text extraction to preserve paragraph boundaries and multi-column flow
            try:
                blocks = page.get_text("blocks")
                # Filter text blocks (block_type == 0)
                text_blocks = [b[4].strip() for b in blocks if len(b) >= 5 and b[4] and b[4].strip()]
                page_text = "\n".join(text_blocks) if text_blocks else page.get_text()
            except Exception:
                page_text = page.get_text()

            if len(page_text.strip()) < 30:
                scanned_pages.append(page_num)
                if self.ocr_service and self.ocr_service.is_available:
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    try:
                        ocr_text = self.ocr_service.extract_text_from_image(img)
                        text_pages.append(ocr_text)
                        ocr_applied_pages.append(page_num)
                    except Exception as err:
                        warnings.append(f"OCR failed for page {page_num}: {err}")
                else:
                    warnings.append(
                        f"Page {page_num} appears scanned. Install or configure Tesseract OCR in Settings to extract scanned questions."
                    )
            else:
                text_pages.append(page_text)

        doc.close()
        full_text = "\n".join(text_pages)
        items = self._extract_srt_situations(full_text)

        if not items:
            warnings.append("No SRT situations could be parsed. Check PDF formatting or use manual import.")
        else:
            # Check serial range 1-60 diagnostics
            int_serials = [int(re.findall(r"\d+", s)[0]) for s, _ in items if re.findall(r"\d+", s)]
            if int_serials:
                min_s, max_s = min(int_serials), max(int_serials)
                expected_set = set(range(min_s, max_s + 1))
                missing = sorted(expected_set - set(int_serials))
                if missing and len(missing) <= 10:
                    warnings.append(f"Missing question serial numbers detected: {', '.join(str(m) for m in missing)}.")

        return SRTParseResult(
            items=items,
            total_pages=total_pages,
            scanned_pages_detected=scanned_pages,
            ocr_applied_pages=ocr_applied_pages,
            warnings=warnings,
        )

    def _extract_srt_situations(self, text: str) -> List[Tuple[str, str]]:
        """
        Extracts situations implementing two strict rules:
        Rule 1: As per serial number (1 to 60) in natural order, handling inline or standalone numbers.
        Rule 2: Sentences terminating with '(...)', merging multi-line prompts and normalizing ending.
        """
        noise_re = re.compile(
            r"^\s*(?:page\s*\d+(?:\s*(?:of|\/)\s*\d+)?|\d+\s*(?:of|\/)\s*\d+|[-–—]\s*\d+\s*[-–—]|\[\s*\d+\s*\]|"
            r"ssb\b|situation\s+reaction\s+test|srt\s+booklet|time\s*allowed|instructions?|confidential|do\s+not\s+turn)\b.*$",
            re.IGNORECASE,
        )

        # Filter out standalone header / footer noise lines
        clean_lines: List[str] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line or noise_re.match(line):
                continue
            clean_lines.append(line)

        joined_text = "\n".join(clean_lines)

        # Serial number marker pattern:
        # Matches numbers 1-999 with delimiters: '.', ')', ':', '-', '—', or followed by newline / multiple spaces / text
        # Or preceding prompt ending with punctuation or newline
        serial_pattern = re.compile(
            r"(?:^|\n|(?<=[\.\…\)])\s+)\s*(?:Q(?:uestion)?[\.\:\s]*|SRT[\.\:\s\-]*)?\(?(\d{1,3}[a-zA-Z]?)\)?(?:[\.\:\)]|\s*[\-–—]|\s*(?=\n)|(?=\s{2,})|\s+)\s*",
            re.IGNORECASE,
        )

        def normalize_prompt_ending(s: str) -> str:
            """Ensure situation sentence terminates cleanly with standard '(...)'."""
            s = s.strip()
            # Normalize internal newlines and whitespace
            s = re.sub(r"\s+", " ", s)
            # If already ends with (...) or variants like ( ... ) or [ ... ]
            if re.search(r"[\(\[]\s*\.{2,}\s*[\)\]]$", s):
                return re.sub(r"[\(\[]\s*\.{2,}\s*[\)\]]$", "(...)", s)
            # If ends with trailing dots: ... or .... or …
            if re.search(r"(?:\.{2,}|\u2026)$", s):
                return re.sub(r"\s*(?:\.{2,}|\u2026)$", " (...)", s)
            # If ends with word without trailing dots (e.g. 'He'), append '(...)'
            return s.rstrip(". ") + " (...)"

        matches = list(serial_pattern.finditer(joined_text))
        raw_items: List[Tuple[str, str]] = []

        if matches:
            for i, m in enumerate(matches):
                start = m.end()
                end = matches[i + 1].start() if i + 1 < len(matches) else len(joined_text)
                serial = m.group(1).strip()
                prompt = joined_text[start:end].strip()
                if prompt:
                    raw_items.append((serial, normalize_prompt_ending(prompt)))
        else:
            # Fallback for documents with no standard question numbers: sequential numbering
            idx = 1
            for line in clean_lines:
                if len(line) >= 8 and not line.lower().startswith(
                    ("situation reaction test", "srt test", "instructions:", "directions:", "sample srt")
                ):
                    raw_items.append((str(idx), normalize_prompt_ending(line)))
                    idx += 1

        # Deduplicate identical consecutive serials while preserving order
        seen_serials = set()
        deduped: List[Tuple[str, str]] = []
        for s, p in raw_items:
            if s not in seen_serials:
                seen_serials.add(s)
                deduped.append((s, p))

        # Natural sort by integer serial number (so 1..60 are ordered strictly)
        def natural_key(item: Tuple[str, str]) -> int:
            digits = re.findall(r"\d+", item[0])
            return int(digits[0]) if digits else 9999

        deduped.sort(key=natural_key)
        return deduped
