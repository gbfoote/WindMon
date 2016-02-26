#!/usr/bin/python3
'''Read out Wind.bin file'''

import time

t0 = time.mktime((2016,1,1,0,0,0,0,0,0))
fileName = 'Wind.bin'

def main():
    f = open(fileName, 'rb')
    t0 = 1456519594.0
    while True:
        b = f.read(8)
        if len(b) < 8:
            break
        sec = int.from_bytes(b[0:4], 'little')
        ms = int.from_bytes(b[4:6], 'little')
        if (b[7]== 0x80):
            t1 = sec + ms/10000.0
            dt = t1-t0
            t0 = t1
            vel = int(2.0 / dt)
            print('pulse at   {0:10d}.{1:4d} sec - velocity = {2:3d} mph; dt = {3:9.4f}'.format(sec, ms, vel, dt))
        else:
            direction = int(360.0*int.from_bytes(b[6:8],'little')/26360.0)
            print('{2:3d} deg at {0:10d}.{1:4d} sec'.format(sec, ms, direction))




if __name__ == '__main__':
    main()
