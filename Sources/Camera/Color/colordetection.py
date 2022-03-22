# -*- coding: utf-8 -*-
import cv2
import numpy as np


class ColorDetection:
    def __init__(self, color_chc='green', ths=2, minEdge=1000, maxEdge=5000,
                 colorcontour=(0, 255, 255), sizecontour=1, arealimits=[1000, 50000], maxV=200):
        self.color_chc = color_chc
        self.colorRange()
        self.ths = ths
        self.minEdge = minEdge
        self.maxEdge = maxEdge
        self.meanarray = []
        self.colorcontour = colorcontour
        self.sizecontour = sizecontour
        self.arealimits = arealimits
        self.maxV = maxV
        self.centerspot = (0, 0)

    def createEmptyMask(self):
        self.mask = np.zeros_like(self.frame)
        return self.mask

    def setFrame(self, frame):
        self.frame = frame
        self.hsv = cv2.cvtColor(self.frame, cv2.COLOR_BGR2HSV)

    def findMaxSatContour(self, idx):
        self.hsv2 = self.hsv.copy()
        h, s, v = cv2.split(self.hsv2)
        mask = np.zeros_like(v)
        cv2.drawContours(mask, self.contours, idx, 255, -1)
        v[mask == 0] = 0
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(v, mask=mask)
        return max_val

    def colorRange(self):
        # define range of colors in HSV 
        self.ranges = {'blue': np.array([[100, 50, 50], [115, 255, 255]]),
                       'red': np.array([[130, 100, 100], [179, 255, 255], [0, 100, 100], [10, 255, 255]]),
                       'green': np.array([[40, 40, 40], [85, 255, 255]]),
                       'white': np.array([[0, 0, 255], [179, 0, 255]]),
                       'yellow': np.array([[30, 75, 75], [35, 255, 255]]),
                       'pink': np.array([[130, 75, 75], [179, 255, 255]])}
        self.colorrange = self.ranges[self.color_chc]
        return self.colorrange

    def CannyDetec(self):
        # Threshold the HSV image to get only chosen colors        
        if self.color_chc == 'red':
            self.maskrange = cv2.inRange(self.hsv, self.colorrange[0], self.colorrange[1])
            self.maskrange2 = cv2.inRange(self.hsv, self.colorrange[2], self.colorrange[3])
            self.maskrange = cv2.add(self.maskrange, self.maskrange2)
        else:
            self.maskrange = cv2.inRange(self.hsv, self.colorrange[0], self.colorrange[1])

        self.kernel = np.ones((self.ths, self.ths), np.uint8)

        # Bitwise-AND mask and original image: the pixels different from mask color set to 0 (black)
        self.res = cv2.bitwise_and(self.frame, self.frame, mask=self.maskrange)

        # Threshold the image to get black and white image
        self.res = np.uint8(self.res / 2.)
        self.res = cv2.cvtColor(self.res, cv2.COLOR_HSV2BGR)
        self.res = cv2.cvtColor(self.res, cv2.COLOR_BGR2GRAY)
        self.rest, self.res = cv2.threshold(self.res, 1, 255, 0)

        # Find the edges on the binary image
        self.edge = cv2.Canny(self.res, self.minEdge, self.maxEdge, apertureSize=3)

        # Find the contours on the binary image
        self.image, self.contours, self.hierarchy = cv2.findContours(self.res, cv2.RETR_EXTERNAL,
                                                                     cv2.CHAIN_APPROX_SIMPLE)

        return self.image, self.contours, self.hierarchy

    def drawContourCircle(self):
        self.mask_temp = self.mask
        if len(self.contours) > 0:
            for idx in range(len(self.contours)):
                self.cnt = self.contours[idx]
                self.area = cv2.contourArea(self.cnt)
                self.M = cv2.moments(self.cnt)
                (self.x, self.y), self.radius = cv2.minEnclosingCircle(self.cnt)
                self.center = (int(self.x), int(self.y))
                self.arearad = np.pi * self.radius * self.radius
                if self.area > self.arealimits[0] and self.area < self.arealimits[1]:
                    self.cx = int(self.M['m10'] / self.M['m00'])
                    self.cy = int(self.M['m01'] / self.M['m00'])
                    if abs(self.cx - self.center[0]) < self.cx * 0.01 and abs(self.cy - self.center[1]) < cy * 0.01:
                        if self.area > 0.4 * arearad and self.area < 1.6 * arearad:
                            cv2.drawContours(self.mask_temp, self.contours, idx, self.colorcontour, self.sizecontour)
                            cv2.circle(self.mask_temp, self.center, int(self.radius), self.colorcontour,
                                       self.sizecontour)
                            if len(self.meanarray) == 0 or len(self.meanarray) == None:
                                self.meanarray = [arearad]
                            elif len(self.meanarray) <= 20:
                                self.meanarray = np.append(self.meanarray, arearad)
                            elif len(self.meanarray) > 20:
                                self.meanarray = np.delete(self.meanarray, 0)
                                self.meanarray = np.append(self.meanarray, arearad)
                            print(np.mean(self.meanarray))
        return self.mask_temp

    def drawContour(self):
        self.mask_temp = self.mask.copy()
        if len(self.contours) > 0:
            for idx in range(len(self.contours)):
                self.cnt = self.contours[idx]
                self.area = cv2.contourArea(self.cnt)
                self.M = cv2.moments(self.cnt)
                (self.x, self.y), self.radius = cv2.minEnclosingCircle(self.cnt)
                self.center = (int(self.x), int(self.y))
                if self.area > 0:
                    self.cx = int(self.M['m10'] / self.M['m00'])
                    self.cy = int(self.M['m01'] / self.M['m00'])
                    self.max_val = self.findMaxSatContour(idx)
                    if self.max_val > self.maxV:
                        cv2.drawContours(self.mask_temp, self.contours, idx, self.colorcontour, self.sizecontour)
                        cv2.circle(self.mask_temp, self.center, int(self.radius), self.colorcontour, self.sizecontour)
                        self.centerspot = self.center
        return self.mask_temp, self.centerspot
