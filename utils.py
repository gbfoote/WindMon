#!/usr/bin/python3
'''Read out Wind.bin file'''

import time, subprocess

t0 = time.mktime((2016,1,1,0,0,0,0,0,0))
fileName = '/home/gbf/repos/WindMon/rpi/Wind.bin'
connectToRPi = ['sshfs', '10.11.2.189:/home/gbf/WindMon', '/home/gbf/repos/WindMon/rpi']
disconnectFromRPi = ['fusermount', '-u', '/home/gbf/repos/WindMon/rpi']
dispLen = 80
dataLen = 8
north = 26360   # raw a/d
offset = 275    # deg


def main():
    subprocess.call(connectToRPi)
    f = open(fileName, 'rb')
    f.seek(-dataLen * dispLen, 2)
    t0 = 1456519594.0
    dirCnt = 0
    velCnt = 0
    dirSum = 0
    initTime = 0
    finalTime = 0
    for i in range(0,dispLen):
        b = f.read(dataLen)
        if len(b) < 8:
            break
        sec = int.from_bytes(b[0:4], 'little')
        ms = int.from_bytes(b[4:6], 'little')
        t1 = sec + ms/10000.0
        if (b[7]== 0x80):       # This is a velocity tick
            if velCnt == 0:
                initTime = t1
            velCnt += 1
            finalTime = t1
            dt = t1-t0
            t0 = t1
            vel = int(2.23 / dt)
            print(time.ctime(t1) + ' velocity = {0:3d} mph; dt = {1:9.4f}'.format(vel, dt))
        else:                   # This is a direction measurement
            d = int.from_bytes(b[6:8], 'little')
            if dirCnt == 0:
                d0 = d
            if d - d0 > north / 2:
                d -= north
            if d0 -d > north / 2:
                d += north
            dirCnt += 1
            dirSum += d

            direction = int(offset + 360.0 * d / north) % 360
            print(time.ctime(t1) + ' {0:3d} deg - {1:6d}'.format(direction, int.from_bytes(b[6:8], 'little')))

    f.close()
    dir = (offset + int(360.0 * dirSum / dirCnt / north)) % 360
    if (initTime == 0) or (finalTime == 0):
        vel = 0
    else:
        vel = int(velCnt * 2.23 / (finalTime - initTime))

    print('Wind is {0:3d} mph at {1:3d} degrees'.format(vel, dir))
    time.sleep(1)
    subprocess.call(disconnectFromRPi)


if __name__ == '__main__':
    main()
