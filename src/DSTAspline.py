import numpy as np
import numpy.random as nr
import rampy as rp
import matplotlib.pyplot as plt
from csaps import csaps


def DSTAspline(X: np.ndarray, Y0: np.ndarray, psmooth=9E-7):
    Y0.reshape([1, -1])
    fFlag = True
    N = len(Y0)
    err = max(round(Y0[0]/500), 4)
    err = 7
    o_1 = np.ones(len(X), dtype=int)  # 一个全1的向量
    gen_max = 128

    t = X.reshape(-1).copy()
    F = 0.1
    bestbase = np.ones(N, dtype=int)
    pop_best = np.ones(N, dtype=int)
    Ys = Y0.copy()
    for gen in range(gen_max):
        tt = t[bestbase == 1]
        Yt = Y0[bestbase == 1]
        Y = csaps(tt, Yt, t, smooth=psmooth)

        e1 = sum(abs(Ys-Y))/N
        e2 = sum(bestbase)
        fitness1 = (e1*e2)/(e1+e2)
        D = min(round(F*e2), N)
        muD = nr.randint(0, N, size=D)
        pop_m = bestbase.copy()
        pop_m[muD] = 0

        pop_m[0:5] = 1
        pop_m[-5:] = 1

        bestbase = pop_m.copy()
        tt = t[bestbase == 1]
        Yt = Y0[bestbase == 1]

        Y = csaps(tt, Yt, t, smooth=psmooth)
        for j in range(N):
            if Y[j]+err < Ys[j]:
                Ys[j] = Y[j]
        bestbase[Ys < Y0] = 0
        bestbase[Ys == Y0] = 1

        Ys[0:11] = Y0[0:11]
        Ys[-10:] = Y0[-10:]
        e1 = sum(abs(Ys-Y))/N
        e2 = sum(bestbase)
        fitness2 = (e1*e2)/(e1+e2)
        if gen >= 2 and (abs(fitness1-fitness2) < 5e-4):
            break
        bestbase[0:10] = 1
        bestbase[-10:] = 1

    pop_best = csaps(t[bestbase == 1],
                     Y0[bestbase == 1], t, smooth=psmooth)

    if fFlag:
        old_best = pop_best
        fFlag = False

    p = sum(o_1[pop_best > Y0])
    return pop_best


if __name__ == '__main__':
    xy = np.loadtxt(
        "C:\\Users\\fire-\\Desktop\\角切迹 A2 2-0.3mm-0.4 220830 11-36-05.txt", skiprows=3, encoding='utf')
    # xy = np.loadtxt(
    # "C:\\Users\\fire-\\Desktop\\cell5_norm.arc_data")
    x = xy[:, 0]
    y = xy[:, 1]
    # y = csaps(x, y, x, smooth=1e-1)
    b = DSTAspline(y, 1e-5)

    y2, b2 = rp.baseline(x, y, np.array(
        [[0, 1000], [2000, 2500]]), 'drPLS', lam=1e8)

    plt.figure()
    plt.plot(x, y, color='blue')
    plt.plot(x, b, color='red')
    plt.plot(x, b2, color='green')

    plt.figure()
    y = rp.smooth(x, y-b, d=500)+b
    plt.plot(x, y-b, color='blue')
    plt.plot(x, np.zeros(len(x)), color='red')
    plt.plot(x, y2-min(y2), color='green')
    print(xy.size)
    plt.show()
    rp.smooth()
