from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *
from PyQt6.QtCharts import *
import sys
import getpass
import queue
import os
from datetime import datetime
from WidgetsFunc import *
from worker import Worker
from ganger import Ganger
from receiver import Receiver
from all_in_one_preprocess import *
from ui_CollectorWindow import Ui_CollectorWindow
import multiprocessing
import socket

class MainWindow(Ui_CollectorWindow, QWidget):
    chageCharts = pyqtSignal()
    specEraser = pyqtSignal(int)
    changeSeries = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.obsPath: os.PathLike
        self.catPath = f'C:\\Users\\{getpass.getuser()}\\Desktop\\'\
            + f'Cated {datetime.now().strftime("%Y%m%d")}'
        self.predPath = f'C:\\Users\\{getpass.getuser()}\\Desktop\\'\
            + f'Pred {datetime.now().strftime("%Y%m%d")}'
        self.avgPath = f'C:\\Users\\{getpass.getuser()}\\Desktop\\'\
            + f'Avg {datetime.now().strftime("%Y%m%d")}'
        self.cAllChart = QChart()
        self.pAllChart = QChart()
        self.catedsView.setChart(self.cAllChart)
        self.predsView.setChart(self.pAllChart)
        self.chageCharts.connect(self.change_O_C_Charts)
        self.specEraser.connect(self.eraseSpec)
        self.changeSeries.connect(self.change_C_P_Series)
        self.cSeriesList = [QLineSeries() for i in range(9)]
        self.pSeriesList = [QLineSeries() for i in range(9)]

        self.pushButton_start.clicked.connect(self.startF)
        self.pushButton_del.clicked.connect(self.delF)
        self.btns = [self.pushButton_1, self.pushButton_2, self.pushButton_3,
                     self.pushButton_4, self.pushButton_5, self.pushButton_6,
                     self.pushButton_7, self.pushButton_8, self.pushButton_9]
        self.colorList = [QColor('#F44A4D'), QColor('#5E38E0'),
                          QColor('#DEA537'), QColor('#42FFF6'),
                          QColor('#9FFF40'),
                          QColor('#E04CF4'), QColor('#45FF78'),
                          QColor('#3A7FE0'), QColor('#DE723A')]
        self.originQueue = queue.Queue(1)
        self.catQueue = queue.Queue(1)
        self.catsQueue = queue.Queue(1)
        self.predQueue = queue.Queue(1)

        self.udpServer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udpServer.settimeout(7)
        self.udpServer.bind(('127.0.0.1', 7219))
        Receiver.udpServer = self.udpServer

    # 用信号改变上面两个视图
    def change_O_C_Charts(self):
        oChart = QChart()
        oSeries = array2Lseries(self.originQueue.get())
        oChart.addSeries(oSeries)
        oChart.legend().close()
        self.originView.setChart(oChart)
        cChart = QChart()
        cSeries = array2Lseries(self.catQueue.get())
        cChart.addSeries(cSeries)
        cChart.legend().close()
        self.catView.setChart(cChart)

    def change_C_P_Series(self, index):
        self.cSeriesList[index] = array2Lseries(self.catsQueue.get())
        self.cSeriesList[index].setColor(self.colorList[index])
        self.pSeriesList[index] = array2Lseries(self.predQueue.get())
        self.pSeriesList[index].setColor(self.colorList[index])
        self.cAllChart.addSeries(self.cSeriesList[index])
        self.cAllChart.createDefaultAxes()
        self.cAllChart.axes(Qt.Orientation.Horizontal)[0].setRange(700, 1900)
        self.cAllChart.axes(Qt.Orientation.Horizontal)[0].setTickCount(13)
        self.cAllChart.legend().close()
        self.pAllChart.addSeries(self.pSeriesList[index])
        self.pAllChart.createDefaultAxes()
        self.pAllChart.axes(Qt.Orientation.Horizontal)[0].setRange(800, 1800)
        self.pAllChart.axes(Qt.Orientation.Horizontal)[0].setTickCount(11)
        self.pAllChart.legend().close()

    def eraseSpec(self, index):

        self.originView.chart().removeAllSeries()
        self.catView.chart().removeAllSeries()
        self.cAllChart.removeSeries(self.cSeriesList[index])
        self.pAllChart.removeSeries(self.pSeriesList[index])

    def delF(self):
        for i in range(9):
            if self.btns[i].isChecked():
                self.workers[i].delsig.emit()
                self.btns[i].setChecked(False)

    def startF(self):

        self.obsPath = QFileDialog.getExistingDirectory(
            self, "选择监视路径", 'D:\\内窥镜 -20190612\\201906\\Data\\')
        if not self.obsPath:
            return
        self.pushButton_start.setDisabled(True)
        self.pushButton_stop.setEnabled(True)
        if not os.path.exists(self.catPath):
            os.makedirs(self.catPath)
        if not os.path.exists(self.predPath):
            os.makedirs(self.predPath)
        if not os.path.exists(self.avgPath):
            os.makedirs(self.avgPath)
        # 打开并创建文件夹，就不打开了

        post = QSemaphore(0)
        Worker.signin = post
        Ganger.signin = post
        Receiver.signin = post
        # 约束打卡个数

        outsource = queue.Queue(9)
        meanQueue = multiprocessing.Queue(9)
        Worker.meanQ = meanQueue
        Worker.tasks = outsource
        Worker.dst = self.catPath
        Worker.pdst = self.predPath
        Worker.obsPath = self.obsPath
        Worker.originQueue = self.originQueue
        Worker.catQueue = self.catQueue
        Worker.catsQueue = self.catsQueue
        Worker.predQueue = self.predQueue
        Receiver.tasks = outsource
        Receiver.obsPath = self.obsPath
        Receiver.avgPath = self.avgPath
        Receiver.meanQ = meanQueue
        # 关联工作发放队列
        keeprunning = True

        self.workers = [Worker(i) for i in range(9)]  # 9个打工人
        self.receiver = Receiver()
        self.ganger = Ganger()
        for worker in self.workers:
            worker.buttonEnable.connect(self.btns[worker.id].setEnabled)
            self.pushButton_stop.clicked.connect(worker.stopsig)
            self.receiver.saveFileSignal.connect(worker.savesig)
            worker.sendUpper.connect(self.chageCharts)
            worker.sendLower.connect(self.changeSeries)
            worker.deleteLower.connect(self.specEraser)
            worker.setTable.connect(
                lambda r, f: self.tableWidget.setItem(r, 0, QTableWidgetItem(f)))
            worker.finished.connect(worker.deleteLater)
            worker.start()
        self.receiver.unlockGanger.connect(self.ganger.sendsig)
        self.pushButton_stop.clicked.connect(self.receiver.stopsig)
        self.pushButton_stop.clicked.connect(self.ganger.stopsig)
        self.pushButton_stop.clicked.connect(
            lambda: self.pushButton_stop.setDisabled(True))
        self.pushButton_stop.clicked.connect(
            lambda: self.pushButton_start.setEnabled(True))
        self.receiver.start()
        self.ganger.start()

        # receiver.exec()
        # ganger.exec()
        # for worker in self.workers:
        #     worker.exec()

    def closeEvent(self, Event):
        try:
            folder_escort()
        except:
            print('移不动')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("./img/accessibility.ico"))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
