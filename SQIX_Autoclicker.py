# import modules

import sys
import time
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel, QSpinBox, QHBoxLayout
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap
import pyautogui

# Thread class for handling clicking func.

class ClickerThread(QThread):
    update_signal = pyqtSignal(str) # Signal to send status message to main

    def __init__(self, interval):
        QThread.__init__(self)
        self.interval = interval # interval betwen clicks
        self.click_count = 0 # Count of clicks
        self.running = True # COntrol flag


    def run(self):
        # Main loop that clicks at specified interval bu user
        while self.running:
            self.click_screen()
            self.click_count += 1
            message = f"SQIX in action - The ants go marching {self.click_count} by {self.click_count} hurrah, hurrah!"
            print(message)  # Print to terminal
            self.update_signal.emit(message) # Signal to update
            time.sleep(self.interval)

    def stop(self):
        # Stop thread
        self.running = False

    def click_screen(self):
        # Simulating mouse click without chanign cursor pos.
        try:
            current_x, current_y = pyautogui.position()
            pyautogui.click()
            pyautogui.moveTo(current_x, current_y) # Return back cursor to original x,y : Placing for future enhancementsif cursor is moved and also to be extra safe
        except Exception as e:
            error_message = f"Error: {str(e)}"
            print(error_message)  # Print error to terminal
            self.update_signal.emit(error_message)

# Main app class

class AutoClickerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.clicker_thread = None # Initialize clicker thread

    def initUI(self):
        # Setup window
        self.setWindowTitle('SQIX AutoClicker')
        self.setGeometry(300, 300, 400, 300)
        main_layout = QVBoxLayout()

        # Add SQIX's logo
        face_label = QLabel(self)
        pixmap = QPixmap('Sqix_Horizontal_Transparent.png')
        face_label.setPixmap(pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        face_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(face_label)

        # Status labels to display message
        self.status_label = QLabel('Hi, I am SQIX and I am ready to help you play hooky', self)
        self.status_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        
        # Layout for interval input
        interval_layout = QHBoxLayout()
        self.interval_label = QLabel('Interval (seconds):', self)
        interval_layout.addWidget(self.interval_label)

        self.interval_spinbox = QSpinBox(self)
        self.interval_spinbox.setRange(1, 3600) # Allow  limit betqween 1-3600 secs
        self.interval_spinbox.setValue(120) # Set default value to 2 mins
        interval_layout.addWidget(self.interval_spinbox)
        main_layout.addLayout(interval_layout)

        # Start button layout
        button_layout = QHBoxLayout()
        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_clicking)
        button_layout.addWidget(self.start_button)

        # Stop button layout
        self.stop_button = QPushButton('Stop', self)
        self.stop_button.clicked.connect(self.stop_clicking)
        self.stop_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.stop_button)

        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def start_clicking(self):
        # Starting clicker thread
        if not self.clicker_thread:
            interval = self.interval_spinbox.value()
            self.clicker_thread = ClickerThread(interval)
            self.clicker_thread.update_signal.connect(self.update_status)
            self.clicker_thread.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            message = 'Hi, I am SQIX and I am ready to help you play hooky'
            print(message)  # Print to terminal
            self.status_label.setText(message)

    def stop_clicking(self):
        if self.clicker_thread:
            self.clicker_thread.stop()
            self.clicker_thread.wait()
            self.clicker_thread = None
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            message = 'SQIX is tired'
            print(message)  # Print to terminal
            self.status_label.setText(message)

    def update_status(self, message):
        # Update status label
        self.status_label.setText(message)
        print(f"Status update: {message}")  # Debug print

    def closeEvent(self, event):
        # Handle cleanupo on appclose
        if self.clicker_thread:
            self.clicker_thread.stop()
            self.clicker_thread.wait()
        print("SQIX is leaving")  # Print to terminal when closing
        event.accept()

# Main -  Entry point of the app
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AutoClickerApp()
    ex.show()
    sys.exit(app.exec_())
