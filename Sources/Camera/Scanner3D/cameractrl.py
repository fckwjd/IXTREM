# -*- coding: utf-8 -*-
import cv2
import numpy as np


# import numpy.zeros_like as zeros_like
# import numpy.array as array


class Cameractrl():
    '''Control the Camera, calculate the position, mouvement, angle and scaling'''

    def __init__(self, camcorr, video_ch=1, xOffset=4, distance_marker=30, ch_nb=4,
                 mtx=[], dist=[], undis=1, color_chc='pink', color_chc_dir='yellow'):
        self.color_chc = color_chc
        self.color_chc_dir = color_chc_dir
        self.xPosT = []
        self.yPosT = []
        self.ch_nb = ch_nb
        self.xOffset = xOffset
        self.xPos = []
        self.yPos = []
        self.distance_marker = distance_marker
        self.isrunning = False
        self.video_ch = video_ch
        self.mtx = mtx
        self.dist = dist
        self.camcorr = camcorr
        self.undis = undis

    def startCamera(self):
        '''Start the camera'''
        self.cap = cv2.VideoCapture(self.video_ch)
        self.ret, self.old_frame = self.cap.read()
        if self.undis == 1:
            if self.mtx != [] or self.dist != []:
                self.old_frame = self.camcorr.undistortImage(self.old_frame, self.mtx, self.dist)
        self.mask_old = np.zeros_like(self.old_frame)
        self.isrunning = True

    def CannyDetec(self, img, color_chc, ths, minEdge, maxEdge):
        '''Detection in the image of the contour of objects with the color chosen'''
        # Convert BGR to HSV
        self.img = img
        self.color_chc_canny = color_chc
        self.ths = ths
        self.minEdge = minEdge
        self.maxEdge = maxEdge
        self.hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)

        # define range of colors in HSV   
        if self.color_chc_canny == 'blue':
            self.lower = np.array([85, 50, 50])
            self.upper = np.array([145, 255, 255])
        if self.color_chc_canny == 'red':
            self.lower1 = np.array([170, 50, 50])
            self.upper1 = np.array([179, 255, 255])
            self.lower2 = np.array([0, 100, 100])
            self.upper2 = np.array([20, 255, 255])
        if self.color_chc_canny == 'orange':
            self.lower = np.array([10, 50, 50])
            self.upper = np.array([25, 255, 255])
        if self.color_chc_canny == 'green':
            self.lower = np.array([40, 50, 50])
            self.upper = np.array([85, 255, 255])
        if self.color_chc_canny == 'yellow':
            self.lower = np.array([30, 60, 70])
            self.upper = np.array([102, 255, 255])
        if self.color_chc_canny == 'pink':
            self.lower = np.array([130, 75, 75])
            self.upper = np.array([170, 255, 255])
        if color_chc == 'white':
            lower = np.array([0, 0, 100])
            upper = np.array([179, 255, 255])
        if color_chc == 'black':
            lower = np.array([0, 0, 0])
            upper = np.array([179, 255, 30])

        # Threshold the HSV image to get only chosen colors
        if self.color_chc_canny == 'red':
            self.mask = cv2.inRange(self.hsv, self.lower1, self.upper1)
            self.mask2 = cv2.inRange(self.hsv, self.lower2, self.upper2)
            self.mask = cv2.add(self.mask, self.mask2)
        else:
            self.mask = cv2.inRange(self.hsv, self.lower, self.upper)
        self.kernel = np.ones((self.ths, self.ths), np.uint8)

        # Bitwise-AND mask and original image: the pixels different from mask color set to 0 (black)
        self.res = cv2.bitwise_and(self.img, self.img, mask=self.mask)

        # Threshold the image to get black and white image
        self.res = np.uint8(self.res / 2.)
        self.res = cv2.cvtColor(self.res, cv2.COLOR_HSV2BGR)
        self.res = cv2.cvtColor(self.res, cv2.COLOR_BGR2GRAY)
        self.rest, self.res = cv2.threshold(self.res, 1, 255, 0)

        # Find the edges on the binary image
        self.edge = cv2.Canny(self.res, self.minEdge, self.maxEdge, apertureSize=5)

        # Find the contours on the binary image
        self.image, self.contours, self.hierarchy = cv2.findContours(self.res, cv2.RETR_EXTERNAL,
                                                                     cv2.CHAIN_APPROX_SIMPLE)

        return self.contours

    def stopCamera(self):
        '''Stop the camera'''
        # Destroy windows, close the app
        cv2.destroyAllWindows()
        self.cap.release()
        self.isrunning = False

    def grabFrame(self):
        '''Grab, correct and search for colored objects'''
        # Recalculate an empty mask
        self.mask_old = np.zeros_like(self.old_frame)

        # Take each frame
        _, self.frame = self.cap.read()
        if self.undis == 1:
            if self.mtx != [] or self.dist != []:
                self.frame = self.camcorr.undistortImage(self.frame, self.mtx, self.dist)

        # Display the recomposed image
        self.contours_r = self.CannyDetec(self.frame, self.color_chc, 2, 1000, 5000)

        # Display the recomposed image
        self.contours_b = self.CannyDetec(self.frame, self.color_chc_dir, 2, 1000, 5000)

        return self.contours_r, self.contours_b

    def calcPos(self):
        '''Calculate the positions of the colored objects, the angle of orientation and the scaling of the image, draw the position already checked'''
        if len(self.contours_b) > 0 and len(self.contours_r) > 0:
            # First contour area
            self.idx = 0
            for self.idx in range(len(self.contours_b)):
                self.cnt_b = self.contours_b[self.idx]
                self.area = cv2.contourArea(self.cnt_b)
                self.M = cv2.moments(self.cnt_b)
                if self.area > 1000 and self.area < 50000:
                    try:
                        self.rect_b = cv2.minAreaRect(self.cnt_b)
                        self.box_b = cv2.boxPoints(self.rect_b)
                        self.box_b = np.int0(self.box_b)
                        cv2.drawContours(self.mask_old, [self.box_b], -1, (0, 255, 255), -1, maxLevel=0)
                    except:
                        None
                    cv2.drawContours(self.mask_old, self.contours_b, self.idx, (0, 255, 255), 1)
                    self.cx_dir = int(self.M['m10'] / self.M['m00'])
                    self.cy_dir = int(self.M['m01'] / self.M['m00'])

                    # Second contour area
            self.idx = 0
            self.M = 0
            for self.idx in range(len(self.contours_r)):
                self.cnt_r = self.contours_r[self.idx]
                self.area = cv2.contourArea(self.cnt_r)
                self.M = cv2.moments(self.cnt_r)
                if self.area > 200:
                    try:
                        self.rect = cv2.minAreaRect(self.cnt_r)
                        self.box = cv2.boxPoints(self.rect)
                        self.box = np.int0(self.box)
                        cv2.drawContours(self.mask_old, [self.box], -1, (255, 0, 255), -1, maxLevel=0)
                        self.cx = int(self.M['m10'] / self.M['m00'])
                        self.cy = int(self.M['m01'] / self.M['m00'])
                        cv2.circle(self.mask_old, (self.cx, self.cy), 1, (0, 255, 0), 1)

                        if len(self.yPos) > 0:
                            if (np.abs(self.cx - self.xPos[len(self.xPos) - 1]) >= 1 or np.abs(
                                    self.cy - self.yPos[len(self.yPos) - 1]) >= 1):
                                self.distance = np.sqrt((self.cx_dir - self.cx) ** 2 + (self.cy_dir - self.cy) ** 2)
                                self.angle = np.arctan2(self.cy_dir - self.cy, self.cx_dir - self.cx)
                                self.scale = self.distance_marker / self.distance
                                self.xPos.append(self.cx)
                                self.yPos.append(self.cy)
                            idx2 = 0
                            for idx2 in range(len(self.xPos)):
                                cv2.circle(self.mask_old, (self.xPos[idx2], self.yPos[idx2]), 1, (255, 255, 0), 1)
                        else:
                            self.distance = np.sqrt((self.cx_dir - self.cx) ** 2 + (self.cy_dir - self.cy) ** 2)
                            self.angle = np.arctan2(self.cy_dir - self.cy, self.cx_dir - self.cx)
                            self.scale = self.distance_marker / self.distance
                            self.xPos.append(self.cx)
                            self.yPos.append(self.cy)
                    except:
                        None
        else:
            if len(self.xPos) > 0:
                idx2 = 0
                for idx2 in range(len(self.xPos)):
                    cv2.circle(self.mask_old, (self.xPos[idx2], self.yPos[idx2]), 1, (255, 255, 0), 1)

    def getPos(self):
        '''Get the position'''
        return self.cx, self.cy

    def getAngle(self):
        '''Get the angle'''
        return self.angle

    def getScale(self):
        '''Get the scaling factor'''
        return self.scale

    def displayImage(self):
        '''Display the image'''
        self.img = cv2.add(self.frame, self.mask_old)
        cv2.imshow('img', self.img)
        cv2.moveWindow('img', 100, 200)

    def setIsRunning(self, isrunning):
        '''Set setIsRunning to check if the app is running'''
        self.isrunning = isrunning

    def getIsRunning(self):
        '''Get getIsRunning to check if the app is running'''
        return self.isrunning

    def waitForEscape(self):
        '''Check if Esc. key has been pressed to escape the app'''
        # Wait for a key pressed
        self.k = cv2.waitKey(10) & 0xFF
        # Esc. pressed, quit app
        if self.k == 27:
            self.isrunning = False
            return self.isrunning
