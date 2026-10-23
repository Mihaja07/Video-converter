from PyQt5.QtWidgets import (QApplication, QWidget, QLineEdit, QLabel, QPushButton, QComboBox,
                             QHBoxLayout, QVBoxLayout, QProgressBar, QSpinBox, QCheckBox, QFileDialog)
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from data import Data
import subprocess
import datetime
import psutil
import sys
import re
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
        self.converting = False
    
    def initUI(self):
        def on_keep_res_state_changed(state):
            self.resolution_cbx.setDisabled(bool(state))
            self.data.save('keep_resolution', bool(state))
        def on_reuse_param_state_changed(state):
            self.data.save('reuse_parameters', state)
            if self.files_selected:
                filename = self.files_selected[0][self.files_selected[0].rfind('/')+1:self.files_selected[0].rfind('.')]
                if len(filename) > 16:
                    filename = "..."+filename[-15:].strip()
                if state:
                    self.convert_btn.setText('Convert   all')
                else:
                    self.convert_btn.setText('Convert   "'+filename+'"')
                self.convert_btn.setToolTip(self.files_selected[0])

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
        self.keep_resolution_chb.stateChanged.connect(on_keep_res_state_changed)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.status_lb = QLabel("fps: 0  cpu: 0.0%")
        self.reuse_settings_chb = QCheckBox("Use the same parameters for every videos")
        self.reuse_settings_chb.setChecked(self.data.get('reuse_parameters', True))
        self.reuse_settings_chb.clicked.connect(on_reuse_param_state_changed)
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
    
    def set_resolution_duration(self, file):
        resolution, self.duration = self.get_info(file)
        if resolution not in self.resolution_opt:
            self.resolution_cbx.addItem(resolution)
        self.resolution_cbx.setCurrentText(resolution)

    def open(self):
        files = QFileDialog.getOpenFileNames(self, "Open files", self.data.get('input'), """Video files (*.mp4;*.avi;*.mkv;*.3gp)""")[0]
        if files:
            self.data.save('input', self.get_path(files[0]))
            self.data.save('output', self.get_path(files[0]))
            self.output_field.setText(self.get_path(files[0]))
            self.input_field.setText(f"{len(files)} files selected")
            self.files_selected = files
            self.set_resolution_duration(files[0])
            filename = files[0][files[0].rfind('/')+1:files[0].rfind('.')]
            if len(filename) > 16:
                filename = "..."+filename[-15:].strip()
            if self.reuse_settings_chb.isChecked():
                self.convert_btn.setText('Convert   all')
            else:
                self.convert_btn.setText('Convert   "'+filename+'"')
            self.convert_btn.setToolTip(files[0])
        else:
            self.files_selected = []
            self.input_field.setText("0 files selected")
    
    def get_info(self, file:str):
        """Return (resolution, duration)"""
        info = subprocess.run(['ffmpeg', '-i', file], capture_output=True)
        for pattern in [r"\d\d\d\dx\d\d\d\d", r"\d\d\dx\d\d\d\d", r"\d\d\d\dx\d\d\d", r"\d\d\dx\d\d\d"]:
            resolution = re.search(pattern, str(info.stderr))
            if resolution:
                resolution = resolution.group(0).strip()
                break

        duration = re.search(r"Duration: \d\d:\d\d:\d\d.\d\d", str(info.stderr))
        if duration is not None:
            duration = duration.group(0)[10:18].strip()

        return (resolution, duration)

    def get_path(self, file:str):
        file = file.replace('\\', '/')
        path = file[:file.rfind('/')]
        return path
    
    def change_output(self):
        path = QFileDialog.getExistingDirectory(self, "Change output", self.data.get('output'))
        if path:
            self.data.save('output', path)
            self.output_field.setText(path)

    def convert(self):
        def finished():
            self.convert_btn.setEnabled(1)
            self.convert_btn.setText("Convert")
            self.convert_thread.started.disconnect()
            self.worker.progress_signal.disconnect()
            self.worker.info_signal.disconnect()
            self.worker.finished_signal.disconnect()
            self.worker.deleteLater()
            self.convert_thread.quit()
            if not self.convert_thread.wait(250):
                self.convert_thread.terminate()
                self.convert_thread.wait()
            self.convert_thread.deleteLater()
            self.convert()

        def change_convert_btn(file:str):
            filename = file[file.rfind('/')+1:file.rfind('.')]
            if len(filename) > 16:
                filename = "..."+filename[-15:].strip()
            self.convert_btn.setText('Convert   "'+filename+'"')
            self.convert_btn.setToolTip(file)
        
        try:
            if self.converting:
                self.input_field.setText(f"{len(self.files_selected)} files remaining")
                file = self.files_selected[0]
                change_convert_btn(file)
                if self.keep_resolution_chb.isChecked():
                    self.set_resolution_duration(file)
                if self.reuse_settings_chb.isChecked():
                    self.files_selected.pop(0)
                    self.converting = True
                else:
                    self.converting = False
                    return 0
            else:
                file = self.files_selected.pop(0)
                self.input_field.setText(f"{len(self.files_selected)} files remaining")
                self.converting = True
        except IndexError:
            self.input_field.setText("0 files selected")
            self.convert_btn.setText("Convert")
            self.convert_btn.setToolTip("Start converting the video to mp4 with ffmpeg")
            self.files_selected = []
            self.converting = False
            return 0
        self.convert_btn.setText("Converting...")
        self.convert_btn.setDisabled(1)
        self.convert_thread = QThread()
        self.worker = ConvertWorker(file, self.duration)
        self.worker.moveToThread(self.convert_thread)

        self.worker.progress_signal.connect(self.progress_bar.setValue)
        self.worker.info_signal.connect(self.status_lb.setText)
        self.worker.finished_signal.connect(finished)
        self.convert_thread.started.connect(self.worker.run)

        self.convert_thread.start()


class ConvertWorker(QObject):
    progress_signal = pyqtSignal(int)
    info_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, file:str, duration:str):
        super().__init__()
        self.data = Data()
        self.file = file
        self.duration = duration
    
    def kill(self):
        self.proc.kill()
    
    def run(self):
        def get_progress(time):

            time_fmt = "%H:%M:%S"
            current = datetime.datetime.strptime(time, time_fmt) - datetime.datetime.strptime('00:00:00', time_fmt)
            total = datetime.datetime.strptime(self.duration, time_fmt) - datetime.datetime.strptime('00:00:00', time_fmt)
            
            return remap(current.total_seconds(), 0, total.total_seconds())

        new_name = self.data.get('output') + self.file[self.file.rfind('/'):self.file.rfind('.')] + "_converted" + ".mp4"
        if os.path.isfile(new_name):
            i = 0
            while os.path.isfile(self.data.get('output') + self.file[self.file.rfind('/'):self.file.rfind('.')] + f"_converted-{i}" + ".mp4"):
                i += 1
            new_name = self.data.get('output') + self.file[self.file.rfind('/'):self.file.rfind('.')] + f"_converted-{i}" + ".mp4"
        
        self.proc = subprocess.Popen(["ffmpeg", "-i", self.file, "-vf", "scale="+self.data.get('resolution').replace('x', ':'), "-vcodec", "libx264", "-crf", str(self.data.get('compression')), new_name], stderr=subprocess.PIPE, text=True, bufsize=1)
        
        for line in self.proc.stderr:
            time = re.search(r"time=\d\d:\d\d:\d\d.\d\d", line)
            fps = re.search(r"fps=......", line)
            if None not in (time, fps):
                time = time.group(0)[5:13].strip()
                self.progress_signal.emit(get_progress(time))
                fps = fps.group(0)[4:fps.group(0).find('q')-1].strip()
                cpu = psutil.cpu_percent()
                self.info_signal.emit(f"fps: {fps}  cpu:{cpu}%")
        self.proc.wait()
        self.info_signal.emit(f"fps: 0  cpu: 0.0%")
        self.finished_signal.emit()
        self.progress_signal.emit(0)

def remap(value, fromMin, fromMax, toMin=0, toMax=100):
    """Remap a value, used for the progress bar"""
    try:
        oldRange = fromMax - fromMin
        newRange = toMax - toMin
        ratio = (value-fromMin) / oldRange
        return int(toMin + (ratio*newRange))
    except:
        return toMax

app = QApplication(sys.argv)
window = Tool()
window.show()
sys.exit(app.exec())