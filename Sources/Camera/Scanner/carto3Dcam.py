# -*- coding: utf-8 -*-
import callbacktasksynchronous as cb
import cameractrl as cam
import numpy


class Carto3D:
    def __init__(self, camcorr='', dev_name="Dev1", ch_name="ai0", data_nb=1000, rate=50000.0,
                 xOffset=4, video_ch=1, distance_marker=30, mtx=[], dist=[], undis=1, color_sensor='pink',
                 color_dir='yellow'):
        self.xPos = 0
        self.yPos = 0
        self.zVar = []
        self.xPosT = []
        self.yPosT = []
        self.zVarT = []
        self.zMean = []
        self.dev_name = dev_name
        self.ch_name = ch_name
        self.data_nb = data_nb
        self.rate = rate
        self.xOffset = xOffset
        self.video_ch = video_ch
        self.distance_marker = distance_marker
        self.mtx = mtx
        self.dist = dist
        self.camcorr = camcorr
        self.undis = undis
        self.msgcam = ''
        self.color_sensor = color_sensor
        self.color_dir = color_dir

        # Set the number of channel, depending on the type of ch_name
        if self.ch_name is None:
            self.ch_nb = 1
        elif type(self.ch_name) is list:
            self.ch_nb = len(self.ch_name)
        elif type(self.ch_name) is str:
            self.ch_nb = 1

    def startDAQTask(self):
        # Start DAQmx Task
        self.task = cb.CallbackTaskSynchronous(dev_name=self.dev_name, ch_name=self.ch_name, data_nb=self.data_nb,
                                               rate=self.rate)
        try:
            self.task.StartTask()
            self.msgcam = 'DAQ started'
        except:
            self.task.setIsRunning(False)

    def initCamera(self):
        self.camera = cam.Cameractrl(self.camcorr, self.video_ch, self.xOffset, self.distance_marker, self.ch_nb,
                                     self.mtx,
                                     self.dist, self.undis, self.color_sensor, self.color_dir)
        self.msgcam = 'Camera initialisation'

    def startCamera(self):
        self.camera.startCamera()
        self.msgcam = 'Camera started'

    def stopCamera(self):
        # if self.camera.getIsRunning():
        self.camera.stopCamera()
        self.msgcam = 'Camera stopped'

    def acquire3D(self):
        # Acquire camera position and data from the sensor
        while self.camera.getIsRunning() and self.task.getIsRunning():
            try:
                self.camera.grabFrame()
                self.camera.calcPos()
                self.xPos, self.yPos = self.camera.getPos()
                self.angle = self.camera.getAngle()
                print(self.angle)
                self.scale = self.camera.getScale()
                self.camera.displayImage()
                self.camera.waitForEscape()
                self.zVar = self.task.get_data(timeout=1.0)
                if self.zVar == []:
                    self.msgcam = 'DAQ device not started'
                    break
                self.idx = 0
                for self.idx in range(self.ch_nb):
                    self.xPosT.append(
                        self.xPos * self.scale + (self.idx - (self.ch_nb + 1) / 2) * self.xOffset * numpy.sin(
                            -self.angle))
                    self.yPosT.append(
                        self.yPos * self.scale + (self.idx - (self.ch_nb + 1) / 2) * self.xOffset * numpy.cos(
                            -self.angle))
                    self.zVar_t = numpy.mean(self.zVar[self.data_nb * (self.idx):self.data_nb * (self.idx + 1) - 1])
                    self.zVarT.append(self.zVar_t)
                time.sleep(0.01)
                self.msgcam = 'Camera running...'
            except:
                self.msgcam = 'No sensor detected'

    def acquireZData(self):
        try:
            self.zVar = self.task.get_data(timeout=1.0)
            self.idx = 0
            for self.idx in range(self.ch_nb):
                self.zVar_t = numpy.mean(self.zVar[self.data_nb * (self.idx):self.data_nb * (self.idx + 1) - 1])
                self.zVarT.append(self.zVar_t)
            if len(self.zVarT) <= self.ch_nb * 10 and self.zVar != []:
                self.acquireZData()
            elif self.zVar == []:
                self.msgcam = 'DAQ device not started'
            else:
                self.msgcam = 'Acquisition Done'
        except:
            self.msgcam = 'No sensor detected'

    def calibZData(self):
        self.idx = 0
        self.idx_ch = 0
        self.zMean_t = []
        for self.idx in range(self.ch_nb):
            self.zMean_t.insert(self.idx, [])
        for self.idx in range(len(self.zVarT) - 1):
            self.zMean_t[self.idx_ch].insert(len(self.zMean_t[self.idx_ch]), self.zVarT[self.idx])
            if self.idx_ch == self.ch_nb - 1:
                self.idx_ch = 0
            else:
                self.idx_ch = self.idx_ch + 1
        self.zMean = []
        for self.idx_ch in range(self.ch_nb):
            self.zMean.insert(self.idx_ch, numpy.mean(self.zMean_t[self.idx_ch]))

    def getZMean(self):
        return self.zMean

    def getZData(self):
        return self.zVarT

    def getCarto3D(self):
        return self.xPosT, self.yPosT, self.zVarT

    def getchnb(self):
        return self.ch_nb

    def getMsgCam(self):
        return self.msgcam

    def stopDAQTask(self):
        # Stop DAQmx Task and release the camera flow
        if self.task.getIsRunning():
            self.task.StopTask()
        self.task.ClearTask()
        self.msgcam = 'DAQ stopped'
