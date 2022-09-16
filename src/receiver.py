from os import PathLike
import socket
from PyQt6.QtCore import QThread, pyqtSignal, QSemaphore
from queue import Queue
import multiprocessing
import numpy as np
from all_in_one_preprocess import *
from WidgetsFunc import *
import glob
import os


class Receiver(QThread):
    tasks: Queue
    obsPath: PathLike
    avgPath: PathLike
    saveFileSignal = pyqtSignal(str)
    stopsig = pyqtSignal()
    unlockGanger = pyqtSignal()
    meanQ: multiprocessing.Queue
    signin: QSemaphore

    def __init__(self):
        super().__init__()
        self.udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpServer.settimeout(7)
        self.udpServer.bind(('127.0.0.1', 7219))
        self.stopFlag = False
        self.stopsig.connect(self.on_stop)

    def on_stop(self):
        self.stopFlag = True

    def run(self):
        prefile = None
        while True:
            try:
                data = self.udpServer.recvfrom(128)
            except:
                if self.stopFlag:
                    print('接收者可以下班')
                    if prefile:
                        self.saveFileSignal.emit(os.path.split(prefile)[1])
                        n = 9 - self.signin.available()
                        msaver = self.Msaver(n, False)
                        msaver.fname = os.path.split(prefile)[1]+'.txt'
                        msaver.dst = self.avgPath
                        msaver.meanQ = self.meanQ
                        msaver.start()
                        msaver.join()
                    self.unlockGanger.emit()
                    break
                else:
                    continue
            if data[0].decode('gbk') == 'w':
                allfiles = glob.glob(self.obsPath+'\\*.txt')
                allfiles.sort(key=lambda x: x[-19:], reverse=True)
                newest = allfiles[0]
                self.tasks.put(newest)
                if prefile and not newest.startswith(prefile):
                    # 不一样就发送信号让打工人存盘
                    n = 9 - self.signin.available()
                    msaver = self.Msaver(n, True)
                    msaver.fname = os.path.split(prefile)[1]+'.txt'
                    msaver.dst = self.avgPath
                    msaver.meanQ = self.meanQ
                    msaver.start()
                    self.saveFileSignal.emit(os.path.split(prefile)[1])

                prefile = newest[:-13]
                self.unlockGanger.emit()

    def __del__(self):
        self.udpServer.close()
        print('接收者退出')

    class Msaver(multiprocessing.Process):
        fname: str
        dst: str
        data: np.ndarray
        meanQ: multiprocessing.Queue

        def __init__(self, num: int, shouhu: bool):
            super().__init__(daemon=shouhu)
            self.n = num

        def run(self):

            datas = np.array([])
            for i in range(self.n):
                spec, pref = self.meanQ.get()
                if datas.size:
                    datas = np.vstack((datas, spec[1, :]))
                else:
                    datas = spec[1, :]
            if self.n > 1:
                spec[1, :] = np.mean(datas, axis=0)
            spec = specSplit(spec, 800, 1800)
            spec[1, :] = rp.smooth(spec[0, :], spec[1, :],  Lambda=500)
            spec[1, :] = norm_Area(spec[1, :])
            saveFile(self.fname, self.dst, pref, spec.transpose())

        def __del__(self):
            print('进程自己退出')
