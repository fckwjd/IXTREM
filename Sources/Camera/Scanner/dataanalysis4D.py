# -*- coding: utf-8 -*-
import matplotlib
from matplotlib import cm
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.widgets import Cursor
import numpy as np
import scipy
from scipy import ndimage
from scipy.interpolate import griddata

from matplotlib.figure import Figure
from mpl_toolkits.mplot3d import axes3d, Axes3D


class DataAnalysis4D:
    def __init__(self, points4D=[[]], ch_nb=1, SDataMean=[]):
        # Initialize variables
        self.points4D = points4D
        self.ch_nb = ch_nb
        self.XPos_s = []
        self.YPos_s = []
        self.ZPos_s = []
        self.zOrd_s = []
        self.XPos_t = []
        self.YPos_t = []
        self.ZPos_t = []
        self.SData_t = []
        self.SDataMean = SDataMean
        self.idx = 0
        self.XPos = []
        self.YPos = []
        self.ZPos = []
        self.SData = []
        self.zOrd = []
        for self.idx in range(self.ch_nb):
            self.XPos_t.insert(self.idx, [])
            self.YPos_t.insert(self.idx, [])
            self.SData_t.insert(self.idx, [])

    def setData(self, points4D):
        '''Set the 4D (X,Y,Z,Data) points and arange it in separate arrays'''
        self.points4D = points4D
        self.XPos = self.points4D[:, :, 0].reshape(1, -1)
        self.YPos = self.points4D[:, :, 1].reshape(1, -1)
        self.ZPos = self.points4D[:, :, 2].reshape(1, -1)
        self.SData = self.points4D[:, :, 3].reshape(1, -1)
        self.XPos = self.XPos[0]
        self.YPos = self.YPos[0]
        self.ZPos = self.ZPos[0]
        self.SData = self.SData[0]

    def setChNb(self, ch_nb):
        '''Set the number of channels and create 4D points separated arrays arranged so that each column correspond to a channel'''
        self.ch_nb = ch_nb
        self.idx = 0
        for self.idx in range(self.ch_nb):
            self.XPos_t.insert(self.idx, [])
            self.YPos_t.insert(self.idx, [])
            self.ZPos_t.insert(self.idx, [])
            self.SData_t.insert(self.idx, [])

    def nDimArrays(self):
        '''Create N-Dim array for the N channel in order to be able to calibrate and perform calculations on each channel independently'''
        self.idx_ch = 0
        print(len(self.SData))
        for self.idx in range(len(self.SData)):
            self.XPos_t[self.idx_ch].insert(len(self.XPos_t[self.idx_ch]), self.XPos[self.idx])
            self.YPos_t[self.idx_ch].insert(len(self.YPos_t[self.idx_ch]), self.YPos[self.idx])
            self.ZPos_t[self.idx_ch].insert(len(self.ZPos_t[self.idx_ch]), self.ZPos[self.idx])
            self.SData_t[self.idx_ch].insert(len(self.SData_t[self.idx_ch]), self.SData[self.idx])
            if self.idx_ch == self.ch_nb - 1:
                self.idx_ch = 0
            else:
                self.idx_ch = self.idx_ch + 1
        return self.XPos_t, self.YPos_t, self.ZPos_t, self.SData_t

    def scaleSData(self):
        # Scale the sensor data
        self.SData = []
        self.XPos = []
        self.YPos = []
        self.ZPos = []
        self.idx = 0
        for self.idx in range(self.ch_nb):
            self.SDataMin = np.min(self.SData_t[self.idx])
            self.SDataMax = np.max(self.SData_t[self.idx])
            # Set the sensor data array around 0 in order to sort it
            self.SData = np.hstack((self.SData, self.SData_t[self.idx] - self.SDataMean[self.idx]))
            self.XPos = np.hstack((self.XPos, self.XPos_t[self.idx]))
            self.YPos = np.hstack((self.YPos, self.YPos_t[self.idx]))
            self.ZPos = np.hstack((self.ZPos, self.ZPos_t[self.idx]))
        print(self.SData)
        return self.XPos, self.XPos, self.ZPos, self.SData

    def sort3D(self):
        # Sort the sensor data array using absolute value
        self.SData_s_idx = sorted(range(len(self.SData)), key=lambda k: abs(self.SData[k]))
        self.SData_s = []
        self.idx = 0
        for self.idx in range(len(self.SData_s_idx)):
            self.SData_s.append(self.SData[self.SData_s_idx[self.idx]])
            # Create the sorted X and Y positions array as well as the zorder array to get the highest (abs intensity) value on top
        self.idx = 0
        for self.idx in range(len(self.SData_s)):
            self.XPos_s.append(self.XPos[self.SData_s_idx[self.idx]])
            self.YPos_s.append(self.YPos[self.SData_s_idx[self.idx]])
            self.ZPos_s.append(self.ZPos[self.SData_s_idx[self.idx]])
            self.zOrd_s.append(self.idx)

    def normalizeCmap(self):
        # Normalize the colormap
        self.SDataMin = np.min(self.SData_s)
        self.SDataMax = np.max(self.SData_s)
        if self.SDataMax > abs(self.SDataMin):
            self.SDataMin = -self.SDataMax
        else:
            self.SDataMax = -self.SDataMin
        self.cmap = cm.bwr
        self.norm = cm.colors.Normalize(vmax=self.SDataMax, vmin=self.SDataMin)

    def plotScatter(self, subScatt):
        # Plot the scatter data using a zorder array    
        self.idx = 0
        self.subScatt = subScatt
        # self.subScatt.cla()
        self.XPosMin = np.min(self.XPos_s)
        self.XPosMax = np.max(self.XPos_s)
        self.YPosMin = np.min(self.YPos_s)
        self.YPosMax = np.max(self.YPos_s)
        self.ZPosMin = np.min(self.ZPos_s)
        self.ZPosMax = np.max(self.ZPos_s)
        self.deltaX = self.XPosMax - self.XPosMin
        self.deltaY = self.YPosMax - self.YPosMin
        self.deltaZ = self.ZPosMax - self.ZPosMin
        if self.deltaX > self.deltaY:
            self.deltacorr = (self.deltaX - self.deltaY) / 2
            self.XPos_s = self.XPos_s - self.XPosMin
            self.YPos_s = self.YPos_s - self.YPosMin + self.deltacorr
        else:
            self.deltacorr = (self.deltaY - self.deltaX) / 2
            self.XPos_s = self.XPos_s - self.XPosMin + self.deltacorr
            self.YPos_s = self.YPos_s - self.YPosMin
        self.ZPos_s = self.ZPos_s - self.ZPosMin

        self.XPosMin = np.min(self.XPos_s)
        self.XPosMax = np.max(self.XPos_s)
        self.YPosMin = np.min(self.YPos_s)
        self.YPosMax = np.max(self.YPos_s)
        self.ZPosMin = np.min(self.ZPos_s)
        self.ZPosMax = np.max(self.ZPos_s)
        if self.XPosMin < self.YPosMin:
            self.YPosMin = self.XPosMin
        else:
            self.XPosMin = self.YPosMin
        if self.XPosMax > self.YPosMax:
            self.YPosMax = self.XPosMax
        else:
            self.XPosMax = self.YPosMax

        # self.subScatt.axis([self.XPosMin, self.XPosMax, self.YPosMin, self.YPosMax])

        dx = self.XPosMax
        trans_dx0 = self.subScatt.transData.transform((dx, 0))
        trans_dx1 = self.subScatt.transData.transform((0, 0))
        dx_in_points = ((trans_dx0[0] - trans_dx1[0])) / dx * 25 * 1
        for self.idx in range(len(self.SData_s)):
            self.zOrd = self.zOrd_s[self.idx]
            self.XPos = self.XPos_s[self.idx]
            self.YPos = self.YPos_s[self.idx]
            self.ZPos = self.ZPos_s[self.idx]
            self.SData = self.SData_s[self.idx]
            print(self.XPos, self.YPos, self.ZPos, self.SData, self.zOrd)
            self.subScatt.scatter(self.XPos, self.YPos, self.ZPos, c=self.SData,
                                  cmap=cm.get_cmap(self.cmap, len(self.SData_s) - 1),
                                  norm=self.norm, alpha=1, edgecolor='', zorder=self.zOrd, marker="s")
        # , s=dx_in_points,                                
        # self.cursorScatt = Cursor(self.subScatt, useblit=True, color='green', linewidth=1)

    # def plotInterp(self, subInterp):
    # #Plot the interpolated map
    # self.subInterp = subInterp
    # self.subInterp.cla()
    # self.grid_x, self.grid_y , self.grid_z= np.mgrid[self.XPosMin:self.XPosMax, self.YPosMin:self.YPosMax, self.ZPosMin:self.ZPosMax]
    # self.points = (self.XPos_s, self.YPos_s, self.ZPos_s)
    # #Interpolation of the data
    # self.grid_z1 = griddata(self.points, self.SData_s, (self.grid_x, self.grid_y, self.grid_z), method='linear', fill_value = 0.0)
    # self.grid_z1 = ndimage.interpolation.rotate(self.grid_z1,0)
    # self.subInterp.imshow(self.grid_z1.T,origin='lower', norm= self.norm, cmap = cm.get_cmap(self.cmap, len(self.SData_s)-1))
    # # self.subInterp.axis([self.XPosMin, self.XPosMax, self.YPosMin, self.YPosMax])
    # #Setup a cursor
    # self.cursorInterp = Cursor(self.subInterp, useblit=True, color='green', linewidth=1)

    def plotInterp(self, subInterp):
        # Plot the interpolated map
        self.subInterp = subInterp
        self.subInterp.cla()
        self.grid_x, self.grid_y = np.mgrid[self.XPosMin:self.XPosMax, self.YPosMin:self.YPosMax]
        self.points = (self.XPos_s, self.YPos_s)
        # Interpolation of the data
        self.grid_z1 = griddata(self.points, self.SData_s, (self.grid_x, self.grid_y), method='linear', fill_value=0.0)
        self.grid_z1 = ndimage.interpolation.rotate(self.grid_z1, 0)
        self.subInterp.imshow(self.grid_z1.T, origin='lower', norm=self.norm,
                              cmap=cm.get_cmap(self.cmap, len(self.SData_s) - 1))
        # self.subInterp.axis([self.xPosMin, self.xPosMax, self.yPosMin, self.yPosMax])
        # Setup a cursor
        self.cursorInterp = Cursor(self.subInterp, useblit=True, color='green', linewidth=1)

    def rotateInterp(self, angle):
        self.grid_z1 = ndimage.interpolation.rotate(self.grid_z1, angle)
        self.subInterp.imshow(self.grid_z1.T, origin='lower', norm=self.norm,
                              cmap=cm.get_cmap(self.cmap, len(self.SData_s) - 1))

    def saveData(self, fname):
        dataT = np.transpose(np.array((self.XPos_s, self.YPos_s, self.ZPos_s, self.SData_s)))
        fileObj = open(fname, mode='w')
        fileObj.write('X' + '\t' + 'Y' + '\t' + 'Z' + '\t' + 'Data' + '\n')
        if fileObj != None:
            for j in range(len(dataT) - 1):
                for l in range(2):
                    fileObj.write(str(dataT[j][l]) + '\t')
                fileObj.write(str(dataT[j][2]) + '\n')
        fileObj.close()

    # def getDataAtPoint(self, XPos, YPos, zPos):
    # X = int(round(XPos))
    # Y = int(round(YPos))
    # Z = int(round(zPos))
    # Xline = self.grid_z1[X,:]
    # for idx in range(len(Xline)):
    # if np.isnan(Xline[idx]):
    # Xline[idx] = 0
    # Yline = self.grid_z1[:,Y]
    # for idx in range(len(Yline)):
    # if np.isnan(Yline[idx]):
    # Yline[idx] = 0
    # Zline = self.grid_z1[:,Z]
    # for idx in range(len(Zline)):
    # if np.isnan(Zline[idx]):
    # Zline[idx] = 0
    # Data = self.grid_z1[X,Y]
    # if np.isnan(Data):
    # Data = 0
    # return Data, Xline, Yline, Zline

    def getDataAtPoint(self, xPos, yPos):
        X = int(round(xPos))
        Y = int(round(yPos))
        Xline = self.grid_z1[X, :]
        for idx in range(len(Xline)):
            if np.isnan(Xline[idx]):
                Xline[idx] = 0
        Yline = self.grid_z1[:, Y]
        for idx in range(len(Yline)):
            if np.isnan(Yline[idx]):
                Yline[idx] = 0
        Z = self.grid_z1[X, Y]
        if np.isnan(Z):
            Z = 0
        return Z, Xline, Yline

    def plotIntersec(self, Xline, Yline, subXFigCut, subYFigCut):
        X = np.linspace(self.XPosMin, self.XPosMax, len(Yline))
        subXFigCut.plot(X, Yline)
        subXFigCut.set_title('Horizontal cut')
        Y = np.linspace(self.YPosMin, self.YPosMax, len(Xline))
        subYFigCut.plot(Y, Xline)
        subYFigCut.set_title('Vertical cut')

    def plotShow(self):
        plt.show()
