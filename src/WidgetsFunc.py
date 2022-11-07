import getpass
import numpy as np
import os
import time
from datetime import datetime
import glob
import shutil
from PyQt6.QtCore import QPointF
from PyQt6.QtWidgets import QApplication, QInputDialog
from PyQt6.QtCharts import QLineSeries
import sys
import fnmatch
import os


def saveFile(filename: str, path: str, prefix: list[str], spec: np.ndarray):
    dst = path+'/'+filename
    np.savetxt(dst, spec, fmt=['%.3f', '%f'], delimiter='\t',
               header=prefix[0]+prefix[1], encoding='utf', comments='')


def array2Lseries(spec: np.ndarray) -> QLineSeries:
    series = QLineSeries()
    series.append([QPointF(x, y)for x, y in spec])
    return series


def locate_organ(fname):
    stomach_key = {'*胃*', '*窦*', '*幽门*', '*ATP*',
                   '*移行部*', '*体大*', '*体小*', '*移行部*', '*角切迹*'}
    oesophagus_key = {'*食*', '*贲门*'}
    colon_key = {'*结肠*', '*曲*', '*乙状*', '*脾区*', '*交界*', '*肠息肉*'}
    rectum_key = {'*直肠*'}
    caecum_key = {'*盲肠*'}
    for keyword in stomach_key:
        if fnmatch.fnmatch(fname, keyword):
            return '胃'
    for keyword in oesophagus_key:
        if fnmatch.fnmatch(fname, keyword):
            return '食道'
    for keyword in colon_key:
        if fnmatch.fnmatch(fname, keyword):
            return '结肠'
    for keyword in rectum_key:
        if fnmatch.fnmatch(fname, keyword):
            return '直肠'
    for keyword in caecum_key:
        if fnmatch.fnmatch(fname, keyword):
            return '盲肠'
    return '不匹配'


def distinguish_stomach(fname):
    if fnmatch.fnmatch(fname, '*窦*'):
        return '胃窦'
    elif fnmatch.fnmatch(fname, '*ATP'):
        return '胃窦'
    elif fnmatch.fnmatch(fname, '*体*'):
        return '胃体'
    elif fnmatch.fnmatch(fname, '*胃底*'):
        return '胃体'
    elif fnmatch.fnmatch(fname, '*胃息肉*'):
        return '胃体'
    elif fnmatch.fnmatch(fname, '*角切迹*'):
        return '角切迹'
    elif fnmatch.fnmatch(fname, '*移行部*'):
        return '胃体'
    elif fnmatch.fnmatch(fname, '*幽门*'):
        return '胃窦'
    else:
        return '其他'


def parse_filename(fname):
    # 定义一个解析文件名的函数吧
    suipian = fname.split()
    for duan in suipian:
        if fnmatch.fnmatch(duan, '*-*-*'):
            continue
        elif duan == time.strftime('%Y%m%d'):
            continue
        elif fnmatch.fnmatchcase(duan, '[A-Z]*[1-9]'):
            continue
        return duan


def folder_escort():
    username = getpass.getuser()
    os.chdir('C:/Users/%s/Desktop' % username)
    xingqi = datetime.isoweekday(datetime.today())
    rawPath = "D:/内窥镜 -20190612/201906/Data"
    donePath = "D:/内镜光谱数据（预处理后）"
    newPath = time.strftime('%Y%m%d')
    # if not os.path.exists('./Pred'):
    # pass
    # 自己的数据自己保存
    arbitraryPath = '橙一 %s' % (time.strftime('%Y%m%d'))
    if glob.glob('%s/*狭缝开*' % (rawPath)):
        os.mkdir(arbitraryPath)
        os.mkdir('%s/origin' % (arbitraryPath))
        for file in glob.glob('%s/*狭缝开*' % rawPath):
            shutil.move(file, '%s/origin' % arbitraryPath)
        shutil.move(glob.glob('./Mean*/*狭缝开*')[0], arbitraryPath)
        for file in glob.glob('./Cated*/*狭缝*'):
            os.remove(file)

    if xingqi % 2 == 1:
        secondPath = "活检标本"
    else:
        # 这个应该可以改成自动化获取的
        buwei = parse_filename(os.path.split(
            glob.glob('./Cated*/*.txt')[-1])[1])
        qiguan = locate_organ(buwei)
        if qiguan == '不匹配':

            secondPath = f"手术标本/{QInputDialog.getText(None,'请输入具体器官部位','肠胃')[0]}"
        else:
            secondPath = "手术标本/%s" % qiguan
        if qiguan != buwei:
            newPath += ' '+buwei

    raw_destination = "%s/%s/%s" % (rawPath, secondPath, newPath)
    done_destination = "%s/%s/%s" % (donePath, secondPath, newPath)
    if not os.path.exists(raw_destination):
        os.mkdir(raw_destination)
    if not os.path.exists(done_destination):
        os.mkdir(done_destination)

    # 采集的数据分类保存
    for file in glob.glob('%s/*.txt' % (rawPath)):
        shutil.move(file, raw_destination)
    shutil.move('./Cated %s' % (time.strftime('%Y%m%d')),
                '%s/拼接后' % (done_destination))
    shutil.move('./Pred %s' % (time.strftime('%Y%m%d')),
                '%s/单独处理dr' % (done_destination))
    shutil.move('./Avg %s' % (time.strftime('%Y%m%d')),
                '%s/平均后dr' % (done_destination))
    shutil.move('./Rough %s' % (time.strftime('%Y%m%d')),
                '%s/未平滑dr' % (done_destination))


    # 做大标本移动图片
    if xingqi % 2 == 0:
        pics = os.listdir("C:/Users/%s/Pictures" % username)
        os.chdir("C:/Users/%s/Pictures" % username)
        for file in pics:
            try:
                if fnmatch.fnmatch(file, '*.psd'):
                    shutil.move(file, done_destination)
                elif fnmatch.fnmatch(file, '*.jpg'):
                    shutil.move(file, done_destination)
                elif fnmatch.fnmatch(file, 'IMG*.png'):
                    shutil.move(file, done_destination)
            except:
                print(file)
                shutil.copy(file, done_destination)
                os.startfile("C:/Users/%s/Pictures" % username)

    os.startfile(done_destination)
    os.startfile(raw_destination)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # a = QFileDialog.getExistingDirectory(None, "请选择文件夹路径", "D:\\")
    a = QInputDialog.getText(None, "请输入具体器官部位", '肠胃')[0]
    print(a)
