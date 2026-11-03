"""Tests for document parsers (WAT word lists, SRT situation extractions with serial gap preservation)."""

from pathlib import Path
from services.pdf_parser import DocumentParser


def test_parse_wat_words_clean(temp_dir: Path, doc_parser: DocumentParser):
    txt_file = temp_dir / "sample_wat.txt"
    txt_file.write_text(
        """
        1. Courage
        2. RESPONSIBLE
        3. leader
        4) Team-work
        5. Sacrifice
        """,
        encoding="utf-8",
    )

    res = doc_parser.parse_wat_file(txt_file)
    assert res.total_words == 5
    assert res.words == ["COURAGE", "RESPONSIBLE", "LEADER", "TEAM-WORK", "SACRIFICE"]


def test_parse_wat_words_comma_separated(temp_dir: Path, doc_parser: DocumentParser):
    txt_file = temp_dir / "words_comma.txt"
    txt_file.write_text("Duty, Honour, Country, Integrity, Respect", encoding="utf-8")

    res = doc_parser.parse_wat_file(txt_file)
    assert res.words == ["DUTY", "HONOUR", "COUNTRY", "INTEGRITY", "RESPECT"]


def test_parse_srt_serial_patterns_and_gaps(temp_dir: Path, doc_parser: DocumentParser):
    txt_file = temp_dir / "sample_srt.txt"
    txt_file.write_text(
        """
        1. He was on his way to exam when he saw a child drowning in the river. He...
        2) His captain was injured in the front line. He...
        5. There was a sudden fire in his college lab. He...
        14a. While travelling on a night train, he noticed smoke coming from adjacent coach. He...
        (15) The bridge was blown up by insurgents. He...
        """,
        encoding="utf-8",
    )

    res = doc_parser.parse_srt_file(txt_file)
    assert len(res.items) == 5

    serials = [item[0] for item in res.items]
    # Verify original serials are preserved without silent renumbering!
    assert serials == ["1", "2", "5", "14a", "15"]

    assert "child drowning" in res.items[0][1]
    assert "injured in the front" in res.items[1][1]
    assert "sudden fire" in res.items[2][1]
    assert "adjacent coach" in res.items[3][1]
    assert "blown up" in res.items[4][1]


def test_parse_srt_multiline_continuation(temp_dir: Path, doc_parser: DocumentParser):
    txt_file = temp_dir / "multiline_srt.txt"
    txt_file.write_text(
        """
        1. He was trekking in the high mountains with four friends
        when a blizzard struck and one friend broke his leg.
        He...
        2. He lost his wallet and train ticket at a strange station. He...
        """,
        encoding="utf-8",
    )

    res = doc_parser.parse_srt_file(txt_file)
    assert len(res.items) == 2
    assert res.items[0][0] == "1"
    assert "high mountains with four friends when a blizzard struck and one friend broke his leg" in res.items[0][1]
    assert res.items[1][0] == "2"


def test_parse_empty_files(temp_dir: Path, doc_parser: DocumentParser):
    empty_txt = temp_dir / "empty.txt"
    empty_txt.write_text("", encoding="utf-8")

    wat_res = doc_parser.parse_wat_file(empty_txt)
    assert wat_res.total_words == 0
    assert len(wat_res.warnings) > 0

    srt_res = doc_parser.parse_srt_file(empty_txt)
    assert len(srt_res.items) == 0
    assert len(srt_res.warnings) > 0


def test_parse_wat_pdf(temp_dir: Path, doc_parser: DocumentParser):
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "1. COURAGE\n2. DETERMINATION\n3. LOYALTY\n4. PATRIOTISM")
    pdf_path = temp_dir / "test_wat.pdf"
    doc.save(str(pdf_path))
    doc.close()

    res = doc_parser.parse_wat_file(pdf_path)
    assert res.total_words == 4
    assert res.words == ["COURAGE", "DETERMINATION", "LOYALTY", "PATRIOTISM"]
    assert res.source_type == "pdf"


def test_parse_srt_pdf(temp_dir: Path, doc_parser: DocumentParser):
    import fitz
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (50, 50),
        "1. He was crossing a bridge when a car plunged into the river. He...\n"
        "2. His colleague fainted during a high altitude parade. He...\n"
    )
    pdf_path = temp_dir / "test_srt.pdf"
    doc.save(str(pdf_path))
    doc.close()

    res = doc_parser.parse_srt_file(pdf_path)
    assert len(res.items) == 2
    assert res.items[0][0] == "1"
    assert "crossing a bridge" in res.items[0][1]
    assert res.items[1][0] == "2"


def test_parse_wat_txt_utf8_bom(temp_dir: Path, doc_parser: DocumentParser):
    txt_file = temp_dir / "sample_bom.txt"
    txt_file.write_text("1. BRAVE\n2. HONEST\n3. ACTIVE", encoding="utf-8-sig")

    res = doc_parser.parse_wat_file(txt_file)
    assert res.words == ["BRAVE", "HONEST", "ACTIVE"]


def test_parse_srt_fallback_sequential(temp_dir: Path, doc_parser: DocumentParser):
    txt_file = temp_dir / "unnumbered_srt.txt"
    txt_file.write_text(
        "Situation Reaction Test Bank\n"
        "He saw a fire breaking out in the library and people shouting.\n"
        "While walking home at midnight he noticed two burglars entering neighbor's house.\n",
        encoding="utf-8",
    )

    res = doc_parser.parse_srt_file(txt_file)
    assert len(res.items) == 2
    assert res.items[0][0] == "1"
    assert "fire breaking out" in res.items[0][1]
    assert res.items[1][0] == "2"
    assert "burglars entering" in res.items[1][1]


def test_parse_srt_60_situations_with_ellipsis_rules(temp_dir: Path, doc_parser: DocumentParser):
    """Test Rule 1 (1-60 serial sequence) and Rule 2 (sentences ending with '(...)' normalization)."""
    lines = ["SSB SRT TEST - 60 OFFICIAL SITUATIONS", "TIME: 30 MINUTES"]
    for i in range(1, 61):
        if i % 3 == 0:
            lines.append(f"{i}. Situation prompt #{i} involving sudden crisis in mountain patrol. He...")
        elif i % 3 == 1:
            lines.append(f"{i}) Situation prompt #{i} in college when fire alarm rang. He (...)")
        else:
            lines.append(f"({i}) Situation prompt #{i} during train journey when wallet was lost. He")

    txt_file = temp_dir / "srt_60_test.txt"
    txt_file.write_text("\n".join(lines), encoding="utf-8")

    res = doc_parser.parse_srt_file(txt_file)
    assert len(res.items) == 60
    # Rule 1: Serials 1 to 60 verified
    assert res.items[0][0] == "1"
    assert res.items[59][0] == "60"
    for idx, (serial, prompt) in enumerate(res.items, 1):
        assert serial == str(idx)
        # Rule 2: Sentences must end with '( ... )'
        assert prompt.endswith("(...)"), f"Item {serial} does not end with (...): {prompt}"


def test_parse_srt_pdf_60_items_with_blocks_and_lone_numbers(temp_dir: Path, doc_parser: DocumentParser):
    """Test extracting 60 situations from PDF with standalone serial numbers and page breaks."""
    import fitz

    doc = fitz.open()
    # Distribute across 3 pages
    for page_num in range(3):
        page = doc.new_page()
        page_lines = [f"PAGE {page_num + 1} OF 3 - CONFIDENTIAL"]
        start_idx = page_num * 20 + 1
        end_idx = start_idx + 20
        for i in range(start_idx, end_idx):
            # Mix lone serial numbers and inline
            if i % 2 == 0:
                page_lines.append(f"{i}\nHe was on a river rafting trip when the boat capsized. He...")
            else:
                page_lines.append(f"{i}. While crossing an old bridge he heard planks cracking. He (...)")
        page.insert_text((40, 40), "\n\n".join(page_lines))

    pdf_path = temp_dir / "srt_60_multipage.pdf"
    doc.save(str(pdf_path))
    doc.close()

    res = doc_parser.parse_srt_file(pdf_path)
    assert len(res.items) == 60
    assert res.items[0][0] == "1"
    assert res.items[59][0] == "60"
    for serial, prompt in res.items:
        assert prompt.endswith("(...)")


