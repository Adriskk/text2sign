import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
)
from PyQt5.QtMultimedia import QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtMultimedia import QMediaContent
from PyQt5.QtCore import QUrl


class MainWindow(QWidget):
    def __init__(self, on_button_click):
        super().__init__()
        self.init_ui()
        self.on_button_click = on_button_click
        self.is_loading = False
        self.previous_video_src = None

    def init_ui(self):
        self.setWindowTitle("text2sign")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()
        self.label = QLabel("Enter a sentence:")
        layout.addWidget(self.label)

        self.input_field = QLineEdit(self)
        layout.addWidget(self.input_field)

        self.generate_button = QPushButton("Generate", self)
        self.generate_button.clicked.connect(self.on_generate_clicked)
        layout.addWidget(self.generate_button)

        self.repeat_button = QPushButton("Repeat", self)
        self.repeat_button.clicked.connect(self.on_repeat_clicked)
        self.repeat_button.setEnabled(False)
        layout.addWidget(self.repeat_button)

        self.video_widget = QVideoWidget(self)
        self.video_widget.setMinimumSize(480, 270)
        layout.addWidget(self.video_widget)

        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        self.setLayout(layout)

    def on_generate_clicked(self):
        sentence = self.input_field.text().strip().upper().replace(',', '').replace('.', '').replace('?', '').replace('!', '')
        self.is_loading = True
        self.generate_button.setText("Generating...")
        video_src = self.on_button_click(sentence)

        if video_src:
            video_src = os.path.abspath(video_src)
            self.previous_video_src = video_src
            self.play_video(video_src)
            self.repeat_button.setEnabled(True)
        else:
            self.label.setText("No video found for the input sentence")

        self.generate_button.setText("Generate")
        self.is_loading = False

    def on_repeat_clicked(self):
        if self.previous_video_src: self.play_video(self.previous_video_src)

    def play_video(self, video_src):
        video_url = QUrl.fromLocalFile(video_src)
        self.media_player.setMedia(QMediaContent(video_url))
        self.media_player.play()


def open_window(on_generate):
    app = QApplication(sys.argv)
    window = MainWindow(on_generate)
    window.show()
    sys.exit(app.exec_())
