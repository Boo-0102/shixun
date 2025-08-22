import sys
import cv2
import numpy as np
import time
import os
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSlider, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap


class HSVFilterApp(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Get HSV")
        self.image = cv2.imread(image_path)
        if self.image is None:
            raise ValueError("无法加载图像: " + image_path)

        # Resize to consistent width
        self.image = cv2.resize(self.image, (640, int(self.image.shape[0] * 640 / self.image.shape[1])))
        self.hsv_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)

        self.h_min, self.h_max = 0, 179
        self.s_min, self.s_max = 0, 255
        self.v_min, self.v_max = 0, 255

        self.init_ui()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_result)
        self.timer.start(30)

    def init_ui(self):
        layout = QVBoxLayout()

        self.image_label = QLabel()
        layout.addWidget(self.image_label)

        sliders_layout = QGridLayout()
        self.sliders = {}

        def add_slider(name, row, max_value, init_value):
            label = QLabel(name)
            slider = QSlider(Qt.Horizontal)
            slider.setMaximum(max_value)
            slider.setValue(init_value)
            slider.valueChanged.connect(self.slider_changed)
            self.sliders[name] = slider
            sliders_layout.addWidget(label, row, 0)
            sliders_layout.addWidget(slider, row, 1)

        add_slider("H Min", 0, 179, 0)
        add_slider("H Max", 1, 179, 179)
        add_slider("S Min", 2, 255, 0)
        add_slider("S Max", 3, 255, 255)
        add_slider("V Min", 4, 255, 0)
        add_slider("V Max", 5, 255, 255)

        layout.addLayout(sliders_layout)
        self.setLayout(layout)

    def slider_changed(self):
        self.h_min = self.sliders["H Min"].value()
        self.h_max = self.sliders["H Max"].value()
        self.s_min = self.sliders["S Min"].value()
        self.s_max = self.sliders["S Max"].value()
        self.v_min = self.sliders["V Min"].value()
        self.v_max = self.sliders["V Max"].value()

    def update_result(self):
        lower = np.array([self.h_min, self.s_min, self.v_min])
        upper = np.array([self.h_max, self.s_max, self.v_max])
        mask = cv2.inRange(self.hsv_image, lower, upper)
        result = cv2.bitwise_and(self.image, self.image, mask=mask)
        combined = np.hstack((self.image, result))

        qimage = self.convert_cv_to_qimage(combined)
        self.image_label.setPixmap(QPixmap.fromImage(qimage))

    @staticmethod
    def convert_cv_to_qimage(cv_img):
        height, width, channel = cv_img.shape
        bytes_per_line = 3 * width
        q_img = QImage(cv_img.data, width, height, bytes_per_line, QImage.Format_BGR888)
        return q_img

    def closeEvent(self, event):
        print("\n当前 HSV 参数为：")
        print(f"([{self.h_min}, {self.s_min}, {self.v_min}],[{self.h_max}, {self.s_max}, {self.v_max}])")
        event.accept()


def auto_capture_and_run():
    save_dir = "assets/debug_for_angel"
    os.makedirs(save_dir, exist_ok=True)

    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2592)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1944)
    cap.set(cv2.CAP_PROP_FPS, 10)

    if not cap.isOpened():
        print("[错误] 无法打开摄像头")
        sys.exit()

    print("[提示] 按 'c' 拍照并进入 HSV 调节，按 'q' 退出程序")

    filename = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[错误] 无法读取摄像头画面")
            break
        resized = cv2.resize(frame, (640, 512))
        cv2.imshow("Camera", resized)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_dir, f"capture_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            print(f"[保存成功] {filename}")
            break
        elif key == ord('q'):
            print("[退出] 用户中止")
            cap.release()
            cv2.destroyAllWindows()
            sys.exit()

    cap.release()
    cv2.destroyAllWindows()
    return filename


if __name__ == '__main__':
    app = QApplication(sys.argv)
    image_path = auto_capture_and_run()
    if image_path:
        window = HSVFilterApp(image_path)
        window.show()
        sys.exit(app.exec_())


    # app = QApplication(sys.argv)
    # window = HSVFilterApp("assets\img_angel_0\capture_20250603_212810.jpg")
    # window.show()
    # sys.exit(app.exec_())