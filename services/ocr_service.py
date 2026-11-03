"""Tesseract OCR service with auto-detection, manual path override, and safe fallback."""

import logging
import os
import shutil
from pathlib import Path
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

COMMON_WINDOWS_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
]


class OCRService:
    """Manages optional Tesseract OCR integration."""

    def __init__(self, custom_tesseract_path: Optional[str] = None) -> None:
        self._custom_path = custom_tesseract_path
        self._detected_path: Optional[str] = None
        self._detect_tesseract()

    def set_custom_path(self, path: Optional[str]) -> None:
        self._custom_path = path
        self._detect_tesseract()

    def _detect_tesseract(self) -> None:
        # 1. Custom path if provided and exists
        if self._custom_path and os.path.isfile(self._custom_path):
            self._detected_path = self._custom_path
            return

        # 2. Check system PATH
        which_path = shutil.which("tesseract")
        if which_path:
            self._detected_path = which_path
            return

        # 3. Check common Windows install directories
        for cand in COMMON_WINDOWS_TESSERACT_PATHS:
            if os.path.isfile(cand):
                self._detected_path = cand
                return

        self._detected_path = None

    @property
    def is_available(self) -> bool:
        """Return True if Tesseract executable is found and operational."""
        return self._detected_path is not None and os.path.isfile(self._detected_path)

    @property
    def executable_path(self) -> Optional[str]:
        return self._detected_path

    def get_status_message(self) -> str:
        if self.is_available:
            return f"Tesseract OCR is available ({self._detected_path})"
        return (
            "Tesseract OCR is not installed or not found. Scanned PDF text extraction will be disabled. "
            "Install Tesseract for Windows from UB-Mannheim or specify its path in Settings."
        )

    def extract_text_from_image(self, image: Image.Image, lang: str = "eng") -> str:
        """Run OCR on a PIL Image if Tesseract is available."""
        if not self.is_available:
            raise RuntimeError(
                "OCR requested but Tesseract executable is not configured or found."
            )

        try:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = self._detected_path
            text = pytesseract.image_to_string(image, lang=lang)
            return text.strip()
        except Exception as ex:
            logger.error(f"Error during OCR execution: {ex}")
            raise RuntimeError(f"OCR processing failed: {ex}") from ex
