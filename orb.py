#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
# Script for controlling a BlinkM enabled alarm clock
# Requires blinkMplay.sh which can be downloaded here:
# http://www.raspberrypi.org/phpBB3/viewtopic.php?t=11969&p=213970
import os
import sys
import socket
import pywapi
import RPi.GPIO as gpio
from subprocess import *
from time import sleep,time
from datetime import datetime
from Adafruit_CharLCD import Adafruit_CharLCD

# Disable annoying RPi.gpio warnings
gpio.setwarnings(False)

# Pre-define some blinkM colors for easy use
rgb_red = ('255','0','0')
rgb_green = ('0','255','0')
rgb_blue = ('0','0','255')
rgb_cyan = ('0','255','255')
rgb_magenta = ('255','0','255')
rgb_yellow = ('255','255','0')
rgb_white = ('255','255','255')
rgb_black = ('0','0','0')

# Path to blinkm binary
blinkm = '/usr/local/bin/blinkm'

def getIPaddr(target):
    '''Gets the current IP address using python's socket function.'''
    ipaddr = ''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((target, 8000))
        ipaddr = s.getsockname()[0]
        s.close()
    except:
        pass
    return ipaddr 

def printLCD(string1, string2):
    '''Prints string1 and string2 onto a 16x2 character LCD.'''
    lcd = Adafruit_CharLCD()
    lcd.begin(16,1)
    lcd.clear()
    sleep(0.5)
    lcd.message(string1+"\n")
    lcd.message(string2)

def blinkMFade( red, green, blue, speed ):
    '''Fade the blinkM to your chosen RGB color at speed 
        (1 = slowest, 255 = faster )
    '''
    os.system(blinkm+' set-fade-speed -f '+speed)
    os.system(blinkm+' fade-rgb -r %s -g %s -b %s' % ( red, green, blue ))
    print 'Set blinkM RGB values at: '+red+' '+blue+' '+green

def blinkMStop():
    '''blinkM.  WAT R U DOIN?  blinkM...STAHP!'''
    os.system(blinkm+' stop-script')
    blinkMFade( *rgb_black, speed='255' )

def getTempRGB(temp_f):
    '''Generates an RGB tuple corresponding to the current temperature'''
    if temp_f <= 32.0:
        red = 0
        green = 0
        blue = 255
    elif 32.0 < temp_f <= 72.0:
        red = 0
        green = 255 * (temp_f - 32) / 40
        blue = 255 - green
    elif 72.0 < temp_f <= 100.0:
        red = 255 * (temp_f - 72) / 27
        green = 255 - red
        blue = 0
    elif temp_f > 100.0:
        red = 255
        green = 0
        blue = 0
    red = int(red)
    green  = int(green)
    blue = int(blue)
    return(str(red), str(green), str(blue))

def moodlight():
    '''Allows user to manually select from the built-in blinkM scripts.'''
    UPPIN = 9
    DOWNPIN = 11
    gpio.setwarnings(False)
    gpio.setmode(gpio.BCM)
    gpio.setup(UPPIN, gpio.IN)
    gpio.setup(DOWNPIN, gpio.IN)
    SCRIPTS = ('Custom','RGB','White Flash','Red Flash','Green Flash',
               'Blue Flash', 'Cyan Flash', 'Magenta Flash', 
               'Yellow Flash', 'Black (Off)', 'Hue Cycle', 'Mood Light',
               'Virtual Candle', 'Water Reflection', 'Old Neon',
               'The Seasons', 'Thunderstorm', 'Traffic Light', 
               'Morse Code SOS')
    printLCD('Mood Light','')
    sleep(1)
    currscript = 0
    printLCD('Select With < >',SCRIPTS[currscript])
    os.system(blinkm+' play-script -s %s' % currscript)
    while True:
        if gpio.input(UPPIN) == False:
            print "Up button pressed."
            if currscript < len(SCRIPTS) - 1:
                currscript += 1
            else:
                currscript = 0
            os.system(blinkm+' play-script -s %s' % currscript)
            printLCD('Select With < >',SCRIPTS[currscript])
        if gpio.input(DOWNPIN) == False:
            print "Down button pressed."
            if currscript == 0:
                currscript = len(SCRIPTS) - 1
            else:
                currscript -= 1
            os.system(blinkm+' play-script -s %s' % currscript)
            printLCD('Select With < >',SCRIPTS[currscript])
        sleep(0.5)

def alarmclock():
    '''Right now it's just a simple clock.'''
    printLCD('Clock Mode','')
    sleep(1)
    curtime = datetime.now().strftime('%a %b %d %H:%M')
    checktime = time()
    printLCD('Austin, TX',curtime)
    while True:
        if time() - checktime > 60:
            print "An minute has passed, updating clock..."
            curtime = datetime.now().strftime('%a %b %d %H:%M')
            printLCD('Austin, TX',curtime)
            checktime = time()
        sleep(0.5)

def weather(interval):
    '''Fetches weather from NOAA XML feed, outputs the data to LCD and the 
    blinkM.  Update interval is specified in seconds.'''
    while True:
        printLCD('Weather Mode','Updating data...')
        sleep(1)
        # First fetch current weather from the NOAA feed
        noaa = pywapi.get_weather_from_noaa('KATT')
        conditions1 = noaa['weather']
        conditions2 = noaa['temp_f']+'F '+noaa['pressure_mb']+' '+noaa['relative_humidity']+'%'
        printLCD(conditions1,conditions2)
        # Now we set up the blinkM script
        blinkMStop()
        tempcolor = getTempRGB(float(noaa['temp_f']))
        checktime = time()
        # For manual testing
        #noaa['weather'] = 'Overcast'
        # Check for unusual weather conditions.
        if 'Tornado' in noaa['weather']:
            # The SOS script seems appropriate here
            os.system(blinkm+' play-script -s 18')
            sleep(interval)
        elif 'Thunderstorm' in noaa['weather']:
            # We have a built-in thunderstorm script
            os.system(blinkm+' play-script -s 16')
            sleep(interval)
        elif 'Rain' in noaa['weather'] or 'Drizzle' in noaa['weather']:
            # Gently fade between black and the temperature color
            while time() - checktime < interval:
                blinkMFade(*tempcolor, speed='16')
                sleep(2)
                blinkMFade(*rgb_black, speed='16')
                sleep(1)
        elif 'Snow' in noaa['weather'] or 'Hail' in noaa['weather'] or 'Freezing' in noaa['weather']:
            # Gently fade between black and white
            while time() - checktime < interval:
                blinkMFade(*rgb_white, speed='16')
                sleep(2)
                blinkMFade(*rgb_black, speed='16')
                sleep(1)
        elif 'Mostly Cloudy' in noaa['weather'] or 'Overcast' in noaa['weather'] or 'Fog' in noaa['weather']:
            # Gently fade between soft white and the temperature color
            while time() - checktime < interval:
                blinkMFade(*tempcolor, speed='4')
                sleep(4)
                blinkMFade('72','72','72','4')
                sleep(2)
        else:
            # If none of the above apply, just set the temperature color
            blinkMFade(*tempcolor, speed='1')
            sleep(interval)

##############################################################################
# Executable code goes below here...
##############################################################################

usage = "This script requires exactly one argument to set the mode.\nUsage: "+sys.argv[0]+" weather|alarmclock|moodlight"

if len(sys.argv) != 2:
    print usage
    sys.exit(1)

mode = sys.argv[1]

if mode == 'weather':
    weather(3600)
elif mode == 'moodlight':
    moodlight()
elif mode == 'alarmclock':
    alarmclock()
else:
    print usage
    sys.exit(1)