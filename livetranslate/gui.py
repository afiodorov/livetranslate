import signal
import sys
from collections.abc import Callable

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QPalette
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

    def __init__(self):
        super().__init__(flags=Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.init_ui()

        self.update_subtitles_signal.connect(self.update_subtitles)

    def init_ui(self):
        # Set the title and initial size of the window
        self.setWindowTitle("LiveTranslate")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        self.setAttribute(Qt.WA_TranslucentBackground)

        screen = QApplication.primaryScreen().geometry()
        window_width = 1200
        window_height = 50

        x_position = (
            screen.width() - window_width
        ) // 2  # Center the window on the screen
        y_position = screen.height() - window_height
        self.setGeometry(x_position, y_position, window_width, window_height)

        # Create a central widget
        central_widget = QWidget(self)
        central_widget.setAutoFillBackground(True)
        palette = central_widget.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 0))
        central_widget.setPalette(palette)
        self.setCentralWidget(central_widget)

        # Layout for labels
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create labels for previous and current subtitles
        self.current_subtitle_label = QLabel("Starting text", self)

        # Set the alignment and add to layout
        self.current_subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_subtitle_label)

        # Set font size
        default_font = QApplication.font()
        default_font.setPointSize(24)
        self.current_subtitle_label.setFont(default_font)

        dark_yellow = QColor(180, 140, 0)  # RGB values for dark yellow

        label_style: str = f"""
            QLabel {{
                color: {dark_yellow.name()};
                background-color: black;
                padding: 5px;
                border-radius: 5px;
                margin: 0px;
            }}
        """

        self.current_subtitle_label.setStyleSheet(label_style)
        self.current_subtitle_label.setAlignment(Qt.AlignCenter)
        self.current_subtitle_label.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred
        )

        self.current_subtitle_label.setFixedWidth(window_width - 10)
        self.current_subtitle_label.setFixedHeight(window_height - 10)
        self.setFixedSize(window_width, window_height)

    @Slot(str)
    def update_subtitles(self, current_subtitle: str) -> None:
        self.current_subtitle_label.setText(current_subtitle)


def start_gui() -> tuple[QApplication, Callable[[str], None]]:
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app: QApplication = QApplication(sys.argv)
    main_window = SubtitleMapWindow()
    main_window.show()

    def update_subtitles_threadsafe(current_subtitle: str) -> None:
        main_window.update_subtitles_signal.emit(current_subtitle)

    return app, update_subtitles_threadsafe
