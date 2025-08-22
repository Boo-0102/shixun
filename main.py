import os
import sys
from datetime import datetime

import cv2
import numpy as np
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import (QApplication, QDialog, QDialogButtonBox,
                             QFormLayout, QFrame, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTextEdit, QVBoxLayout,
                             QWidget)

from communication import TCPServerThread
from detect import detect_multiple_objects

# # TCP通讯设置
# HOST = '192.168.1.100'
# PORT = 2000



class TcpConfigDialog(QDialog):
    def __init__(self, parent=None, default_host='192.168.1.100', default_port=2000):
        super().__init__(parent)
        self.setWindowTitle("TCP 设置")
        self.setFixedSize(300, 120)

        layout = QFormLayout()

        self.ip_edit = QLineEdit(default_host)
        self.port_edit = QLineEdit(str(default_port))
        layout.addRow("IP 地址：", self.ip_edit)
        layout.addRow("端口号：", self.port_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.setLayout(layout)

    def get_config(self):
        return self.ip_edit.text(), int(self.port_edit.text())

# 视频流进程
class VideoThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)
    log_signal = pyqtSignal(str)

    def __init__(self, cam_id=1):
        super().__init__()
        self.cam_id = cam_id
        self.running = True
        self._latest_frame = None  

    def run(self):
        cap = cv2.VideoCapture(self.cam_id)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2592)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1944)
        cap.set(cv2.CAP_PROP_FPS, 10)

        if not cap.isOpened():
            print("摄像头打开失败")
            return

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue
            # frame_resized = cv2.resize(frame, (640, 512))
            self._latest_frame = frame.copy()  # 缓存当前帧
            self.frame_ready.emit(frame)

        cap.release()

    def get_current_frame(self):
        return self._latest_frame.copy() if self._latest_frame is not None else None

    def stop(self):
        self.running = False
        self.wait()



class MyApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("数字孪生智能控制系统")
        self.setGeometry(100, 100, 1000, 600)
        self.tcp_thread = None
        self.init_ui()
        self.workpiece_info_list = []

        # 启动摄像头线程
        self.video_thread = VideoThread(cam_id=1)
        self.video_thread.frame_ready.connect(self.display_frame)
        self.video_thread.log_signal.connect(self.workpiece_box.append)
        self.video_thread.start()

        # 目前模式
        self.current_display_mode = 'video' # 默认显示视频
        # tcp 配置
        self.tcp_host = '192.168.1.100'
        self.tcp_port = 2000

        # 初始化定时器，单次触发
        self.photo_display_timer = QTimer(self)
        self.photo_display_timer.setSingleShot(True)
        self.photo_display_timer.timeout.connect(self.switch_to_video_mode)

    def init_ui(self):
        # 主布局：横向
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

           # 设置整体背景色
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f4f8;
            }
            QTextEdit, QLineEdit {
                background-color: #ffffff;
                border: 1px solid #b0bec5;
                border-radius: 6px;
                font-size: 15px;
            }
            QPushButton {
                background-color: #1976d2;
                color: #fff;
                border-radius: 8px;
                padding: 8px 18px;
                font-weight: bold;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QLabel#logo_label {
                background: transparent;
            }
            QLabel#pattern_label {
                background: transparent;
            }
        """)


        # 左侧：功能区
        left_panel = QVBoxLayout()

        # 校徽图片
        self.logo_label = QLabel()
        pixmap = QPixmap("assets/logo.png").scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.logo_label.setPixmap(pixmap)
        self.logo_label.setAlignment(Qt.AlignCenter)

       
        # 功能按钮
        self.connect_btn = QPushButton("连接 TCP")
        self.connect_btn.clicked.connect(self.handle_connect)
        self.capture_btn = QPushButton("拍照识别")
        self.capture_btn.clicked.connect(self.capture_and_detect)
        self.tcp_config_btn = QPushButton("配置 TCP")
        self.tcp_config_btn.clicked.connect(self.open_tcp_config)

        
        # 通讯信息窗口
        self.info_box = QTextEdit()
        self.info_box.setReadOnly(True)
        self.info_box.setPlaceholderText("通信信息将在此显示...")

        # 工件信息窗口
        self.workpiece_box = QTextEdit()
        self.workpiece_box.setReadOnly(True)
        self.workpiece_box.setPlaceholderText("工件信息将在此显示...")

        # 添加到左侧布局
        left_panel.addWidget(self.logo_label)
        left_panel.addSpacing(20)  # 增加空隙

        tcp_button_layout = QHBoxLayout()
        tcp_button_layout.addWidget(self.connect_btn)
        tcp_button_layout.addWidget(self.tcp_config_btn)
        left_panel.addLayout(tcp_button_layout)



        left_panel.addWidget(self.capture_btn)
        left_panel.addWidget(self.info_box)
        left_panel.addWidget(self.workpiece_box)


        # 右侧：视频显示区域
        self.label = QLabel("画面显示区域")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFrameShape(QFrame.Box)
        self.label.setStyleSheet("""
            QLabel {
                background-color: #e3eaf2;
                border: 2px solid #90caf9;
                font-size: 22px;
                color: #1976d2;
            }
        """)

        # 加入主布局
        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addWidget(self.label, stretch=2)

    def open_tcp_config(self):
        dialog = TcpConfigDialog(self, self.tcp_host, self.tcp_port)
        if dialog.exec_() == QDialog.Accepted:
            self.tcp_host, self.tcp_port = dialog.get_config()
            self.info_box.append(f"[系统] TCP 设置更新为 {self.tcp_host}:{self.tcp_port}")
        else:
            self.info_box.append("[系统] 已取消 TCP 设置")


    def handle_connect(self):
            if self.tcp_thread is None:
                self.tcp_thread = TCPServerThread(workpiece_info_list=self.workpiece_info_list, host=self.tcp_host, port=self.tcp_port)
                self.tcp_thread.message_signal.connect(self.info_box.append)
                self.tcp_thread.start()
                self.info_box.append("[系统] TCP 服务已启动")
            else:
                self.info_box.append("[系统] TCP 服务已在运行")


    def capture_and_detect(self):
        frame = self.video_thread.get_current_frame()
        if frame is None:
            self.workpiece_box.append("[系统] 无法获取当前帧")
            return

        self.workpiece_box.append("[系统] 开始识别拍摄图像...")
        result , self.workpiece_info_list = detect_multiple_objects(frame, log_callback=self.workpiece_box.append)
        
        # ====保存图像====
        save_dir = "results"
        original_dir = os.path.join(save_dir, "original")
        detect_dir = os.path.join(save_dir, "detect")
        os.makedirs(original_dir, exist_ok=True)
        os.makedirs(detect_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 保存原图
        original_path = os.path.join(original_dir, f"{timestamp}.jpg")
        cv2.imwrite(original_path, frame)

        # 保存识别结果图
        result_path = os.path.join(detect_dir, f"{timestamp}.jpg")
        cv2.imwrite(result_path, result)

        self.display_image(result)
        self.workpiece_box.append(f"[系统] 识别图像已保存")
        self.workpiece_box.append("[系统] 识别完成")

        if self.tcp_thread is not None:
            self.tcp_thread.workpiece_info_list = self.workpiece_info_list
            self.tcp_thread.workpiece_index = 0  # 重置索引

        # 切换为“photo”模式，暂停视频显示
        self.current_display_mode = 'photo'
        # 启动定时器，3秒后恢复视频显示
        self.photo_display_timer.start(3000)
    

    def switch_to_video_mode(self):
        self.current_display_mode = 'video'


    def display_frame(self, frame):
        if self.current_display_mode == "video":
            self.display_image(frame)

    def display_image(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (640, 512))
        h, w, ch = rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(qt_image))
    
    
    def closeEvent(self, event):
        if self.tcp_thread:
            self.tcp_thread.stop()
        self.video_thread.stop()
        super().closeEvent(event)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())

