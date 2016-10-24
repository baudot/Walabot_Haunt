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
import RPi.GPIO as GPIO
import time

class prank_state(Enum):
    no_target = 1
    distant_target = 2
    target_approaching = 3
    target_close = 4
    target_fleeing = 5

'''
Change the behavior of the pranker by changing these variables:
R_MIN and R_MAX set the minimum and maximum range the Walabot scans for 
trick-or-treaters at, in centimeters. Modify these settings to set the 
range that the pranker starts to taunt trick-or-treaters at.

You can widen the area being scanned by increasing the THETA and PHI 
variables. 

The bigger you increase the area, the longer each scan takes. With the
current settings, each scan completes in under a second, which makes the
pranker fairly responsive.
'''

R_MIN, R_MAX, R_RES = 20, 300, 8 # walabot SetArenaR parameters
THETA_MIN, THETA_MAX, THETA_RES = -4, 4, 2 # walabot SetArenaTheta parameters
PHI_MIN, PHI_MAX, PHI_RES = -4, 4, 2 # walabot SetArenaPhi parametes
THRESHOLD = 15 # walabot SetThreshold parametes
MAX_Y_VALUE = R_MAX * cos(radians(THETA_MAX)) * sin(radians(PHI_MAX))
SENSITIVITY = 0.25 # amount of seconds to wait after a move has been detected
asked_to_quit = False;

'''
Change the color of the optional light strip by setting red_brightness,
green_brightness, and blue_brightness.
'''

red_brightness = 100
green_brightness = 10
blue_brightness = 0

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

# Prepare the red, green and blue pins to fade in and out.
GPIO.setmode(GPIO.BOARD)
red_pin = 35
green_pin = 33
blue_pin = 37
GPIO.setup(red_pin, GPIO.OUT)
GPIO.setup(green_pin, GPIO.OUT)
GPIO.setup(blue_pin, GPIO.OUT)
red = GPIO.PWM(red_pin,200)
green = GPIO.PWM(green_pin,200)
blue = GPIO.PWM(blue_pin,200)


wlbt.Init()
wlbt.SetSettingsFolder()
state = prank_state.no_target

def setup_lights():
    global red_pin, green_pin, blue_pin
    global red, green, blue
    red.start(0)
    green.start(0)
    blue.start(0)

def pumpkin_flash():
    global red_pin, green_pin, blue_pin
    global red, green, blue
    global red_brightness, green_brightness, blue_brightness

    for i in range(100):
      red.ChangeDutyCycle(i * red_brightness / 100.0)
      green.ChangeDutyCycle(i * green_brightness / 100.0)
      blue.ChangeDutyCycle(i * blue_brightness / 100.0)
      time.sleep(0.001)
    for i in range(100):
      red.ChangeDutyCycle(red_brightness - (i * red_brightness / 100.0))
      green.ChangeDutyCycle(green_brightness - (i * green_brightness / 100.0))
      blue.ChangeDutyCycle(blue_brightness - (i * blue_brightness / 100.0))
      time.sleep(0.001)

    red.ChangeDutyCycle(0)
    green.ChangeDutyCycle(0)
    blue.ChangeDutyCycle(0)

def distance(target):
    return sqrt(target.xPosCm**2 + target.yPosCm**2 + target.zPosCm**2)

def target_appears():
    pumpkin_flash()
    call (["omxplayer", "-o", "both", "./sounds/target_detected.mp3"])
    pumpkin_flash()
    return True

def target_approaches(num_targets):
    pumpkin_flash()
    if (num_targets == 2):
        call (["omxplayer", "-o", "both", "./sounds/two_targets_approaching.mp3"])
    elif (num_targets == 3):     
        call (["omxplayer", "-o", "both", "./sounds/three_targets_approaching.mp3"])
    elif (num_targets == 4):     
        call (["omxplayer", "-o", "both", "./sounds/four_targets_approaching.mp3"])
    elif (num_targets == 5):     
        call (["omxplayer", "-o", "both", "./sounds/five_targets_approaching.mp3"])
    else:
        call (["omxplayer", "-o", "both", "./sounds/target_approaching.mp3"])
    pumpkin_flash()
    return True

def target_close():
    pumpkin_flash()
    call (["omxplayer", "-o", "both", "./sounds/target_is_here.mp3"])
    pumpkin_flash()
    return True

def target_fleeing():
    pumpkin_flash()
    call (["omxplayer", "-o", "both", "./sounds/target_is_fleeing.mp3"])
    pumpkin_flash()
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

def react_to_moving_target(nearest_target, num_targets):
    global state
    if (state == prank_state.no_target):
        if (distance(nearest_target) < R_MAX):
            state = prank_state.distant_target
            target_appears()
    elif (state == prank_state.distant_target):
		if (distance(nearest_target) < OUTER_THIRD_APPROACH):
			state = prank_state.target_approaching
			target_approaches(num_targets)
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
    
    try:
        targets = wlbt.GetSensorTargets()
    except wlbt.WalabotError as err:
        print(err)
        return
    if targets:
        for target in targets:
            if (target.amplitude > 0.001):
                valid_targets += 1
    if (valid_targets > 0):
        nearest_target = min(targets, key=lambda t: distance(t)) 
        report_state()
        # print(distance(nearest_target))
        react_to_moving_target(nearest_target, valid_targets)
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
	setup_lights()
	wala_connect()
	wala_config()
	wala_start()
	print("Watching for Trick-or-Treaters.\nPress Enter to quit.")
	while (no_enter_keystroke()):
	  wlbt.Trigger()
	  wala_get_result()
	wala_stop()
	GPIO.cleanup()
	return 0

if __name__ == '__main__':
	main()

