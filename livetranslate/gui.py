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
        super().__init__(flags=Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        # Define window dimensions as class variables
        self.window_width = 1200
        self.window_height = 90

        # Create styles and fonts
        self.normal_font = QApplication.font()
        self.normal_font.setPointSize(24)

        self.fullscreen_font = QApplication.font()
        self.fullscreen_font.setPixelSize(100)

        self.dark_yellow = QColor(180, 140, 0)  # RGB values for dark yellow

        self.normal_label_style = f"""
            QLabel {{
                color: {self.dark_yellow.name()};
                background-color: rgba(0, 0, 0, 255);
                padding: 5px;
                border-radius: 5px;
                margin: 0px;
            }}
        """

        self.fullscreen_label_style = f"""
            QLabel {{
                color: {self.dark_yellow.name()};
                background-color: transparent;
                padding: 5px;
                margin: 0px;
            }}
        """

        # Track fullscreen state
        self.is_in_fullscreen = False

        self.init_ui()

        self.dragging = False
        self.drag_moved = False
        self.offset = None

        self.update_subtitles_signal.connect(self.update_subtitles)

    def init_ui(self):
        self.setCursor(Qt.OpenHandCursor)
        # Set the title and initial size of the window
        self.setWindowTitle("LiveTranslate")
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)

        # Create a central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Layout for labels
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)  # Center alignment

        # Create label for subtitles
        self.current_subtitle_label = QLabel("Starting text", self)
        self.current_subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_subtitle_label)

        # Apply normal mode settings
        self.apply_normal_mode_settings()

    def apply_normal_mode_settings(self):
        """Apply all settings for normal (non-fullscreen) mode"""
        # Set window position
        self.position_window_normal()

        # Set transparency
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        # Configure central widget background
        central_widget = self.centralWidget()
        central_widget.setAutoFillBackground(True)
        palette = central_widget.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 0))  # Fully transparent
        central_widget.setPalette(palette)

        # Configure layout
        self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)

        # Configure label appearance
        self.current_subtitle_label.setFont(self.normal_font)
        self.current_subtitle_label.setWordWrap(True)
        self.current_subtitle_label.setStyleSheet(self.normal_label_style)
        self.current_subtitle_label.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred
        )

        # Set fixed dimensions
        self.current_subtitle_label.setFixedWidth(self.window_width - 10)
        self.current_subtitle_label.setFixedHeight(self.window_height - 10)
        self.setFixedSize(self.window_width, self.window_height)

    def apply_fullscreen_mode_settings(self):
        """Apply all settings for fullscreen mode"""
        # Disable transparency
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # Configure central widget background
        central_widget = self.centralWidget()
        central_widget.setAutoFillBackground(True)
        palette = central_widget.palette()
        palette.setColor(
            QPalette.Window, QColor(0, 0, 0, 255)
        )  # Solid black, fully opaque
        central_widget.setPalette(palette)

        # Configure layout
        self.centralWidget().layout().setContentsMargins(50, 50, 50, 50)

        # Configure label appearance
        self.current_subtitle_label.setFont(self.fullscreen_font)
        self.current_subtitle_label.setWordWrap(True)
        self.current_subtitle_label.setStyleSheet(self.fullscreen_label_style)
        self.current_subtitle_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )

        # Remove fixed size constraints
        self.current_subtitle_label.setMaximumWidth(16777215)  # QWIDGETSIZE_MAX
        self.current_subtitle_label.setMaximumHeight(16777215)  # QWIDGETSIZE_MAX
        self.setMaximumSize(16777215, 16777215)  # QWIDGETSIZE_MAX

    def position_window_normal(self):
        """Position the window at the bottom center of the screen"""
        screen = QApplication.primaryScreen().geometry()
        x_position = (screen.width() - self.window_width) // 2  # Center horizontally
        available_screen = QApplication.primaryScreen().availableGeometry()
        y_position = (
            available_screen.height() + available_screen.y() - self.window_height
        )
        self.setGeometry(x_position, y_position, self.window_width, self.window_height)

    @Slot(str)
    def update_subtitles(self, current_subtitle: str) -> None:
        self.current_subtitle_label.setText(current_subtitle)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.drag_moved = False
            self.offset = event.pos()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self.offset:
            new_pos = event.globalPos() - self.offset
            self.move(new_pos)
            self.dragging = True
            self.drag_moved = True

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.drag_moved:
                text = self.current_subtitle_label.text()
                if text:
                    QApplication.clipboard().setText(text)
            self.dragging = False
            self.drag_moved = False
            self.offset = None
            self.setCursor(Qt.OpenHandCursor)

    def showFullScreen(self):
        if self.is_in_fullscreen:
            return

        # Apply fullscreen settings
        self.apply_fullscreen_mode_settings()

        # Now actually go fullscreen
        super().showFullScreen()
        self.is_in_fullscreen = True

    def showNormal(self):
        if not self.is_in_fullscreen:
            return

        # First exit fullscreen mode
        super().showNormal()

        # Apply normal mode settings (reuses the same code as initialization)
        self.apply_normal_mode_settings()

        self.is_in_fullscreen = False

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            # Check if in fullscreen mode
            if self.is_in_fullscreen:
                # Exit fullscreen and return to normal window
                self.showNormal()

                # Don't attempt to close the window in the same keypress
                # This avoids potential race conditions with window state changes
                event.accept()
                return
            else:
                # Emit close signal for graceful shutdown
                self.close_signal.emit()
                # Close the window
                self.close()
        elif event.key() == Qt.Key_F:
            # Toggle fullscreen mode
            if self.is_in_fullscreen:
                self.showNormal()
            else:
                self.showFullScreen()


def start_gui() -> tuple[QApplication, Callable[[str], None], SignalInstance]:
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app: QApplication = QApplication(sys.argv)
    main_window = SubtitleMapWindow()
    main_window.show()

    def update_subtitles_threadsafe(current_subtitle: str) -> None:
        main_window.update_subtitles_signal.emit(current_subtitle)

    return app, update_subtitles_threadsafe, main_window.close_signal
