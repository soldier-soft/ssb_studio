"""Tests for natural filename and serial sorting."""

from core.natural_sort import natural_key, natural_sort


def test_natural_sort_numbers():
    files = ["img10.jpg", "img1.jpg", "img2.jpg", "img20.jpg", "img3.jpg"]
    sorted_files = natural_sort(files)
    assert sorted_files == ["img1.jpg", "img2.jpg", "img3.jpg", "img10.jpg", "img20.jpg"]


def test_natural_sort_case_insensitivity():
    items = ["Pic2.PNG", "pic1.png", "PIC10.png"]
    sorted_items = natural_sort(items)
    assert sorted_items == ["pic1.png", "Pic2.PNG", "PIC10.png"]


def test_natural_sort_with_custom_key():
    data = [
        {"name": "Set 10", "id": 10},
        {"name": "Set 2", "id": 2},
        {"name": "Set 1", "id": 1},
    ]
    sorted_data = natural_sort(data, key=lambda x: x["name"])
    assert [d["id"] for d in sorted_data] == [1, 2, 10]
