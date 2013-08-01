#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# Listens for mode button input.  For use with orb.py

import RPi.GPIO as gpio
import os
from time import sleep
MODES = ('weather','moodlight','alarmclock')

# Set up our mode button pin for input
MODEPIN = 10
gpio.setwarnings(False)
gpio.setmode(gpio.BCM)
gpio.setup(MODEPIN, gpio.IN)

# Command for killing the current orb.py process
killcmd="kill -9 $(ps auxwww | grep orb.py | head -1 | awk '{ print $2 }')"
orbscript='/usr/local/bin/orb.py'

currmode = 0
while True:
    if gpio.input(MODEPIN) == False:
        if currmode < len(MODES) - 1:
            currmode += 1
        else:
            currmode = 0
        print MODES[currmode]
        os.system(killcmd)
        os.system(orbscript+' '+MODES[currmode]+' &')
        print orbscript+' '+MODES[currmode]
    sleep(0.5)
