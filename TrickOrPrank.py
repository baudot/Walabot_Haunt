#!/usr/bin/env python

'''
Watches for tricker treaters, taunts them to come closer, then tries to 
make them run away.
'''

from __future__ import print_function, division # python2-python3 compatibillity
try: input = raw_input # python2-python3 compatibillity
except NameError: pass # python2-python3 compatibillity
from datetime import datetime, timedelta # used to the current time
from math import sin, cos, radians, sqrt # used to calculate MAX_Y_VALUE
from operator import attrgetter
import WalabotAPI as wlbt
import select, sys
from subprocess import call
from enum import Enum

class prank_state(Enum):
    no_target = 1
    distant_target = 2
    target_approaching = 3
    target_close = 4
    target_fleeing = 5

R_MIN, R_MAX, R_RES = 20, 300, 8 # walabot SetArenaR parameters
THETA_MIN, THETA_MAX, THETA_RES = -4, 4, 2 # walabot SetArenaTheta parameters
PHI_MIN, PHI_MAX, PHI_RES = -4, 4, 2 # walabot SetArenaPhi parametes
THRESHOLD = 15 # walabot SetThreshold parametes
MAX_Y_VALUE = R_MAX * cos(radians(THETA_MAX)) * sin(radians(PHI_MAX))
SENSITIVITY = 0.25 # amount of seconds to wait after a move has been detected
asked_to_quit = False;

# Distance thresholds to cross to trigger different behaviors.
# There's two of each to enable hysteresis. 
# i.e. If a person's standing on a threshold, and their reading is 
# jumping to either side of the threshold, it doesn't keep tripping
# a new reaction constantly. New reactions only are triggered by decisive
# moves.
OUTER_THIRD_APPROACH = R_MAX * 0.63
OUTER_THIRD_RETREAT = R_MAX * 0.69
INNER_THIRD_APPROACH = R_MAX * 0.30
INNER_THIRD_RETREAT = R_MAX * 0.36

wlbt.Init()
wlbt.SetSettingsFolder()
state = prank_state.no_target

def distance(target):
    return sqrt(target.xPosCm**2 + target.yPosCm**2 + target.zPosCm**2)

def target_appears():
    call (["omxplayer", "./sounds/target_detected.mp3"])
    return True

def target_approaches():
    call (["omxplayer", "./sounds/target_approaching.mp3"])
    return True

def target_close():
    call (["omxplayer", "./sounds/target_is_here.mp3"])
    return True

def target_fleeing():
    call (["omxplayer", "./sounds/target_is_fleeing.mp3"])
    return True
    
def report_state():
    global state
    if (state == prank_state.no_target):
        print('No target')
    elif (state == prank_state.distant_target):
		print('Distant target')
    elif (state == prank_state.target_approaching):
		print('Target approaching')
    elif (state == prank_state.target_close):
		print('Target close')
    elif (state == prank_state.target_fleeing):
		print('Target fleeing')

def react_to_moving_target(nearest_target):
    global state
    if (state == prank_state.no_target):
        if (distance(nearest_target) < R_MAX):
            state = prank_state.distant_target
            target_appears()
    elif (state == prank_state.distant_target):
		if (distance(nearest_target) < OUTER_THIRD_APPROACH):
			state = prank_state.target_approaching
			target_approaches()
    elif (state == prank_state.target_approaching):
		if (distance(nearest_target) > OUTER_THIRD_RETREAT):
			state = prank_state.target_fleeing
			target_fleeing()
		if (distance(nearest_target) < INNER_THIRD_APPROACH):
			state = prank_state.target_close
			target_close()
    elif (state == prank_state.target_close):
		if (distance(nearest_target) > OUTER_THIRD_RETREAT):
			state = prank_state.target_fleeing
			target_fleeing()
    elif (state == prank_state.target_fleeing):
		if (distance(nearest_target) < INNER_THIRD_APPROACH):
			state = prank_state.target_close
			target_close()

def no_enter_keystroke():
	i,o,e = select.select([sys.stdin],[],[],0.0001)
	for s in i:
		if s == sys.stdin:
			input = sys.stdin.readline()
			return False
	return True

def wala_connect():
    while True:
        try:
            wlbt.ConnectAny()
        except wlbt.WalabotError as err:
            if err.code == 19: # 'WALABOT_INSTRUMENT_NOT_FOUND'
                input("- Connect Walabot and press 'Enter'.")
        else:
            print('- Connection to Walabot established.')
            return

def wala_config():
	wlbt.SetProfile(wlbt.PROF_SENSOR_NARROW)
	wlbt.SetArenaR(R_MIN, R_MAX, R_RES)
	wlbt.SetArenaTheta(THETA_MIN, THETA_MAX, THETA_RES)
	wlbt.SetArenaPhi(PHI_MIN, PHI_MAX, PHI_RES)
	wlbt.SetThreshold(THRESHOLD)
	wlbt.SetDynamicImageFilter(wlbt.FILTER_TYPE_MTI)
	print('- Walabot Configurated.')

def wala_start():
    wlbt.Start()
    wlbt.StartCalibration()
    print('- Calibrating...')
    while wlbt.GetStatus()[0] == wlbt.STATUS_CALIBRATING:
        wlbt.Trigger()
    print('- Calibration ended.\n- Ready!')

def wala_get_result():
    global state
    valid_targets = 0
    # print('Target: ')
    try:
        targets = wlbt.GetSensorTargets()
        # print('...acquired...')
    except wlbt.WalabotError as err:
        print(err)
        return
    if targets:
        for target in targets:
            # print('Amplitude: ')
            # print(target.amplitude)
            if (target.amplitude > 0.001):
                valid_targets += 1
    if (valid_targets > 0):
        nearest_target = min(targets, key=lambda t: distance(t)) 
        report_state()
        # print(distance(nearest_target))
        react_to_moving_target(nearest_target)
        # Trigger once without checking the results: This avoids double-triggering
        # as a shadow-signal appears behind a signal that has just vanished.
        wlbt.Trigger()
    else:
         if ((state == prank_state.distant_target) or (state == prank_state.target_fleeing)):
            state = prank_state.no_target
    return False

def wala_stop():
    wlbt.Stop()
    wlbt.Disconnect()

def main():
	wala_connect()
	wala_config()
	wala_start()
	print("Watching for Trick-or-Treaters.\nPress Enter to quit.")
	while (no_enter_keystroke()):
	  wlbt.Trigger()
	  wala_get_result()
	wala_stop()
	return 0

if __name__ == '__main__':
	main()
