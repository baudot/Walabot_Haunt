from __future__ import print_function
from sys import platform
from os import system
import WalabotAPI as wlbt


R_MIN, R_MAX, R_RES = 20, 600, 8
T_MIN, T_MAX, T_RES = -15, 15, 10
P_MIN, P_MAX, P_RES = -25, 25, 8
SLICES = [R_MAX * 0.2, R_MAX * 0.4, R_MAX * 0.6, R_MAX * 0.8]
D_FACTOR = 5  # should be changed according to environment
C_MIN = 0
C_MAX = D_FACTOR * 2

counters = [0, 0, 0, 0]


def distance(t):
    return (t.yPosCm ** 2 + t.zPosCm ** 2) ** 0.5


wlbt.Init()
wlbt.SetSettingsFolder()
wlbt.ConnectAny()
wlbt.SetProfile(wlbt.PROF_SENSOR)
wlbt.SetArenaR(R_MIN, R_MAX, R_RES)
wlbt.SetArenaTheta(T_MIN, T_MAX, T_RES)
wlbt.SetArenaPhi(P_MIN, P_MAX, P_RES)
wlbt.SetThreshold(100)
wlbt.SetDynamicImageFilter(wlbt.FILTER_TYPE_MTI)
wlbt.Start()


while True:
    wlbt.Trigger()
    targets = wlbt.GetSensorTargets()
    for t in targets:
        pass
    system('cls' if platform == 'win32' else 'clear')  # clear the terminal
    for i, s in enumerate(SLICES):
        targetsBelow = [t for t in targets if distance(t) < s]
        if targetsBelow:
            counters[i] = min(counters[i] + 1, C_MAX)
            targets = [t for t in targets if t not in targetsBelow]
        else:
            counters[i] -= 0.5 if counters[i] > 0 else 1
            counters[i] = max(counters[i], C_MIN)
    validSlices = [i for (i, a) in enumerate(counters) if a > D_FACTOR]
    print(counters)
    if not validSlices:
        print("No targets")
    for i in validSlices:
        if i is 0:
            print("People below {} cm".format(SLICES[i]))
        else:
            print("People between {} cm and {} cm".format(
                SLICES[i-1], SLICES[i]
            ))

wlbt.Stop()
wlbt.Disconnect()
