#!/usr/bin/env python

'''
Simple Multithreaded video .
Usage:
   Simple theaded video stream, serve as a base for more complex live video
   code
Keyboard shortcuts:
   ESC - exit
   c - start and stop the clock
   p - save image
'''

# Python 2/3 compatibility
from __future__ import print_function
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    xrange = range

import numpy as np
import cv2
from multiprocessing.pool import ThreadPool
from collections import deque
import colorbox as cb
from common import draw_str, StatValue
import cameraundistort as cu
import chessboard3D as chb
from os import getcwd


# import mossedetection as mosse

class App:
    def __init__(self, video_src, board_h, board_w, size):
        # folder = os.path.dirname(os.path.realpath(__file__)) + 'chessboard\\'
        self.points3D = []
        folder = getcwd() + '\\chessboard\\'
        self.cap, self.isrunning = self.startCamera(video_src=0, width=1280, height=720, brightness=8, contrast=20,
                                                    saturation=60)
        self.camcorr = cu.CameraUndistort(folder, board_h, board_w, size)
        self.mtx, self.dist = self.camcorr.calibrate()
        self.chess = chb.Chessboard3D(self.mtx, self.dist, board_h, board_w, size, folder)
        self.frame = self.grabImage(self.cap)

        # self.frame = self.imageCorr(self.camcorr,self.frame,self.mtx,self.dist)

        frame_gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)

        points3D = self.getPos3D(self.frame, True, True, True, (0, 0, 0, 0))
        xmin, xmax, ymin, ymax = self.chess.getSubRect()
        if xmin is not None:
            xmin = int(xmin - (xmax - xmin) / 2)
            xmax = int(xmax + (xmax - xmin) / 2)
            ymin = int(ymin - (ymax - ymin) / 2)
            ymax = int(ymax + (ymax - ymin) / 2)
            self.rect = (xmin, ymin, xmax, ymax)
        self.threadn = cv2.getNumberOfCPUs()
        self.pool = ThreadPool(processes=self.threadn)
        self.pending = deque()

        cv2.imshow('frame', self.frame)

    def process_frame(self):
        frame = self.grabImage(self.cap)
        # frame = self.imageCorr(self.camcorr,frame,self.mtx,self.dist)
        subframe = self.getSubFrame(frame, self.rect)
        self.points3D = self.getPos3D(subframe, False, True, False, (0, 0, 0, 0))
        # if self.chess.getCornerExist(): 
        xminc, xmaxc, yminc, ymaxc = self.chess.getSubRect()
        if xminc is not None:
            xminr, yminr, xmaxr, ymaxr = self.rect
            wsub = subframe.shape[0]
            hsub = subframe.shape[1]
            # print('xminc',xminc,'xmaxc',xmaxc)

            xcc = xminc + (xmaxc - xminc) / 2
            ycc = yminc + (ymaxc - yminc) / 2

            # print('xcc:',xcc,'ycc:',ycc)

            xcr = (xmaxr - xminr) / 2
            ycr = (ymaxr - yminr) / 2
            xcsub = wsub / 2
            ycsub = hsub / 2

            dx = xcc - xcsub
            dy = ycc - ycsub
            # print('dx:',dx,'dy:',dy)
            xminr = xminr + 0.2 * dx
            xmaxr = xmaxr + 0.2 * dx
            yminr = yminr + 0.2 * dy
            ymaxr = ymaxr + 0.2 * dy

            self.rect = (xminr, yminr, xmaxr, ymaxr)
            # frame = self.chess.drawRect(frame,(xminw-(xmax-xmin),yminw-(ymax-ymin)))
            frame = self.chess.drawRect(frame, (xminr - (xmaxc - xminc), yminr - (ymaxc - yminc)))
            # print(self.rect)  
        return frame, subframe

    def startCamera(self, video_src, width, height, brightness, contrast, saturation):
        '''Start the camera'''
        cap = cv2.VideoCapture(video_src)
        cap.set(3, width)
        cap.set(4, height)
        cap.set(10, brightness)
        cap.set(11, contrast)
        cap.set(12, saturation)
        isrunning = True
        return cap, isrunning

    def grabImage(self, cap):
        ret, frame = cap.read()
        return frame

    def imageCorr(self, camcorr, frame, mtx, dist):
        frame = camcorr.undistortImage(frame, mtx, dist)
        return frame

    def getPos3D(self, frame, drawimg=False, keep=False, initimg=False, pos=(0, 0, 0, 0)):
        '''Get the position'''
        frame, ptzero, points3D, grayimg = self.chess.chessboard3D(frame, drawimg, keep, initimg, pos)
        return points3D

    def getSubFrame(self, frame, rect):
        xmin, ymin, xmax, ymax = rect
        w = int((xmax - xmin) * 2)
        h = int((ymax - ymin) * 2)
        x = int((xmin + xmax) / 2)
        y = int((ymin + ymax) / 2)
        subframe = cv2.getRectSubPix(frame, (w, h), (x, y))
        return subframe

    def stopCamera(self):
        '''Stop the camera'''
        # Destroy windows, close the app
        cv2.destroyAllWindows()
        self.cap.release()
        self.isrunning = False

    def initTracking(self):
        cv2.destroyAllWindows()
        frame = self.grabImage(self.cap)
        points3D = self.getPos3D(frame, True, True, True)
        xmin, xmax, ymin, ymax = self.chess.getSubRect()
        xmin = int(xmin - (xmax - xmin) / 2)
        xmax = int(xmax + (xmax - xmin) / 2)
        ymin = int(ymin - (ymax - ymin) / 2)
        ymax = int(ymax + (ymax - ymin) / 2)
        self.rect = (xmin, ymin, xmax, ymax)

    def run(self):
        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                frame, subframe = self.pending.popleft().get()
                cv2.imshow('frame', frame)
                # cv2.imshow('subframe', subframe)                
            if len(self.pending) < self.threadn:
                self.task = self.pool.apply_async(self.process_frame, ())
                self.pending.append(self.task)
            ch = cv2.waitKey(1)
            if ch == 27:
                break
            if ch == ord('c'):
                try:
                    self.initTracking()
                except:
                    None
        self.stopCamera()


if __name__ == '__main__':
    print(__doc__)
    try:
        video_src = args[0]
    except:
        video_src = 0
    App(video_src, 5, 5, 10).run()
