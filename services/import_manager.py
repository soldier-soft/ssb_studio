"""Content import manager for TAT images, WAT word lists, and SRT situation sets."""

import hashlib
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from PIL import Image

from app.config import get_library_asset_dir
from core.natural_sort import natural_sort
from database.repositories import ContentSetRepository
from services.pdf_parser import DocumentParser, SRTParseResult, WATParseResult

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def compute_file_hash(path: Path) -> str:
    """Calculate SHA-256 hash for file content deduplication."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ImportManager:
    """Orchestrates asset discovery, deduplication, safe copying, and database insertion."""

    def __init__(
        self,
        repo: ContentSetRepository,
        doc_parser: DocumentParser,
    ) -> None:
        self.repo = repo
        self.parser = doc_parser

    # -------------------------------------------------------------
    # TAT Import
    # -------------------------------------------------------------
    def scan_tat_images(
        self, paths: List[Path | str]
    ) -> Tuple[List[Path], List[Path]]:
        """
        Scan given file or directory paths for supported images.
        Returns (sorted_valid_paths, duplicate_paths).
        Naturally sorts image filenames.
        """
        collected_files: List[Path] = []

        for p in paths:
            path = Path(p)
            if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                collected_files.append(path)
            elif path.is_dir():
                for root, _, files in os.walk(path):
                    for file in files:
                        fpath = Path(root) / file
                        if fpath.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS:
                            collected_files.append(fpath)

        # Natural sort on filename
        sorted_files = natural_sort(collected_files, key=lambda x: x.name)

        # Detect duplicates by hash
        seen_hashes: Dict[str, Path] = {}
        unique_paths: List[Path] = []
        duplicate_paths: List[Path] = []

        for file_path in sorted_files:
            try:
                # Quick verify that Pillow can open image
                with Image.open(file_path) as img:
                    img.verify()
                f_hash = compute_file_hash(file_path)
                if f_hash in seen_hashes:
                    duplicate_paths.append(file_path)
                else:
                    seen_hashes[f_hash] = file_path
                    unique_paths.append(file_path)
            except Exception as e:
                logger.warning(f"Skipping unreadable image {file_path}: {e}")

        return unique_paths, duplicate_paths

    def import_tat_set(
        self,
        name: str,
        image_paths: List[Path],
        source_label: str = "",
    ) -> int:
        """
        Creates a new TAT ContentSet and safely copies images into user asset directory.
        Returns the new ContentSet ID.
        """
        if not image_paths:
            raise ValueError("No images provided for TAT set creation.")

        set_id = self.repo.create_content_set(
            test_type="TAT",
            name=name,
            source_file=source_label or str(image_paths[0].parent),
            metadata={"source_count": len(image_paths)},
        )

        dest_dir = get_library_asset_dir() / f"tat_set_{set_id}"
        dest_dir.mkdir(parents=True, exist_ok=True)

        items_to_insert: List[Tuple[int, str, str, str]] = []

        for order, src_path in enumerate(image_paths, start=1):
            dest_filename = f"{order:03d}_{src_path.name}"
            dest_file_path = dest_dir / dest_filename
            shutil.copy2(src_path, dest_file_path)

            items_to_insert.append(
                (order, str(dest_file_path), src_path.name, f"Picture #{order}")
            )

        self.repo.add_tat_items(set_id, items_to_insert)
        return set_id

    # -------------------------------------------------------------
    # WAT Import
    # -------------------------------------------------------------
    def preview_wat_file(self, file_path: Path | str) -> WATParseResult:
        """Extract words for review before saving."""
        return self.parser.parse_wat_file(file_path)

    def import_wat_set(
        self,
        name: str,
        words: List[str],
        source_file: str = "",
    ) -> int:
        if not words:
            raise ValueError("Word list cannot be empty.")

        set_id = self.repo.create_content_set(
            test_type="WAT",
            name=name,
            source_file=source_file,
            metadata={"word_count": len(words)},
        )
        self.repo.add_wat_items(set_id, words)
        return set_id

    # -------------------------------------------------------------
    # SRT Import
    # -------------------------------------------------------------
    def preview_srt_file(self, file_path: Path | str) -> SRTParseResult:
        """Extract questions with serial numbers for review before saving."""
        return self.parser.parse_srt_file(file_path)

    def import_srt_set(
        self,
        name: str,
        items: List[Tuple[str, str]],  # [(original_serial, situation_text)]
        source_file: str = "",
    ) -> int:
        if not items:
            raise ValueError("SRT situation list cannot be empty.")

        set_id = self.repo.create_content_set(
            test_type="SRT",
            name=name,
            source_file=source_file,
            metadata={"situation_count": len(items)},
        )
        self.repo.add_srt_items(set_id, items)
        return set_id
