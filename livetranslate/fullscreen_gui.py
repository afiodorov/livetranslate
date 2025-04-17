import signal
import sys
from collections.abc import Callable

from PySide6.QtCore import Qt, Signal, SignalInstance, Slot
from PySide6.QtGui import QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class SubtitleMapWindow(QMainWindow):
    update_subtitles_signal = Signal(str)
    close_signal = Signal()

    def __init__(self):
        super().__init__()
        self.init_ui()

        self.dragging = False
        self.offset = None

        self.update_subtitles_signal.connect(self.update_subtitles)

    def init_ui(self):
        self.setCursor(Qt.OpenHandCursor)
        self.setWindowTitle("LiveTranslate")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Create a central widget
        central_widget = QWidget(self)
        central_widget.setAutoFillBackground(True)
        palette = central_widget.palette()
        palette.setColor(
            QPalette.Window, QColor(0, 0, 0)
        )  # Set background color to black
        central_widget.setPalette(palette)
        self.setCentralWidget(central_widget)

        # Layout for the label
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)  # Center alignment

        self.current_subtitle_label = QLabel("Starting text", self)
        self.current_subtitle_label.setAlignment(Qt.AlignCenter)
        self.current_subtitle_label.setWordWrap(True)
        self.current_subtitle_label.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Expanding
        )

        # Set font size
        default_font = QApplication.font()
        default_font.setPixelSize(100)
        self.current_subtitle_label.setFont(default_font)

        dark_yellow = QColor(180, 140, 0)  # RGB values for dark yellow

        label_style: str = f"""
            QLabel {{
                color: {dark_yellow.name()};
                background-color: transparent;
                padding: 5px;
                margin: 0px;
            }}
        """

        self.current_subtitle_label.setStyleSheet(label_style)
        layout.addWidget(self.current_subtitle_label)

    @Slot(str)
    def update_subtitles(self, current_subtitle: str) -> None:
        self.current_subtitle_label.setText(current_subtitle)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.offset = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.dragging and self.offset:
            new_pos = event.globalPos() - self.offset
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.offset = None
            self.setCursor(Qt.OpenHandCursor)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            # Emit close signal for graceful shutdown
            self.close_signal.emit()
            # Close the window
            self.close()


def start_gui() -> tuple[QApplication, Callable[[str], None], SignalInstance]:
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app: QApplication = QApplication(sys.argv)
    main_window = SubtitleMapWindow()
    main_window.showFullScreen()

    def update_subtitles_threadsafe(current_subtitle: str) -> None:
        main_window.update_subtitles_signal.emit(current_subtitle)

    return app, update_subtitles_threadsafe, main_window.close_signal
