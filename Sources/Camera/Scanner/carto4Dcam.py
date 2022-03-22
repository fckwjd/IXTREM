# -*- coding: utf-8 -*-
import callbacktasksynchronous as cb
import camera3Dchessboard as cam
import numpy as np
import cv2
import time


class Carto4D:
    def __init__(self, camcorr='', dev_name="Dev1", ch_name="ai0", data_nb=1000, rate=50000.0, video_ch=1,
                 distance_marker=30, mtx=[], dist=[],
                 undis=1, board_h=8, board_w=7, size=25,
                 folder='C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Sources\\Camera\\Scanner\\chessboard\\'):
        self.camcorr = camcorr
        self.dev_name = dev_name
        self.ch_name = ch_name
        self.data_nb = data_nb
        self.rate = rate
        self.video_ch = video_ch
        self.distance_marker = distance_marker
        self.mtx = mtx
        self.dist = dist
        self.undis = undis
        self.board_h = board_h
        self.board_w = board_w
        self.size = size
        self.folder = folder
        self.SData = []
        self.SDataMean = []
        self.points4D = [[[]]]
        self.msgcam = ''
        self.points3D = []

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
        self.camera = cam.Cameractrl3D(self.camcorr, self.video_ch, self.distance_marker, self.mtx, self.dist,
                                       self.undis, self.board_h, self.board_w, self.size, self.folder)
        self.msgcam = 'Camera initialisation'

    def startCamera(self):
        self.camera.startCamera()
        self.msgcam = 'Camera started'

    def stopCamera(self):
        # if self.camera.getIsRunning():
        self.camera.stopCamera()
        self.msgcam = 'Camera stopped'

    def acquire4D(self):
        # Acquire camera position and data from the sensor
        while self.camera.getIsRunning() and self.task.getIsRunning():
            try:
                self.frame = self.camera.grabFrame()
                self.points3D = self.camera.getPos3D(True, False)
                self.camera.displayImage()
                self.camera.waitForEscape()
                self.acquireSData()
                if self.points3D is not None:
                    if type(self.points3D) is list:
                        self.points3D = np.array(self.points3D)
                    else:
                        self.points3D = np.array(self.points3D.tolist())
                    self.points3D = np.insert(self.points3D.T, np.shape(self.points3D)[2], self.SData, axis=0).T
                    if np.shape(self.points4D) == (1, 1, 0):
                        self.points4D = self.points3D.copy()
                    else:
                        self.points4D = np.insert(self.points4D, np.shape(self.points4D)[0], self.points3D, axis=0)
                time.sleep(0.01)
                self.msgcam = 'Camera running...'
            except:
                self.msgcam = 'No sensor detected'

    def acquireSData(self):
        try:
            self.SDataRaw = self.task.get_data(timeout=1.0)
            self.SData = []
            self.SData_t = 0
            self.idx = 0
            for self.idx in range(self.ch_nb):
                self.SData_t = np.mean(self.SDataRaw[self.data_nb * (self.idx):self.data_nb * (self.idx + 1) - 1])
                self.SData.append(self.SData_t)
            if len(self.SData) < self.ch_nb * 1 and self.SDataRaw != []:
                self.acquireSData()
            elif self.SDataRaw == []:
                self.msgcam = 'DAQ device not started'
            else:
                self.msgcam = 'Acquisition Done'
                self.SData = np.array(self.SData).reshape((1, 4, 1))
        except:
            self.msgcam = 'No sensor detected'

    def calibSData(self):
        self.idx = 0
        self.idx_ch = 0
        self.SDataMean_t = []
        for self.idx in range(self.ch_nb):
            self.SDataMean_t.insert(self.idx, [])
        for self.idx in range(len(self.SData[0])):
            self.SDataMean_t[self.idx_ch].insert(len(self.SDataMean_t[self.idx_ch]), self.SData[0][self.idx][0])
            if self.idx_ch == self.ch_nb - 1:
                self.idx_ch = 0
            else:
                self.idx_ch = self.idx_ch + 1
        self.SDataMean = []
        for self.idx_ch in range(self.ch_nb):
            self.SDataMean.insert(self.idx_ch, np.mean(self.SDataMean_t[self.idx_ch]))

    def getSDataMean(self):
        return self.SDataMean

    def getSData(self):
        return self.SData

    def getCarto4D(self):
        return self.points4D

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
