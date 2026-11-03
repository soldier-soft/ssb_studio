"""Lightweight floating toast notifications with smooth fade and slide animations."""

from typing import Optional
from PySide6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget


class ToastNotification(QLabel):
    """Temporary notification banner that slides up, glows, and smoothly fades away."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self._fade_anim: Optional[QPropertyAnimation] = None

        self._dismiss_timer = QTimer(self)
        self._dismiss_timer.setSingleShot(True)
        self._dismiss_timer.timeout.connect(self._fade_out)

    def show_message(
        self,
        message: str,
        duration_ms: int = 3000,
        is_error: bool = False,
    ) -> None:
        self.setText(message)
        if is_error:
            self.setStyleSheet(
                """
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #991B1B, stop:1 #B91C1C);
                    color: #FFFFFF;
                    border: 1.5px solid #F87171;
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 0.3px;
                }
                """
            )
        else:
            self.setStyleSheet(
                """
                QLabel {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #064E3B, stop:1 #065F46);
                    color: #FFFFFF;
                    border: 1.5px solid #34D399;
                    border-radius: 10px;
                    padding: 12px 24px;
                    font-size: 13px;
                    font-weight: 700;
                    letter-spacing: 0.3px;
                }
                """
            )
        self.adjustSize()

        parent_w = self.parentWidget()
        if parent_w:
            x = (parent_w.width() - self.width()) // 2
            y = parent_w.height() - self.height() - 44
            self.move(parent_w.mapToGlobal(QPoint(x, y)))

        self.opacity_effect.setOpacity(0.0)
        self.show()
        self.raise_()

        # Fade in
        self._fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._fade_anim.setDuration(220)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_anim.start()

        self._dismiss_timer.start(duration_ms)

    def _fade_out(self) -> None:
        self._fade_anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self._fade_anim.setDuration(300)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_anim.finished.connect(self.hide)
        self._fade_anim.start()
