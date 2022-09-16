from os import PathLike
import os.path
from PyQt6.QtWidgets import *
from PyQt6.QtCore import QThread, pyqtSignal, QMutexLocker, QMutex, QSemaphore, QMetaType
from queue import Queue
import numpy as np
import rampy as rp
from all_in_one_preprocess import *
from WidgetsFunc import *
import multiprocessing


class Worker(QThread):
    tasks: Queue
    savesig = pyqtSignal(str)
    delsig = pyqtSignal()
    signin: QSemaphore
    dst: PathLike
    pdst: PathLike
    obsPath: PathLike
    standup = pyqtSignal()
    sendUpper = pyqtSignal()
    sendLower = pyqtSignal(int)
    deleteLower = pyqtSignal(int)
    stopsig = pyqtSignal()
    setTable = pyqtSignal(int, str)
    buttonEnable = pyqtSignal(bool)
    originQueue: Queue
    catsQueue: Queue
    catQueue: Queue
    predQueue: Queue
    plotLock = QMutex()
    meanQ: multiprocessing.Queue

    def __init__(self, id):
        super().__init__()
        self.id = id
        self.savesig.connect(self.on_save)
        self.filename: str
        self.loaded = False
        self.catedSpec: np.ndarray
        self.predSpec: np.ndarray
        self.mutex = QMutex()
        self.chair = QMutex()
        self.chair.lock()  # 初始锁上，线程才能休息
        self.standup.connect(self.on_standup)
        self.delsig.connect(self.on_del)
        self.savesig.connect(self.on_save)
        self.stopsig.connect(self.on_stop)
        self.stopFlag = False
        self.pref: list[str]

    def on_standup(self):
        self.catedSpec = None
        self.loaded = False
        self.chair.unlock()

    def on_save(self, savegroup):
        with QMutexLocker(self.mutex):
            if self.loaded and self.filename.startswith(savegroup):
                saveFile(self.filename, self.dst, self.pref, self.catedSpec)
                saveFile(self.filename, self.pdst, self.pref, self.predSpec)
                roil = np.array([[i, i+500] for i in range(0, 4000, 500)])
                spec = self.catedSpec.copy().transpose()
                spec[1, :] = rp.baseline(spec[0, :], spec[1, :], roil, 'drPLS',
                                         lam=9.7e7, ratio=0.00047)[0].reshape(-1,)
                self.meanQ.put((spec, self.pref))
                self.deleteLower.emit(self.id)
                self.setTable.emit(self.id, '')
                self.standup.emit()

    def on_del(self):
        # 删除图像所需的代码
        self.deleteLower.emit(self.id)
        self.setTable.emit(self.id, '')
        if os.path.exists(self.obsPath+'/'+self.filename):
            os.remove(self.obsPath+'/'+self.filename)
        self.standup.emit()

    def on_stop(self):
        self.stopFlag = True

    def run(self):
        noTimeout = True
        while True:
            if noTimeout:
                self.signin.release()  # 打卡上班
            noTimeout = True
            try:
                targetFile = self.tasks.get(timeout=20)
            except:
                # 20秒没收到的话就解锁查看重来一次
                if self.stopFlag:
                    print(str(self.id)+"号工人恶意不加班")
                    break
                else:
                    noTimeout = False
                    continue
            with QMutexLocker(self.mutex):
                self.loaded = True
                self.filename = os.path.split(targetFile)[1]
                originSpec = np.loadtxt(targetFile, skiprows=3)
                with open(targetFile, 'r') as f:
                    self.pref = [f.readline(), f.readline()]
                spec = np.delete(originSpec.transpose(), 1002, axis=1)
                spec[1, :] = cat_spec(spec[1, :], [1002, 1960])
                self.catedSpec = spec.copy().transpose()

                with QMutexLocker(self.plotLock):
                    self.originQueue.put(originSpec)
                    self.catQueue.put(self.catedSpec)
                    self.sendUpper.emit()
                self.catsQueue.put(self.catedSpec)

                roil = np.array([[i, i+500] for i in range(0, 4000, 500)])
                spec[1, :] = rp.baseline(spec[0, :], spec[1, :], roil, 'drPLS',
                                         lam=9.7e7, ratio=0.0047)[0].reshape(-1,)
                spec = specSplit(spec, 800, 1800)
                spec[1, :] = rp.smooth(spec[0, :], spec[1, :], Lambda=500)
                spec[1, :] = norm_Area(spec[1, :])
                self.predSpec = spec.copy().transpose()

                # 发送两个Series的信号
                self.predQueue.put(self.predSpec)
                self.sendLower.emit(self.id)
                self.setTable.emit(self.id, self.filename)
                self.buttonEnable.emit(True)

            self.chair.lock()
            self.buttonEnable.emit(False)

    def __del__(self):
        print(str(self.id)+"号工人下班")
