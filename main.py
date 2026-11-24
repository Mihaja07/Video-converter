from PyQt5.QtWidgets import (QApplication, QWidget, QLineEdit, QLabel, QPushButton, QComboBox,
                             QHBoxLayout, QVBoxLayout, QProgressBar, QSpinBox, QCheckBox, QFileDialog)
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QIcon
from data import Data
import subprocess
import datetime
import sys
import re
import os


class Tool(QWidget):
    def __init__(self):
        super().__init__()
        self.initData()
        self.apply_style()
        self.resize(300, 400)
        self.spalsh_screen()
        self.setWindowTitle("Video converter")
        self.setWindowIcon(QIcon("images/icon.ico"))
    
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
        self.output_field.setToolTip(self.data.get('output'))
        self.output_field.setReadOnly(True)
        output_btn = QPushButton("Change")
        output_btn.clicked.connect(self.change_output)
        output_layout.addWidget(self.output_field)
        output_layout.addWidget(output_btn)

        quality_cbx = QSpinBox()
        quality_cbx.setRange(1, 51)
        quality_cbx.setValue(self.data.get('quality', 30))
        quality_cbx.setToolTip("Higher quality outputs smaller files\n28 good, 51 worst")
        quality_cbx.valueChanged.connect(lambda x: self.data.save('quality', x))
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
        self.status_lb = QLabel("fps: 0")
        self.reuse_settings_chb = QCheckBox("Use the same parameters for every videos")
        self.reuse_settings_chb.setChecked(self.data.get('reuse_parameters', True))
        self.reuse_settings_chb.clicked.connect(on_reuse_param_state_changed)
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.setToolTip("Start converting the video to mp4 with ffmpeg")
        self.convert_btn.clicked.connect(self.convert)

        layout.addWidget(QLabel("File:"))
        layout.addLayout(input_layout)
        layout.addWidget(QLabel("Quality:"))
        layout.addWidget(quality_cbx)
        layout.addWidget(QLabel("Resolution:"))
        layout.addWidget(self.keep_resolution_chb)
        layout.addWidget(self.resolution_cbx)
        layout.addWidget(QLabel("Output:"))
        layout.addLayout(output_layout)
        layout.addWidget(self.status_lb)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.reuse_settings_chb)
        layout.addWidget(self.convert_btn)
    
    def spalsh_screen(self):
        def checked(ffmpeg):
            self.timer.stop()
            QWidget().setLayout(self.layout())
            if not ffmpeg:
                layout = QVBoxLayout(self)
                label = QLabel("ffmpeg is not installed or not in PATH\n\nDownload it at https://ffmpeg.org/download.html")
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                button = QPushButton("OK")
                button.clicked.connect(self.close)
                layout.addWidget(label)
                layout.addWidget(button)
            else:
                self.initUI()
        
        def loading():
            if self.checking_label.text() == "Loading ...":
                self.checking_label.setText("Loading .")
                self.checking_label.show()
            elif self.checking_label.text() == "Loading ..":
                self.checking_label.setText("Loading ...")
            elif self.checking_label.text() == "Loading .":
                self.checking_label.setText("Loading ..")

        layout = QVBoxLayout(self)
        self.checking_label = QLabel("Loading ...")
        self.timer = QTimer()
        self.timer.timeout.connect(loading)
        self.timer.start(500)
        layout.addWidget(self.checking_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.show()

        self.checking_thread = QThread()
        self.checking_worker = CheckFFMPEG()
        self.checking_worker.moveToThread(self.checking_thread)
        self.checking_thread.started.connect(self.checking_worker.run)
        self.checking_worker.finished.connect(checked)
        self.checking_thread.start()

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
            self.input_field.setToolTip(self.get_path(files[0]))
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
            self.output_field.setToolTip(path)

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
                self.input_field.setText(f"{len(self.files_selected)+1} files remaining")
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
                self.input_field.setText(f"{len(self.files_selected)+1} files remaining")
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
    
    def closeEvent(self, a0):
        if self.converting:
            try:
                self.worker.kill()
            except ValueError:
                pass
        return super().closeEvent(a0)

    def apply_style(self):
        try:
            with open("style.qss", "r") as file:
                self.setStyleSheet(file.read())
        except:
            pass

class CheckFFMPEG(QObject):
    finished = pyqtSignal(bool)
    def __init__(self):
        super().__init__()
    
    def run(self):
        def check_encode(encode):
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=256x256:d=0.1", "-c:v", encode, "-f", "null", "-"]
            return subprocess.run(cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL).returncode == 0
        try:
            encode = ["h264_nvenc", "h264_qsv", "h264_amf", "libx264"]      #NVIDIA   INTEL   AMD   CPU
            cmd = [["-rc", "vbr", "-b:v", "0", "-cq"], ["-look_ahead", "1", "-global_quality"], ["-rc", "-qvbr", "-qvbr_quality_level"], ["-crf"]]       #Quality
            for i in encode:
                if check_encode(i):
                    Data().save("encode", i)
                    Data().save("quality_cmd", cmd[encode.index(i)])
                    break

            self.finished.emit(True)
        except FileNotFoundError:
            self.finished.emit(False)

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
        
        self.proc = subprocess.Popen(["ffmpeg", "-i", self.file, "-vf", "scale="+self.data.get('resolution').replace('x', ':'), "-c:v", Data().get("encode")]+self.data.get('quality_cmd')+[str(self.data.get('quality')), new_name], stderr=subprocess.PIPE, text=True, bufsize=1)
        
        while True:
            try:
                for line in self.proc.stderr:
                    time = re.search(r"time=\d\d:\d\d:\d\d.\d\d", line)
                    fps = re.search(r"fps=......", line)
                    if None not in (time, fps):
                        time = time.group(0)[5:13].strip()
                        self.progress_signal.emit(get_progress(time))
                        fps = fps.group(0)[4:fps.group(0).find('q')-1].strip()
                        self.info_signal.emit(f"fps: {fps}")
                break
            except UnicodeDecodeError:
                continue

        self.proc.wait()
        self.info_signal.emit(f"fps: 0")
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