#!/usr/bin/python3
'''Look at velocity distribution'''

fileName = 'Wind.bin'
arraySize = 60

def fetchRecord(file):
    recordLen = 8
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




def main():
    # Initialize hystogram
    a = [0]
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
                print(dt, v, vel)
    i = 0
    for t in a:
        print('{0:2d} mph  for {1:10.0f} sec'.format(i, t))
        i += 1


if __name__ == '__main__':
    main()
