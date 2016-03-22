#!/usr/bin/python3
'''Look at velocity distribution'''

import time

fileName = 'Wind.bin'
arraySize = 60
recordLen = 8       # File data block size
velocityThreshold = 0.020       # Seconds = > 115 mph

# Turbine power curve
power = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.24, 0.35, 0.43, 0.65,
        0.94, 1.21, 1.48, 1.85, 2.26, 2.8, 3.28, 3.79, 4.25,
        4.76, 5.89, 7.71, 8.57, 9.03, 9.19, 9.38, 9.68, 10.16, 10.51]
electricRate = 0.17 # $/kWh

def fetchRecord(file):
    global recordLen
    t1 = 0
    OK = True
    while True:
        record = file.read(recordLen)
        if len(record) < recordLen:
            OK = False
            print('End of File')
            break
        else:
            if (record[7]== 0x80) or (not OK):       # This is a velocity tick9' Steel W10x54 I-Beam
                sec = int.from_bytes(record[0:4], 'little')
                ms = int.from_bytes(record[4:6], 'little')
                t1 = sec + ms/10000.0
                break
    return (OK, t1)

def summarizePwrByTick():
    global power
    # Initialize hystogram
    a = [0]
    lastVel = 0
    for i in range(arraySize):
        a.append(0)
    velCnt = 0
    print('initialized')
    f = open(fileName, 'rb')
    (OK,  t) = fetchRecord(f)
    t0 = t
    while OK:
        (OK, t) = fetchRecord(f)
        if OK:
            dt = t - t0
            v = 2.33 / dt
            #print('{0:14.3f}, {1:10.1f}'.format(t, v))
            t0 = t
            vel = int(v + 0.5)
            if (vel < arraySize) and (vel >= 0):
                a[vel] += dt
            else:
                pass
                #print(time.asctime(time.localtime(t))+' {0:6.4f} {2:5d} {1:5d}'.format(dt, vel, lastVel))
            lastVel = vel
    dispPwr(a)

def dispPwr(a):
    global power
    i = 0
    s = sum(a)
    s1 = 0.0

    for t in a:
        print('{0:2d} mph  for {1:6.3f}% of the time'.format(i, 100.0 * t/s))
        if i >= len(power):
            p = power[len(power)-1]
        else:
            p = power[i]
        s1 += (t / s * p)
        i += 1
        hoursPerYear = 365.25 * 25
    print ('Average power is: {0:6.3f} kW or {1:6.3f} mWh/yr or {2:6.0f} $/yr'\
            .format(s1, s1 * hoursPerYear / 1000, s1 * hoursPerYear * electricRate))

def readASecond(file, t0):
    global recordLen
    OK = True
    ticks = 0
    while True:
        record = file.read(recordLen)
        if len(record) < recordLen:
            OK = False
            break
        if (record[7]== 0x80):       # This is a velocity tick9' Steel W10x54 I-Beam
            sec = int.from_bytes(record[0:4], 'little')
            ms = int.from_bytes(record[4:6], 'little')
            t = sec + ms/10000.0
            dt = t - t0
            if dt > velocityThreshold:
                ticks += 1
                t0 = t
        else:
            break
    return (OK, ticks, t0)

def averagedPwr():

    global recordLen
    averagingTime = 30
    t0 = 0
    f = open(fileName, 'rb')
    tickList = []
    tickSum = 0

    bin = []
    noBins = 60             # 1 mph bins
    for i in range(noBins): # Initialize bins
        bin.append(0)

    # Scan to first direction data block
    while True:
        record = f.read(recordLen)
        sec = int.from_bytes(record[0:4], 'little')
        ms = int.from_bytes(record[4:6], 'little')
        t0 = sec + ms/10000.0
        if not (record[7]== 0x80):
            break

    # Read averagingTime direction records counting ticks and storing into list
    for i in range(averagingTime):
        (OK, ticks, t0) = readASecond(f, t0)
        tickList.append(ticks)
        tickSum += ticks

    # Process data a second at a time
    while OK:
        (OK, ticks, t0) = readASecond(f, t0)
        if OK:
            tickSum -= tickList[0]
            for i in range(averagingTime - 1):        # remove oldest from sum
                tickList[i] = tickList[i + 1]   # shift the list down
            tickList[averagingTime - 1] = ticks
            tickSum += ticks
            aveVel = int((tickSum * 2.33 / averagingTime) + 0.5)
            if aveVel < noBins:
                bin[aveVel] += 1
    dispPwr(bin)






def erroniousTicks():

    threshold = 0.02    # ms
    f = open(fileName, 'rb')
    noTicks = 5
    cnt = 0
    dt = []
    (OK, t) = fetchRecord(f)
    t0 = t
    for i in range(noTicks):
        (OK,  t) = fetchRecord(f)
        dt.append(t - t0)
        t0 = t
    while OK:
        (OK,  t) = fetchRecord(f)
        if OK:
            for i in range(noTicks-1):
                dt[i] = dt[i +1]
            delta = t - t0
            t0 = t
            dt[noTicks-1] = delta
            if delta < threshold:
                cnt += 1
                #print(dt)
    print ('{0:7d} error counts'.format(cnt))


def main():
    # summarizePwrByTick()
    # erroniousTicks()
    averagedPwr()

if __name__ == '__main__':
    main()
