#!/usr/bin/python3

import RPi.GPIO as GPIO
import time, threading, smbus, queue

'''Raspberry Pi GPIO Configuration
SDA & SCL - I presume the I2C code takes care of these pins
GPIO4 - USED to check TI-ADS1115 Analog to Digital Converter ALRT line
    Alert goes low when ADC conversion is complete - Input requires pull-up
GPIO14 - USED to detect reed switch closure - Input requires pull-up
Output data structure:
    B7:4    Time in sec since epoch (1/1/1970)
    B3:2    Milliseconds
    B1:0    Data
        b14=1 => 1 m wind travel
        b14=0 => data/26360*360 = direction
'''

# Constants

fileName = 'Wind.bin'   # Output File Name
textFileName = 'Wind.txt'

velCounter = 0
t0 = time.time()
velThreshold = 0.02     # Sec = 116 mph



class i2cDev(object):

    bus = smbus.SMBus(1)
    # Register Pointers
    convReg = 0
    confReg = 1
    loReg   = 2
    hiReg   = 3
    alert = 4       # GPIO4
    switch = 14     # GPIO14

    # A/D Configuration register
    mux = 4         # Bits 14:12
    pga = 1         # Bits 11:9 - Gain = 1; FS = 4.096V
    mode = 0        # Bit 8 - Continuous conversions
    data_rate = 1   # Bits 7:5 - 16 S/Sec
    comp_mode = 0   # Bit 4 - Not used
    comp_pol = 0    # Bit 3 - Alert active low
    comp_lat = 0    # Bit 2 not used
    comp_que = 0    # Bits 1:0 2 bits - Assert Alert after 1 conversion
    # A/D TDhreshold Registers
    hi_thresh = (1 << 15)
    lo_thresh = 0
    adc_addr = 0x48
    configReg = (mux << 12) + (pga << 9) + (mode << 8) + (data_rate << 5) +\
                (comp_mode << 4) + (comp_pol << 3) + (comp_lat << 2) +\
                (comp_que << 0)

    def writeReg(self, regAddr, word):
        v = ((word << 8) & 0XFF00) + (word >> 8)
        self.bus.write_word_data(self.addr, regAddr, v)

    def writePointer(self, regAddr):
        self.bus.write_byte(self.addr, regAddr)

    def __init__(self, addr):
        self.addr = addr
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(i2cDev.alert, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        GPIO.setup(i2cDev.switch, GPIO.IN, pull_up_down = GPIO.PUD_UP)
        # Setup A/D Converter
        self.writeReg(i2cDev.hiReg, i2cDev.hi_thresh)         # High threshold register
        self.writeReg(i2cDev.loReg, i2cDev.lo_thresh)         # Low threshold register
        self.writeReg(i2cDev.confReg, i2cDev.configReg)       # Configuration register
        # print('registers = {0:4X}, {1:4X}, {2:4X}'.format(configReg, hi_thresh, lo_thresh))

    def startConversion(self):
        self.writeReg(i2cDev.confReg, (1<<15) & i2cDev.configReg)

    def readReg(self, regAddr):
        a = self.bus.read_word_data(self.addr, regAddr)
        v = ((a << 8) & 0xFF00) + (a >> 8)
        return v

class binaryWriter(threading.Thread):
    def __init__(self, writeQueue):
        threading.Thread.__init__(self)
        self.queue = writeQueue

    def write(self, message):
        file = open(fileName, 'ab')
        file.write(message)
        file.close()

    def run(self):
        while True:
            message = self.queue.get()
            self.write(message)
            self.queue.task_done()


class velLogger(threading.Thread):

    velThreshold = 0.02

    def __init__(self, outputQueue):
        global velCounter
        threading.Thread.__init__(self)
        self.queue = outputQueue
        self.t0 = time.time()
        velCounter = 0

    def run(self):
        global velCounter
        while True:
            #time.sleep(1.0)
            GPIO.wait_for_edge(i2cDev.switch, GPIO.FALLING)
            t= time.time()
            if (t - t0) > velLogger.velThreshold:     # skip switch bouonce
                b = formatedTime() + b'\x00\x80'
                self.queue.put(b)
                velCounter += 1

class directionLogger(threading.Thread):
    def __init__(self, outputQueue):
        threading.Thread.__init__(self)
        self.queue = outputQueue
        adc_addr = 0x48
        self.adc = i2cDev(adc_addr)

    def run(self):
        global velCounter
        while True:
            #wait for 1 sec
            time.sleep(1.0)
            #read direction
            dir = self.adc.readReg(i2cDev.convReg)
            b = formatedTime() + dir.to_bytes(2, 'little')
            self.queue.put(b)
            #print ('At {0:14.3f} voltage was {1:6d} and direction was {2:3d} deg'.format(time.time(),int(dir), int(dir*360.0/26360)))
            with open(textFileName, 'a') as tf:
                tf.write('{0:10d},{1:5d},{2:3d}\n'.format(int(time.time()), int(dir), velCounter))
                tf.close()
            velCounter = 0


def initializeSystem():
    # Setup GPIO

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(alert, GPIO.IN, pull_up_down = GPIO.PUD_UP)
    GPIO.setup(switch, GPIO.IN, pull_up_down = GPIO.PUD_UP)

def formatedTime():
    t = time.time()
    a = int(t)
    return int(a).to_bytes(4, 'little') + int((t-a)*10000).to_bytes(2, 'little')

def writeFile(b):
    with open(fileName, 'ab') as f:
        f.write(b)
        f.close()

def velocity():
    global velCounter, t0, velThreshold
    # Set bit 15 = 1 for velocity
    while True:
        #time.sleep(1.0)
        GPIO.wait_for_edge(switch, GPIO.FALLING)
        t= time.time()
        if (t - t0) > velThreshold:     # skip switch bouonce
            b = formatedTime() + b'\x00\x80'
            writeFile(b)
            velCounter += 1
        #print('Switched at {0:4X}H sec and {1:2X}H 0.1 msec'.format(int(t), int((t-int(t))*10000)))

def direction():
    global velCounter
    # set bit 15 for direction
    adc = i2cDev(adc_addr)
    while True:
        #wait for 1 sec
        time.sleep(1.0)
        #read direction
        dir = adc.readReg(convReg)
        b = formatedTime() + dir.to_bytes(2, 'little')
        writeFile(b)
        #print ('At {0:14.3f} voltage was {1:6d} and direction was {2:3d} deg'.format(time.time(),int(dir), int(dir*360.0/26360)))
        with open(textFileName, 'a') as tf:
            tf.write('{0:10d},{1:5d},{2:3d}\n'.format(int(time.time()), int(dir), velCounter))
            tf.close()
        velCounter = 0
        #write time, direction to file
        #print('registers = {0:4X}, {1:4X}, {2:4X}'.format(a, b, c))

def main():
    #initializeSystem()
    outputQueue = queue.Queue()
    # Start the file-writer
    wrt = binaryWriter(outputQueue)
    wrt.setDaemon(True)
    wrt.start()
    # spawn thread 1 - 1 sec sampling of A/D
    d = directionLogger(outputQueue)
    #d.setDaemon(True)
    d.start()
    #directionThread = threading.Thread(target=direction)
    #directionThread.start()
    # spawn thread 2 - recording time of anemometer switch closings
    v = velLogger(outputQueue)
    #v.setDaemon(True)
    v.start()
    #velocityThread = threading.Thread(target = velocity)
    #velocityThread.start()


if __name__ == '__main__':
    main()
