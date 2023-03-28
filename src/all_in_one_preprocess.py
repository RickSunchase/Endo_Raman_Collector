from math import sqrt
import pylab
from glob import glob
from fnmatch import fnmatch
import rampy as rp
import numpy as np
import numpy.random as nr
import time
import os
import pathlib
from scipy.linalg import cholesky
from threading import Thread
from functools import reduce
from scipy import sparse
from filterpy.kalman import KalmanFilter


def find_origin(file):
    # 找到每个文件对应的原始文件的地址
    nyr, sfm = os.path.splitext(os.path.split(file)[1])[0].split(' ')[-2:]
    origin_file_path = 'd:\\内窥镜 -20190612\\201906\\Data\\'
    origin_file = glob(
        f"{origin_file_path}**\\*{nyr} {sfm}.txt", recursive=True)
    return origin_file[0]


def cosrad_eli(spec: np.ndarray):
    # 去除宇宙射线的函数,已经复刻写完
    lam = 1000
    N = len(spec)
    D = sparse.csc_matrix(np.diff(np.eye(N), 2))
    w = np.ones(N)  # 行向量
    while True:
        W = sparse.spdiags(w, 0, N, N)
        Z = W + lam * D.dot(D.transpose())
        z = sparse.linalg.spsolve(Z, w*spec)

        d = spec-z
        c = W @ d
        s = np.std(c)

        if np.any(c > 3*s):
            w[c >= 3*s] = 0
        else:
            break

    spec[w == 0] = z[w == 0] + np.random.randn() * s
    return spec


def cat_spec(spec, p):
    # 使用drPLS拼接光谱的函数
    # intense = np.delete(spec, 1002)
    intense = spec
    p.extend([0, len(intense)])
    q = list(set(p))
    q.sort()
    segments = [(i, j) for i, j in zip(q[:-1], q[1:])]
    base_he = []
    roil = np.array([[i, i+500] for i in range(0, 4000, 500)])
    for seg in segments:
        l = intense[seg[0]:seg[1]] = cosrad_eli(intense[seg[0]:seg[1]])

        base = rp.baseline(np.array(range(len(l))), l, roil,
                           method='drPLS', lam=6.18e3, ratio=0.0001)[1]
        base_he.append((base[0], base[-1]))
    offsets = [0]
    offsets.extend([j[0]-i[1]
                    for i, j in zip(base_he[:-1], base_he[1:])])
    shifts = [sum(offsets[:i]) for i in range(1, len(offsets)+1)]
    for seg, shift in zip(segments, shifts):
        intense[seg[0]:seg[1]] -= shift
    return intense


def specSmooth(x, y):
    y_ = rp.smooth(x, y, Lambda=500)
    noi = y - y_
    y2 = calman(noi)
    return y_ + y2


def calman(z):
    n_iter = len(z)
    d = np.var(z)
    sz = (n_iter,)
    xhat = np.zeros(sz)
    P = np.zeros(sz)

    kf = KalmanFilter(dim_x=1, dim_z=1)
    kf.F = np.array([1])
    kf.H = np.array([1])
    kf.R = np.array([d])
    kf.P = np.array([1.0])
    kf.Q = 0.17
    xhat[0] = 0.0
    P[0] = 1.0
    for k in range(1, n_iter):
        kf.predict()
        xhat[k] = kf.x
        kf.update(z[k], d, np.array([1]))
    return xhat


def specSplit(spec: np.ndarray, start: int, end: int):
    # spec是n×2的矩阵
    return spec[:, (end >= spec[0, :]) & (spec[0, :] >= start)]


def norm_Area(spec: np.ndarray):
    spec -= spec.min()
    area = reduce(lambda x, y: x+y**2, spec, 0)
    if area == 0:
        spec = 1
    else:
        spec /= sqrt(area)
    return spec


if __name__ == '__main__':
    # all_pred_files = glob('d:\\内镜光谱数据*\\**\\预处理\\*.txt', recursive=True)
    """
    for file in tqdm.tqdm(all_pred_files, total=len(all_pred_files), ncols=97):
        # 有进度条的
        o_file = find_origin(file)
        if o_file:
            with open(o_file)as f:
                prefix = [f.readline() for i in range(3)]
            spec = np.loadtxt(o_file, skiprows=3)
    """
    spec = np.loadtxt(
        "C:\\Users\\fire-\\Desktop\\20210511 食道 癌\\食道  A06 2s-0.3mm-0.4 210511 14-52-39.txt", skiprows=3).T
    spec = np.delete(spec, 1002, axis=1)
    spec[1, :] = cat_spec(spec[1, :], [1002, 1960])
    roil = np.array([[i, i+500] for i in range(0, 4000, 500)])
    spec[1, :] = rp.baseline(spec[0, :], spec[1, :], roil, 'drPLS',
                             lam=9.7e7, ratio=0.00047)[0].reshape(-1,)
    spec = specSplit(spec, 800, 1800)
    spec[1, :] = rp.smooth(spec[0, :], spec[1, :])
    spec[1, :] = norm_Area(spec[1, :])
    pylab.plot(spec[0, :], spec[1, :])
    pylab.show()
