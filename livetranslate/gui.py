import signal
import sys
from typing import Callable

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QVBoxLayout, QWidget


class SubtitleMapWindow(QMainWindow):
    update_subtitles_signal = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.initUI()

        self.update_subtitles_signal.connect(self.update_subtitles)

    def initUI(self):
        # Set the title and initial size of the window
        self.setWindowTitle("LiveTranslate")
        screen = QApplication.primaryScreen().geometry()
        window_width = 1200
        window_height = 100

        x_position = (
            screen.width() - window_width
        ) // 2  # Center the window on the screen
        y_position = screen.height() - window_height
        self.setGeometry(x_position, y_position, window_width, window_height)

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Layout for labels
        layout = QVBoxLayout(central_widget)

        # Create labels for previous and current subtitles
        self.prev_subtitle_label = QLabel("Previous subtitle", self)
        self.current_subtitle_label = QLabel("Current subtitle", self)

        # Set the alignment and add to layout
        self.prev_subtitle_label.setAlignment(Qt.AlignCenter)
        self.current_subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_subtitle_label)
        layout.addWidget(self.prev_subtitle_label)

        # Set font size
        default_font = QApplication.font()
        default_font.setPointSize(24)
        self.prev_subtitle_label.setFont(default_font)
        self.current_subtitle_label.setFont(default_font)

    @Slot(str, str)
    def update_subtitles(self, prev_subtitle: str, current_subtitle: str) -> None:
        self.prev_subtitle_label.setText(prev_subtitle)
        self.current_subtitle_label.setText(current_subtitle)


def start_gui() -> tuple[QApplication, Callable[[str, str], None]]:
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app: QApplication = QApplication(sys.argv)
    main_window = SubtitleMapWindow()
    main_window.show()

    def update_subtitles_threadsafe(prev_subtitle: str, current_subtitle: str) -> None:
        main_window.update_subtitles_signal.emit(prev_subtitle, current_subtitle)

    return app, update_subtitles_threadsafe
