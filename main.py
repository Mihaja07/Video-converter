from PyQt5.QtWidgets import (QApplication, QWidget, QLineEdit, QLabel, QPushButton, QComboBox,
                             QHBoxLayout, QVBoxLayout, QProgressBar, QSpinBox, QCheckBox)
from data import Data
import sys
import os


class Tool(QWidget):
    def __init__(self):
        super().__init__()
        self.initData()
        self.initUI()
        self.show()
    
    def initData(self):
        self.data = Data()
        self.data.get('input', os.path.join('C:/Users', os.getlogin(), 'Videos/').replace('\\', '/'))
        self.data.get('output', os.path.join('C:/Users', os.getlogin(), 'Videos/').replace('\\', '/'))
        self.files_selected = []
    
    def initUI(self):
        layout = QVBoxLayout(self)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setText("0 files selected")
        self.input_field.setReadOnly(True)
        input_btn = QPushButton("Open")
        input_btn.setToolTip("Select a video file")
        input_btn.clicked.connect(self.open)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(input_btn)

        output_layout = QHBoxLayout()
        self.output_field = QLineEdit()
        self.output_field.setText(self.data.get('output'))
        self.output_field.setReadOnly(True)
        output_btn = QPushButton("Change")
        output_btn.clicked.connect(self.change_output)
        output_layout.addWidget(self.output_field)
        output_layout.addWidget(output_btn)

        compression_cbx = QSpinBox()
        compression_cbx.setRange(10, 40)
        compression_cbx.setValue(self.data.get('compression', 28))
        compression_cbx.setToolTip("The higher the compression, the smaller the file")
        compression_cbx.valueChanged.connect(lambda x: self.data.save('compression', x))
        self.resolution_cbx = QComboBox()
        self.resolution_opt = ["1920x1080", "1366x768", "1280x720", "960x540", "850x480", "640x360"]
        self.resolution_cbx.addItems(self.resolution_opt)
        self.resolution_cbx.setCurrentText(self.data.get('resolution', '1280x720'))
        self.resolution_cbx.currentTextChanged.connect(lambda x: self.data.save('resolution', x))
        self.resolution_cbx.setToolTip("Resolution of the video")
        self.resolution_cbx.setDisabled(self.data.get('keep_resolution', False))
        self.keep_resolution_chb = QCheckBox("Keep resolution")
        self.keep_resolution_chb.setChecked(self.data.get('keep_resolution', False))

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.status_lb = QLabel("fps: 0  cpu: 0.0%")
        self.reuse_settings_chb = QCheckBox("Use the same parameters for every videos")
        self.reuse_settings_chb.setChecked(self.data.get('reuse_parameters', True))
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setToolTip("Start converting the video to mp4 with ffmpeg")
        self.convert_btn.clicked.connect(self.convert)

        layout.addWidget(QLabel("File:"))
        layout.addLayout(input_layout)
        layout.addWidget(QLabel("Compression:"))
        layout.addWidget(compression_cbx)
        layout.addWidget(QLabel("resolution:"))
        layout.addWidget(self.keep_resolution_chb)
        layout.addWidget(self.resolution_cbx)
        layout.addWidget(QLabel("Output:"))
        layout.addLayout(output_layout)
        layout.addWidget(self.status_lb)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.reuse_settings_chb)
        layout.addWidget(self.convert_btn)

    def open(self):
        pass
    
    def change_output(self):
        pass

    def convert(self):
        pass

app = QApplication(sys.argv)
window = Tool()
window.show()
sys.exit(app.exec())