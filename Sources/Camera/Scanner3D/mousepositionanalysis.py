# -*- coding: utf-8 -*-
import matplotlib
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
import numpy
import scipy
from scipy import ndimage
from scipy.interpolate import griddata


class MousePosAnalysis:
    def __init__(self, xPosT=[], yPosT=[], zVarT=[], zMean=[], ch_nb=1):
        # Initialize variables
        self.xPosT = xPosT
        self.yPosT = yPosT
        self.zVarT = zVarT
        self.ch_nb = ch_nb
        self.xPos_s = []
        self.yPos_s = []
        self.zOrd_s = []
        # self.fig = plt.figure()
        self.xPos_m = []
        self.yPos_m = []
        self.zVar_m = []
        self.zMean = zMean
        self.idx = 0
        self.xPos = []
        self.yPos = []
        self.zVar = []
        self.zOrd = []
        for self.idx in range(self.ch_nb):
            self.xPos_m.insert(self.idx, [])
            self.yPos_m.insert(self.idx, [])
            self.zVar_m.insert(self.idx, [])

    def setData(self, xPos, yPos, zVar):
        self.xPosT = xPos
        self.yPosT = yPos
        self.zVarT = zVar

    def setChNb(self, ch_nb):
        self.ch_nb = ch_nb
        self.idx = 0
        for self.idx in range(self.ch_nb):
            self.xPos_m.insert(self.idx, [])
            self.yPos_m.insert(self.idx, [])
            self.zVar_m.insert(self.idx, [])

    def nDimArrays(self):
        self.idx_ch = 0
        # Create N-Dim array for the N channel in order to be able to calibrate and perform calculations on each channel independently
        for self.idx in range(len(self.zVarT)):
            self.zVar_m[self.idx_ch].insert(len(self.zVar_m[self.idx_ch]), self.zVarT[self.idx])
            self.xPos_m[self.idx_ch].insert(len(self.xPos_m[self.idx_ch]), self.xPosT[self.idx])
            self.yPos_m[self.idx_ch].insert(len(self.yPos_m[self.idx_ch]), self.yPosT[self.idx])
            if self.idx_ch == self.ch_nb - 1:
                self.idx_ch = 0
            else:
                self.idx_ch = self.idx_ch + 1
        return self.xPos_m, self.yPos_m, self.zVar_m

    def scalezVar(self):
        # Scale the sensor data
        self.zVar = []
        self.xPos = []
        self.yPos = []
        self.idx = 0
        for self.idx in range(self.ch_nb):
            self.zMin = numpy.min(self.zVar_m[self.idx])
            self.zMax = numpy.max(self.zVar_m[self.idx])
            # Set the sensor data array around 0 in order to sort it
            self.zVar = numpy.hstack((self.zVar, self.zVar_m[self.idx] - self.zMean[self.idx]))
            self.xPos = numpy.hstack((self.xPos, self.xPos_m[self.idx]))
            self.yPos = numpy.hstack((self.yPos, self.yPos_m[self.idx]))
        return self.xPos, self.yPos, self.zVar

    def sort3D(self):
        # Sort the sensor data array using absolute value
        self.zVar_s_idx = sorted(range(len(self.zVar)), key=lambda k: abs(self.zVar[k]))
        self.zVar_s = []
        self.idx = 0
        for self.idx in range(len(self.zVar_s_idx)):
            self.zVar_s.append(self.zVar[self.zVar_s_idx[self.idx]])
            # Create the sorted X and Y positions array as well as the zorder array to get the highest (abs intensity) value on top
        self.idx = 0
        for self.idx in range(len(self.zVar_s)):
            self.xPos_s.append(self.xPos[self.zVar_s_idx[self.idx]])
            self.yPos_s.append(self.yPos[self.zVar_s_idx[self.idx]])
            self.zOrd_s.append(self.idx)

    def normalizeCmap(self):
        # Normalize the colormap
        self.zMin = numpy.min(self.zVar_s)
        self.zMax = numpy.max(self.zVar_s)
        if self.zMax > abs(self.zMin):
            self.zMin = -self.zMax
        else:
            self.zMax = -self.zMin
        self.cmap = cm.bwr
        self.norm = cm.colors.Normalize(vmax=self.zMax, vmin=self.zMin)

    def plotScatter(self, subScatt):
        # Plot the scatter data using a zorder array    
        self.idx = 0
        self.subScatt = subScatt
        self.subScatt.cla()
        self.xPosMin = numpy.min(self.xPos_s)
        self.xPosMax = numpy.max(self.xPos_s)
        self.yPosMin = numpy.min(self.yPos_s)
        self.yPosMax = numpy.max(self.yPos_s)
        self.deltaX = self.xPosMax - self.xPosMin
        self.deltaY = self.yPosMax - self.yPosMin
        if self.deltaX > self.deltaY:
            self.deltacorr = (self.deltaX - self.deltaY) / 2
            self.xPos_s = self.xPos_s - self.xPosMin
            self.yPos_s = self.yPos_s - self.yPosMin + self.deltacorr
        else:
            self.deltacorr = (self.deltaY - self.deltaX) / 2
            self.xPos_s = self.xPos_s - self.xPosMin + self.deltacorr
            self.yPos_s = self.yPos_s - self.yPosMin

        self.xPosMin = numpy.min(self.xPos_s)
        self.xPosMax = numpy.max(self.xPos_s)
        self.yPosMin = numpy.min(self.yPos_s)
        self.yPosMax = numpy.max(self.yPos_s)
        if self.xPosMin < self.yPosMin:
            self.yPosMin = self.xPosMin
        else:
            self.xPosMin = self.yPosMin
        if self.xPosMax > self.yPosMax:
            self.yPosMax = self.xPosMax
        else:
            self.xPosMax = self.yPosMax

        self.subScatt.axis([self.xPosMin, self.xPosMax, self.yPosMin, self.yPosMax])

        dx = self.xPosMax
        trans_dx0 = self.subScatt.transData.transform((dx, 0))
        trans_dx1 = self.subScatt.transData.transform((0, 0))
        dx_in_points = ((trans_dx0[0] - trans_dx1[0])) / dx * 25 * 1
        for self.idx in range(len(self.zVar_s)):
            self.zOrd = self.zOrd_s[self.idx]
            self.xPos = self.xPos_s[self.idx]
            self.yPos = self.yPos_s[self.idx]
            self.zVar = self.zVar_s[self.idx]
            self.subScatt.scatter(self.xPos, self.yPos, s=dx_in_points, c=self.zVar,
                                  cmap=cm.get_cmap(self.cmap, len(self.zVar_s) - 1),
                                  norm=self.norm, alpha=1, edgecolor='', zorder=self.zOrd, marker="s")
            # self.cursorScatt = Cursor(self.subScatt, useblit=True, color='green', linewidth=1)

    def plotInterp(self, subInterp):
        # Plot the interpolated map
        self.subInterp = subInterp
        self.subInterp.cla()
        self.grid_x, self.grid_y = numpy.mgrid[self.xPosMin:self.xPosMax, self.yPosMin:self.yPosMax]
        self.points = (self.xPos_s, self.yPos_s)
        # Interpolation of the data
        self.grid_z1 = griddata(self.points, self.zVar_s, (self.grid_x, self.grid_y), method='linear', fill_value=0.0)
        self.grid_z1 = ndimage.interpolation.rotate(self.grid_z1, 0)
        self.subInterp.imshow(self.grid_z1.T, origin='lower', norm=self.norm,
                              cmap=cm.get_cmap(self.cmap, len(self.zVar_s) - 1))
        # self.subInterp.axis([self.xPosMin, self.xPosMax, self.yPosMin, self.yPosMax])
        # Setup a cursor
        self.cursorInterp = Cursor(self.subInterp, useblit=True, color='green', linewidth=1)

    def rotateInterp(self, angle):
        self.grid_z1 = ndimage.interpolation.rotate(self.grid_z1, angle)
        self.subInterp.imshow(self.grid_z1.T, origin='lower', norm=self.norm,
                              cmap=cm.get_cmap(self.cmap, len(self.zVar_s) - 1))

    def saveData(self, fname):
        dataT = numpy.transpose(numpy.array((self.xPos_s, self.yPos_s, self.zVar_s)))
        fileObj = open(fname, mode='w')
        fileObj.write('X' + '\t' + 'Y' + '\t' + 'Data' + '\n')
        if fileObj != None:
            for j in range(len(dataT) - 1):
                for l in range(2):
                    fileObj.write(str(dataT[j][l]) + '\t')
                fileObj.write(str(dataT[j][2]) + '\n')
        fileObj.close()

    def getDataAtPoint(self, xPos, yPos):
        X = int(round(xPos))
        Y = int(round(yPos))
        Xline = self.grid_z1[X, :]
        for idx in range(len(Xline)):
            if numpy.isnan(Xline[idx]):
                Xline[idx] = 0
        Yline = self.grid_z1[:, Y]
        for idx in range(len(Yline)):
            if numpy.isnan(Yline[idx]):
                Yline[idx] = 0
        Z = self.grid_z1[X, Y]
        if numpy.isnan(Z):
            Z = 0
        return Z, Xline, Yline

    def plotIntersec(self, Xline, Yline, subXFigCut, subYFigCut):
        X = numpy.linspace(self.xPosMin, self.xPosMax, len(Yline))
        subXFigCut.plot(X, Yline)
        subXFigCut.set_title('Horizontal cut')
        Y = numpy.linspace(self.yPosMin, self.yPosMax, len(Xline))
        subYFigCut.plot(Y, Xline)
        subYFigCut.set_title('Vertical cut')

    def plotShow(self):
        plt.show()
