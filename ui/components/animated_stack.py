"""Animated stacked widget providing smooth fade transitions between screens."""

from typing import Optional
from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect, QStackedWidget, QWidget


class AnimatedStackedWidget(QStackedWidget):
    """QStackedWidget subclass that performs smooth crossfade animations between pages."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._anim: Optional[QPropertyAnimation] = None

    def fade_to_index(self, index: int, duration_ms: int = 200) -> None:
        """Switch to target page with a smooth opacity crossfade."""
        if index == self.currentIndex() or index < 0 or index >= self.count():
            return

        target_widget = self.widget(index)
        if not target_widget:
            self.setCurrentIndex(index)
            return

        # Setup opacity effect on target widget
        eff = QGraphicsOpacityEffect(target_widget)
        target_widget.setGraphicsEffect(eff)
        eff.setOpacity(0.0)

        # Switch to widget
        self.setCurrentIndex(index)

        # Animate opacity 0.0 -> 1.0
        self._anim = QPropertyAnimation(eff, b"opacity")
        self._anim.setDuration(duration_ms)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def on_finished():
            target_widget.setGraphicsEffect(None)
            self._anim = None

        self._anim.finished.connect(on_finished)
        self._anim.start()

