#!/usr/bin/python3

import RPi.GPIO as GPIO
import time, threading

'''Raspberry Pi GPIO Configuration
SDA & SCL - I presume the I2C code takes care of these pins
GPIO4 - USED to check TI-ADS1115 Analog to Digital Converter ALRT line
    Alert goes low when ADC conversion is complete - Input requires pull-up
GPIO17 - USED to detect reed switch closure - Input requires pull-up
'''

# Constants
# GPIO4
alert = 4
switch = 17

# A/D Configuration register
mux = 4         # Bits 14:12
pga = 1         # Bits 11:9 - Gain = 1; FS = 4.096V
mode = 1        # Bit 8 - Single shot conversion
data_rate = 7   # Bits 7:5 - Max speed - 860 s/sec
comp_mode = 0   # Bit 4 - Not used
comp_pol = 0    # Bit 3 - Alert active low
comp_lat = 0    # Bit 2 not used
comp_que = 0    # Bits 1:0 2 bits - Assert Alert after 1 conversion
# A/D TDhreshold Registers
hi_thresh = (1 << 15)
lo_thresh = 0
adc_addr = 0x48
# Register Pointers
convReg = 0
confReg = 1
loReg   = 2
hiReg   = 3

def initializeSystem():
    # Setup GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(alert, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(switch, GPIO.IN, pull_up_down = GPIO.PUD_UP)

    # Setup A/D Converter
    configReg = (mux << 12) + (pga << 9) + (mode << 8) + (data_rate << 5) +\
                (comp_mode << 4) + (comp_pol << 3) + (comp_lat << 2) +\
                (comp_que << 0)


def velocity():
    pass

def direction():
    while True:
        pass
        #wait for 1 sec
        #start conversion
        #wait for alert
        #read direction
        #write time, direction to file

def main():
    initializeSystem()


if __name__ == '__main__':
    main()
