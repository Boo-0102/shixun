from PyQt5.QtCore import QThread, pyqtSignal
import socket
import threading
from PyQt5.QtCore import QThread, pyqtSignal
import socket
import threading
import time 

class TCPServerThread(QThread):
    message_signal = pyqtSignal(str)

    def __init__(self, workpiece_info_list, host='192.168.1.100', port=2000, buffer_size=1024):
        super().__init__()
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.running = True

        # 工件信息列表
        self.workpiece_info_list = workpiece_info_list
        self.workpiece_index = 0

    def run(self):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind((self.host, self.port))
            server.listen(1)
            self.message_signal.emit(f"[监听] 等待来自 PLC 的连接 {self.host}:{self.port}...")

            while self.running:
                conn, addr = server.accept()
                self.message_signal.emit(f"[连接成功] 来自 {addr}")
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
        except Exception as e:
            self.message_signal.emit(f"[服务器错误] {e}")

    def handle_client(self, conn, addr):
        try:
            while self.running:
                data = conn.recv(self.buffer_size)
                if not data:
                    self.message_signal.emit(f"[断开连接] 来自 {addr}")
                    break

                ## 接受PLC发送的数据
                # msg = data.decode('utf-8').strip()
                msg = data.decode("ascii", errors="ignore")
                self.message_signal.emit(f"[接收] {msg} 从 {addr}")

                if "OK" in msg:
                    # 等待 workpiece_info_list 有内容或超时
                    self.message_signal.emit(f"[提示] 接收到OK,开始拍照识别！")
                    self.workpiece_index = 0 # 索引清零
                    
                    timeout = 4
                    waited = 0
                    while self.running and not self.workpiece_info_list and waited < timeout:
                        time.sleep(0.1)
                        waited += 0.1

                    self.message_signal.emit(f"[提示] 工件总数: {len(self.workpiece_info_list)}")
                    while self.workpiece_index < len(self.workpiece_info_list):
                        info = self.workpiece_info_list[self.workpiece_index]
                        try:
                            conn.sendall(info.encode('utf-8'))
                            self.message_signal.emit(f"[发送] {info}")
                        except Exception as e:
                            self.message_signal.emit(f"[发送错误] {e}")
                            break  # 出错就停止发送
                        self.workpiece_index += 1
                        time.sleep(1)  # 延迟一秒再发送下一个工件

                # if "OK" in msg:
                #     # 等待 workpiece_info_list 有内容或超时
                #     timeout = 4  # 最多等待 4 秒
                #     waited = 0
                #     while self.running and not self.workpiece_info_list and waited < timeout:
                #         time.sleep(0.1)
                #         waited += 0.1
                        
                #     self.message_signal.emit(f"[提示] 工件总数: {len(self.workpiece_info_list)}")

                #     if self.workpiece_index < len(self.workpiece_info_list):
                #         info = self.workpiece_info_list[self.workpiece_index]
                #         conn.sendall(info.encode('utf-8'))
                #         self.message_signal.emit(f"[发送] {info}")
                #         time.sleep(1)  # 1s发送一次
                #         self.workpiece_index += 1

        except Exception as e:
            self.message_signal.emit(f"[客户端异常] {e}")
        finally:
            conn.close()


    def stop(self):
        self.running = False
        self.quit()
        self.wait()

