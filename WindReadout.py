#!/usr/bin/python3
'''PySide widget to display wind velocity and direction'''

import sys, threading, time,subprocess
from PySide import QtGui, QtCore


connectToRPi = ['sshfs', '10.11.2.189:/home/gbf/WindMon', '/home/gbf/repos/WindMon/rpi']
disconnectFromRPi = ['fusermount', '-u', '/home/gbf/repos/WindMon/rpi']
statusAlive = threading.Event()
interval = 5    # Interval in seconds between data samples

class Form(QtGui.QDialog):

    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.speedLabel=QtGui.QLabel()
        self.speedLabel.setText('Speed')
        self.directionLabel = QtGui.QLabel()
        self.directionLabel.setText('Direction')
        self.speedValue = QtGui.QLabel()
        self.directionValue = QtGui.QLabel()

        frame = QtGui.QGridLayout()
        frame.addWidget(self.speedLabel, 0, 0)
        frame.addWidget(self.directionLabel, 0, 1)
        frame.addWidget(self.speedValue, 1, 0)
        frame.addWidget(self.directionValue, 1, 1)
        self.setLayout(frame)


        self.anemometer = dataSource()

        self.anemometer.vUpdate.connect(self.speedValue.setText)
        self.anemometer.dUpdate.connect(self.directionValue.setText)


        source = threading.Thread(target=self.windData)
        statusAlive.set()
        source.start()

    def fetchDataOld(self):
        # t0 = time.mktime((2016,1,1,0,0,0,0,0,0))
        fileName = '/home/gbf/repos/WindMon/rpi/Wind.bin'
        dirCnt = 0
        velCnt = 0
        dirSum = 0
        dispLen = 80
        dataLen = 8
        north = 26360   # raw a/d
        offset = 255    # deg

        try:
            f = open(fileName, 'rb')
        except FileNotFoundError:
            subprocess.call(connectToRPi)
            f = open(fileName, 'rb')
        f.seek(-dataLen * dispLen, 2)

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
        f.close()
        dir = (offset + int(360.0 * dirSum / dirCnt / north)) % 360
        if (initTime == 0) or (finalTime == 0):
            vel = 0
        else:
            vel = int((velCnt-1) * 2.23 / (finalTime - initTime))
        return (vel, dir)

    def fetchData(self):
        # t0 = time.mktime((2016,1,1,0,0,0,0,0,0))
        fileName = '/home/gbf/repos/WindMon/rpi/Wind.txt'
        #dirCnt = 0
        #velCnt = 0
        dirSum = 0
        dispLen = 80
        dataLen = 8
        north = 26360   # raw a/d
        offset = 255    # deg
        noReadings = 5
        lineLength = 23

        try:
            f = open(fileName, 'r')
        except FileNotFoundError:
            subprocess.call(connectToRPi)
            f = open(fileName, 'r')
        f.seek(0, 2)
        pos = f.tell()
        f.seek(pos - noReadings*lineLength, 0)
        lines = f.readlines()
        f.close()
        n = len(lines)
        lines = lines[n - noReadings:]
        data = []
        for l in lines:
            l = l[:-1].split(',')
            d = []
            for i in l:
                d.append(int(i))
            data.append(d)
        sumDir = 0
        sumVel = 0
        for reading in data:
            sumVel += reading[2]
            d = reading[1]
            if sumDir == 0:
                d0 = d
            if d - d0 > north / 2:
                d -= north
            if d0 -d > north / 2:
                d += north
            sumDir += d

        dir = (offset + int(360.0 * sumDir / noReadings / north)) % 360
        vel = int(sumVel * 2.33 /noReadings)
        return (vel, dir)




    def windData(self):
        while True:
            (v, d) = self.fetchData()
            vel = '{0:3d} mph'.format(v)
            direction = '{0:3d} deg'.format(d)
            self.anemometer.vUpdate.emit(vel)
            self.anemometer.dUpdate.emit(direction)
            if not statusAlive.is_set():
                break
            time.sleep(interval)



class dataSource(QtCore.QObject):
     vUpdate = QtCore.Signal(str)
     dUpdate = QtCore.Signal(str)

     def __init__(self):
         super(dataSource, self).__init__()

def main():
    app = QtGui.QApplication(sys.argv)
    subprocess.call(connectToRPi)   # Mount RPi on local system
    window = Form()
    window.setWindowTitle('Wind Conditions')
    window.show()
    app.exec_()
    statusAlive.clear()
    time.sleep(int(1.2 * interval))                  # Stop fetching wind data
    subprocess.call(disconnectFromRPi)   # Un-mount RPi on local system



if __name__ == '__main__':
    main()
