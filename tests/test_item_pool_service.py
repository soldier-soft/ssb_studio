"""Tests for ItemPoolService non-repeater cycles and 2-day exclusion difference."""

import pytest
from app.app_context import AppContext
from services.item_pool_service import ItemPoolService


def test_item_pool_service_daily_task_generation(tmp_path):
    db_path = tmp_path / "test_pool.db"
    ctx = AppContext(db_path=db_path)
    service = ItemPoolService(ctx)

    task = service.get_daily_task()
    assert "tat" in task
    assert "wat" in task
    assert "srt" in task
    assert len(task["tat"]) == 2
    assert len(task["wat"]) == 15
    assert len(task["srt"]) == 15

    # Check streak initial
    streak = service.get_streak()
    assert streak >= 0

    # Record completion
    new_streak = service.record_daily_completion()
    assert new_streak == 1
    assert service.get_streak() == 1


def test_item_pool_service_no_repeater_and_difference(tmp_path):
    db_path = tmp_path / "test_pool2.db"
    ctx = AppContext(db_path=db_path)
    service = ItemPoolService(ctx)

    day1 = service.get_daily_task()
    day1_wat_ids = {w["id"] for w in day1["wat"]}
    service.record_daily_completion()

    day2 = service.get_daily_task()
    day2_wat_ids = {w["id"] for w in day2["wat"]}

    # Because day 1 was recorded in history, day 2 should exclude day 1 items
    intersection = day1_wat_ids.intersection(day2_wat_ids)
    assert len(intersection) == 0, f"Expected non-overlapping sets between consecutive days, got {intersection}"

