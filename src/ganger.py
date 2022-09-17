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
        while not self.stopFlag:
            if not self.__lock.tryLock(7):
                continue
            if self.signin.tryAcquire(1, 7):
                self.__udpSender.sendto(
                    'c'.encode('gbk'), ('127.0.0.1', 52169))
        return

    def __del__(self):
        self.__lock.unlock()
        self.__udpSender.close()
        print('工头跑路')
