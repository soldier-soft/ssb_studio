"""Tests for ImportManager scanning, deduplication, and safe copying."""

from pathlib import Path
from PIL import Image
from services.import_manager import ImportManager, compute_file_hash


def test_tat_scan_and_deduplication(temp_dir: Path, import_mgr: ImportManager):
    img_dir = temp_dir / "tat_source"
    img_dir.mkdir()

    # Create 3 unique images and 1 duplicate
    img1 = img_dir / "img1.jpg"
    img2 = img_dir / "img2.jpg"
    img3_dup = img_dir / "img3_copy.jpg"

    Image.new("RGB", (100, 100), color=(255, 0, 0)).save(img1)
    Image.new("RGB", (100, 100), color=(0, 255, 0)).save(img2)
    # Identical content to img1
    Image.new("RGB", (100, 100), color=(255, 0, 0)).save(img3_dup)

    unique_paths, dup_paths = import_mgr.scan_tat_images([img_dir])

    assert len(unique_paths) == 2
    assert len(dup_paths) == 1
    assert compute_file_hash(img1) == compute_file_hash(img3_dup)


def test_import_tat_set_safely_copies(temp_dir: Path, import_mgr: ImportManager, repos):
    img_dir = temp_dir / "source_imgs"
    img_dir.mkdir()

    paths = []
    for i in range(3):
        p = img_dir / f"pic_{i}.png"
        Image.new("RGB", (50, 50), color=(i * 20, 50, 100)).save(p)
        paths.append(p)

    set_id = import_mgr.import_tat_set("Test Copied Set", paths)
    assert set_id > 0

    content_repo = repos["content"]
    items = content_repo.get_tat_items(set_id)
    assert len(items) == 3

    # Verify copied file exists at destination
    for it in items:
        assert Path(it.file_path).exists()
        assert Path(it.file_path) != paths[it.item_order - 1]  # Copied to safe user assets!


def test_seed_sample_content(temp_dir: Path):
    from app.app_context import AppContext
    db_file = temp_dir / "test_app_ctx.db"
    ctx = AppContext(db_path=db_file)
    wat_sets = ctx.content_repo.list_content_sets("WAT")
    srt_sets = ctx.content_repo.list_content_sets("SRT")
    tat_sets = ctx.content_repo.list_content_sets("TAT")
    assert len(wat_sets) >= 1
    assert len(srt_sets) >= 1
    assert len(tat_sets) >= 1
    assert wat_sets[0].item_count == 60
    assert srt_sets[0].item_count == 60
    # Verify rule 2 for seeded SRT items
    srt_items = ctx.content_repo.get_srt_items(srt_sets[0].id)
    assert len(srt_items) == 60
    for item in srt_items:
        assert item.situation_text.strip().endswith("(...)")
    assert tat_sets[0].item_count == 4
