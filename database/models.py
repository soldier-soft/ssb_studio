"""Domain data models for SSB Practice Studio."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class ContentSet:
    id: Optional[int] = None
    test_type: str = "WAT"  # "TAT", "WAT", "SRT"
    name: str = ""
    source_file: str = ""
    item_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata_json: str = "{}"


@dataclass
class TATItem:
    id: Optional[int] = None
    set_id: int = 0
    item_order: int = 0
    file_path: str = ""
    original_filename: str = ""
    title: str = ""


@dataclass
class WATItem:
    id: Optional[int] = None
    set_id: int = 0
    item_order: int = 0
    word: str = ""


@dataclass
class SRTItem:
    id: Optional[int] = None
    set_id: int = 0
    item_order: int = 0
    original_serial: str = "1"
    situation_text: str = ""


@dataclass
class Preset:
    id: Optional[int] = None
    name: str = ""
    test_type: str = "WAT"
    view_duration: float = 0.0  # seconds (used in TAT)
    write_duration: float = 15.0  # seconds (WAT=15, SRT=30, TAT=270)
    item_count: int = 60
    randomize: bool = False
    repeat: bool = False
    countdown_seconds: int = 3
    sound_enabled: bool = True
    exam_mode: bool = True
    is_builtin: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Session:
    id: Optional[int] = None
    preset_id: Optional[int] = None
    test_type: str = "WAT"
    preset_name: str = ""
    content_set_id: Optional[int] = None
    content_set_name: str = ""
    total_items: int = 0
    completed_items: int = 0
    is_exam_mode: bool = True
    view_duration: float = 0.0
    write_duration: float = 15.0
    status: str = "IN_PROGRESS"  # "IN_PROGRESS", "COMPLETED", "ABANDONED"
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    elapsed_seconds: float = 0.0
    evaluator_notes: str = ""
    user_rating: Optional[int] = None


@dataclass
class SessionResponse:
    id: Optional[int] = None
    session_id: int = 0
    item_index: int = 0
    item_identifier: str = ""  # original serial / image file / word
    prompt_text: str = ""
    response_text: str = ""
    response_length: int = 0
    time_spent_seconds: float = 0.0
    is_completed: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class UserGoal:
    id: Optional[int] = None
    test_type: str = "ALL"
    goal_text: str = ""
    target_count: int = 0
    target_date: Optional[str] = None
    is_achieved: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
