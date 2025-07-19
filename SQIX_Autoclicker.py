# Import modules
import sys
import os
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QSpinBox, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import pyautogui

# Thread class for handling clicking functionality
class ClickerThread(QThread):
    update_signal = pyqtSignal(str)  # Signal to send status message to main

    def __init__(self, interval, test_mode=False):
        super().__init__()
        self.interval = interval  # Interval between clicks
        self.click_count = 0  # Count of clicks
        self.running = True  # Control flag
        self.test_mode = test_mode  # Whether real click is enabled

    def run(self):
        # Main loop that clicks at specified interval
        while self.running:
            self.click_screen()
            self.click_count += 1
            message = f"SQIX<sup>™</sup> in action - The ants go marching {self.click_count} by {self.click_count} hurrah, hurrah!"
            print(message)
            self.update_signal.emit(message)
          #  time.sleep(self.interval)

            # Break long sleep into smaller intervals for responsiveness
            elapsed = 0
            while elapsed < self.interval and self.running:
                time.sleep(0.1)
                elapsed += 0.1

    def stop(self):
        # Gracefully stop the thread
        self.running = False

    # Optional: original real clicking method (commented out for testing)
    # def click_screen(self):
    #     try:
    #         current_x, current_y = pyautogui.position()
    #         pyautogui.click()
    #         pyautogui.moveTo(current_x, current_y)
    #     except Exception as e:
    #         error_message = f"Error: {str(e)}"
    #         print(error_message)
    #         self.update_signal.emit(error_message)

    def click_screen(self):
        try:
            current_x, current_y = pyautogui.position()
            if self.test_mode:
                print(f"[TEST MODE] Simulated click at ({current_x}, {current_y})")
            else:
                pyautogui.click()
                pyautogui.moveTo(current_x, current_y)
        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(error_message)
            self.update_signal.emit(error_message)


# Main app class
class AutoClickerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.clicker_thread = None

    def initUI(self):
        self.setWindowTitle('SQIX\u2122 AutoClicker')
        self.setGeometry(300, 300, 400, 300)
        main_layout = QVBoxLayout()

        # SQIX logo
        face_label = QLabel(self)
        image_path = self.resource_path("Sqix_Horizontal_Transparent.png")
        pixmap = QPixmap(image_path)
        face_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        face_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(face_label)

        # Status message
        self.status_label = QLabel('Hi, I am SQIX<sup>™</sup> and I am ready to help you play hooky', self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setTextFormat(Qt.RichText)
        main_layout.addWidget(self.status_label)

        # Interval input
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel('Interval (seconds):', self)
        interval_layout.addWidget(self.interval_label)

        self.interval_spinbox = QSpinBox(self)
        self.interval_spinbox.setRange(1, 3600)
        self.interval_spinbox.setValue(120)
        interval_layout.addWidget(self.interval_spinbox)
        main_layout.addLayout(interval_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_clicking)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_clicking)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def resource_path(self, relative_path):
        """ Get absolute path to resource (image, etc.), works for dev and PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def start_clicking(self):
        if not self.clicker_thread:
            interval = self.interval_spinbox.value()
            self.clicker_thread = ClickerThread(interval, test_mode=True)  # test_mode=True avoids real clicks
            self.clicker_thread.update_signal.connect(self.update_status)
            self.clicker_thread.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            message = 'Hi, I am SQIX<sup>™</sup> and I am ready to help you play hooky'
            self.status_label.setTextFormat(Qt.RichText)
            self.status_label.setText(message)
            print(message)

    def stop_clicking(self):
        if self.clicker_thread:
            self.clicker_thread.stop()
            self.clicker_thread.wait()
            self.clicker_thread = None
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            message = 'SQIX<sup>™</sup> is tired'
            self.status_label.setTextFormat(Qt.RichText)
            self.status_label.setText(message)
            print(message)

    def update_status(self, message):
        self.status_label.setTextFormat(Qt.RichText)
        self.status_label.setText(message)
        print(f"Status update: {message}")

    def closeEvent(self, event):
        if self.clicker_thread:
            self.clicker_thread.stop()
            self.clicker_thread.wait()
        print("SQIX™ is leaving")
        event.accept()

# Entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutoClickerApp()
    ex.show()
    sys.exit(app.exec_())
