"""Session orchestration, autosave debouncing, crash recovery, and state management."""

import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.models import (
    ContentSet,
    Preset,
    Session,
    SessionResponse,
    SRTItem,
    TATItem,
    WATItem,
)
from database.repositories import (
    ContentSetRepository,
    PresetRepository,
    SessionRepository,
)

logger = logging.getLogger(__name__)


class ActiveSessionItem:
    """Represents a single prompt item inside an active test run."""

    def __init__(
        self,
        index: int,
        identifier: str,  # Serial, filename, or word
        prompt_text: str,  # Image path, word, or situation text
        title: str = "",
    ) -> None:
        self.index = index
        self.identifier = identifier
        self.prompt_text = prompt_text
        self.title = title


class SessionService:
    """Manages active session preparation, answer debouncing, persistence, and recovery."""

    def __init__(
        self,
        session_repo: SessionRepository,
        content_repo: ContentSetRepository,
        preset_repo: PresetRepository,
    ) -> None:
        self.session_repo = session_repo
        self.content_repo = content_repo
        self.preset_repo = preset_repo

        self.current_session: Optional[Session] = None
        self.active_items: List[ActiveSessionItem] = []
        self._current_item_index: int = 0
        self._buffered_responses: Dict[int, SessionResponse] = {}

    def prepare_session(
        self,
        preset: Preset,
        content_set: ContentSet,
        override_item_count: Optional[int] = None,
    ) -> Tuple[Session, List[ActiveSessionItem]]:
        """Validate content, build sequence, and persist initial session record."""
        test_type = preset.test_type.upper()

        if test_type == "TAT":
            items = self.content_repo.get_tat_items(content_set.id)
            if not items:
                raise ValueError(f"Content set '{content_set.name}' contains no TAT images.")
            raw_seq = [
                ActiveSessionItem(
                    index=0,
                    identifier=it.original_filename,
                    prompt_text=it.file_path,
                    title=it.title or f"Picture #{it.item_order}",
                )
                for it in items
            ]

        elif test_type == "WAT":
            items = self.content_repo.get_wat_items(content_set.id)
            if not items:
                raise ValueError(f"Content set '{content_set.name}' contains no WAT words.")
            raw_seq = [
                ActiveSessionItem(
                    index=0,
                    identifier=it.word,
                    prompt_text=it.word,
                    title=f"Word #{it.item_order}",
                )
                for it in items
            ]

        elif test_type == "SRT":
            items = self.content_repo.get_srt_items(content_set.id)
            if not items:
                raise ValueError(f"Content set '{content_set.name}' contains no SRT questions.")
            raw_seq = [
                ActiveSessionItem(
                    index=0,
                    identifier=it.original_serial,
                    prompt_text=it.situation_text,
                    title=f"Situation {it.original_serial}",
                )
                for it in items
            ]
        else:
            raise ValueError(f"Unsupported test type: {test_type}")

        # Apply randomization if requested
        if preset.randomize:
            random.shuffle(raw_seq)

        # Apply item count limit
        target_count = override_item_count if override_item_count is not None else preset.item_count
        if target_count > 0:
            if len(raw_seq) >= target_count:
                selected_items = raw_seq[:target_count]
            else:
                if preset.repeat:
                    # Repeat until target_count is reached
                    selected_items = []
                    while len(selected_items) < target_count:
                        selected_items.extend(raw_seq)
                    selected_items = selected_items[:target_count]
                else:
                    selected_items = raw_seq
        else:
            selected_items = raw_seq

        # Re-index items 0 to N-1
        for idx, item in enumerate(selected_items):
            item.index = idx

        now_str = datetime.now().isoformat()
        session = Session(
            preset_id=preset.id,
            test_type=preset.test_type,
            preset_name=preset.name,
            content_set_id=content_set.id,
            content_set_name=content_set.name,
            total_items=len(selected_items),
            completed_items=0,
            is_exam_mode=preset.exam_mode,
            view_duration=preset.view_duration,
            write_duration=preset.write_duration,
            status="IN_PROGRESS",
            start_time=now_str,
            elapsed_seconds=0.0,
            evaluator_notes="",
        )

        session_id = self.session_repo.create_session(session)
        session.id = session_id

        self.current_session = session
        self.active_items = selected_items
        self._buffered_responses.clear()
        self._current_item_index = 0

        return session, selected_items

    def buffer_response(
        self,
        item_index: int,
        response_text: str,
        time_spent: float = 0.0,
    ) -> None:
        """Store draft in memory before debounce flush or transition."""
        if not self.current_session or item_index >= len(self.active_items):
            return

        item = self.active_items[item_index]
        resp = SessionResponse(
            session_id=self.current_session.id,
            item_index=item_index,
            item_identifier=item.identifier,
            prompt_text=item.prompt_text,
            response_text=response_text,
            response_length=len(response_text.strip()),
            time_spent_seconds=time_spent,
            is_completed=(len(response_text.strip()) > 0),
        )
        self._buffered_responses[item_index] = resp

    def flush_responses(self) -> None:
        """Persist all in-memory responses immediately to SQLite."""
        if not self.current_session:
            return

        for idx, resp in list(self._buffered_responses.items()):
            try:
                self.session_repo.save_response(resp)
            except Exception as e:
                logger.error(f"Error flushing response for item {idx}: {e}")

    def flush_item_response(self, item_index: int) -> None:
        """Mandatory flush for the current item before advancing slide."""
        if item_index in self._buffered_responses:
            resp = self._buffered_responses[item_index]
            self.session_repo.save_response(resp)

    def complete_session(self, elapsed_seconds: float) -> None:
        """Finalize session, flush any pending answers, update status to COMPLETED."""
        if not self.current_session:
            return

        self.flush_responses()
        now_str = datetime.now().isoformat()

        # Count completed items with non-empty responses
        saved_responses = self.session_repo.get_responses(self.current_session.id)
        completed_count = sum(1 for r in saved_responses if r.is_completed)

        self.session_repo.update_session_status(
            session_id=self.current_session.id,
            status="COMPLETED",
            completed_items=completed_count,
            elapsed_seconds=elapsed_seconds,
            end_time=now_str,
        )
        self.current_session.status = "COMPLETED"
        self.current_session.completed_items = completed_count
        self.current_session.elapsed_seconds = elapsed_seconds

    def abandon_session(self, elapsed_seconds: float) -> None:
        """Safely abandon test while preserving all answered questions to date."""
        if not self.current_session:
            return

        self.flush_responses()
        now_str = datetime.now().isoformat()

        saved_responses = self.session_repo.get_responses(self.current_session.id)
        completed_count = sum(1 for r in saved_responses if r.is_completed)

        self.session_repo.update_session_status(
            session_id=self.current_session.id,
            status="ABANDONED",
            completed_items=completed_count,
            elapsed_seconds=elapsed_seconds,
            end_time=now_str,
        )
        self.current_session.status = "ABANDONED"

    def check_crash_recovery(self) -> Optional[Session]:
        """Detect any uncompleted in-progress session from previous run."""
        return self.session_repo.get_uncompleted_session()

    @staticmethod
    def calculate_estimated_duration(
        test_type: str,
        item_count: int,
        view_duration: float,
        write_duration: float,
        countdown_seconds: int = 3,
    ) -> float:
        """Calculate total estimated session time in seconds."""
        if item_count <= 0:
            return 0.0

        if test_type.upper() == "TAT":
            per_item = view_duration + write_duration
        else:
            per_item = write_duration

        total = countdown_seconds + (item_count * per_item)
        return total
