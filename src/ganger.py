from PyQt6.QtCore import QThread, QMutex, pyqtSignal, QSemaphore
from socket import socket, AF_INET, SOCK_DGRAM, timeout


# 工头类，已发现闲置打工人线程就发送采集请求
class Ganger(QThread):
    sendsig = pyqtSignal()
    signin: QSemaphore
    stopsig = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.__udpSender = socket(AF_INET, SOCK_DGRAM)
        self.__lock = QMutex()
        self.__lock.lock()
        self.stopFlag = False
        self.sendsig.connect(self.__lock.unlock)
        self.stopsig.connect(self.on_stop)

    def on_stop(self):
        self.stopFlag = True

    def run(self):
        while True:
            self.__lock.lock()
            if self.stopFlag:
                print('工头可以下班')
                break
            if self.signin.tryAcquire(1, 7):
                if self.stopFlag:
                    print('工头可以下班')
                    break
                else:
                    self.__udpSender.sendto(
                        'c'.encode('gbk'), ('127.0.0.1', 52169))

    def __del__(self):
        self.__udpSender.close()
        print('工头退出')
