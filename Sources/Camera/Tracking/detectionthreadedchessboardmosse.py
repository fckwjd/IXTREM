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

import numpy as np
import cv2
from multiprocessing.pool import ThreadPool
from collections import deque
import colorbox as cb
from common import draw_str, StatValue
import cameraundistort as cu
import chessboard3D as chb
from os import getcwd
import mossedetection as mosse
from time import sleep

import sys

PY3 = sys.version_info[0] == 3

if PY3:
    xrange = range


class App:
    def __init__(self, video_src, board_h, board_w, size):
        # folder = os.path.dirname(os.path.realpath(__file__)) + 'chessboard\\'
        self.points3D = []
        folder = getcwd() + '\\chessboard\\'
        self.cap, self.isrunning = self.startCamera(video_src=0, width=800, height=600, brightness=6,
                                                    contrast=30, saturation=60)
        self.camcorr = cu.CameraUndistort(folder, board_h, board_w, size)
        self.mtx, self.dist = self.camcorr.calibrate()
        # self.mtx=[]
        # self.dist=[]
        self.chess = chb.Chessboard3D(mtx=self.mtx, dist=self.dist, board_h=board_h, board_w=board_w,
                                      size=size, folder=folder)

        frame = self.grabImage(self.cap)
        frame = self.imageCorr(self.camcorr, frame, self.mtx, self.dist)
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        self.lastsubframe = frame.copy()

        self.threadn = cv2.getNumberOfCPUs()
        self.pool = ThreadPool(processes=self.threadn)
        self.pending = deque()

        cv2.imshow('frame', frame)

        points3D = self.getPos3D(frame, True, True, True, (0, 0, 0, 0))
        xmin, xmax, ymin, ymax = self.chess.getSubRect()

        if xmin is not None:
            xmin = int(xmin - (xmax - xmin) / 2)
            xmax = int(xmax + (xmax - xmin) / 2)
            ymin = int(ymin - (ymax - ymin) / 2)
            ymax = int(ymax + (ymax - ymin) / 2)
            self.rect = (xmin, ymin, xmax, ymax)

            self.trackers = mosse.MOSSE(frame_gray, frame, self.rect, colordetection=False)
        else:
            self.trackers = None

    def process_frame(self):
        frame = self.grabImage(self.cap)
        frame = self.imageCorr(self.camcorr, frame, self.mtx, self.dist)
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.trackers is not None:
            self.trackers.update(frame_gray, frame, 0.05)
            tracked = self.trackers.get_istracked()
            pos = self.trackers.get_pos()
            subframe = self.trackers.get_subframe(frame)
            subframe, self.points3D, graysubframe = self.getPos3D(subframe, False, True, False, pos)

            cornerexist = self.chess.getCornerExist()
            if tracked and np.min(pos) >= 0 and cornerexist:
                # offset = (pos[0],pos[1])
                offset = (0, 0)
                frame = self.chess.drawRect(frame, offset)
                print('tracked')
            else:
                print('not tracked or no corner')
                self.initTracking(frame)
            self.lastsubframe = graysubframe.copy()
        else:
            print('not tracked')
            self.initTracking(frame)
        return frame, self.lastsubframe

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
        frame, ptzero, points3D, graysubframe = self.chess.chessboard3D(frame, drawimg, keep, initimg, pos)
        return frame, points3D, graysubframe

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

    def initTracking(self, frame=None):
        try:
            if frame is None:
                frame = self.grabImage(self.cap)
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            points3D = self.getPos3D(frame, False, True, True, (0, 0, 0, 0))
            xmin, xmax, ymin, ymax = self.chess.getSubRect()
            if xmax - xmin < frame.shape[0] and ymax - ymin < frame.shape[1]:
                xmin = int(xmin - (xmax - xmin) / 2)
                xmax = int(xmax + (xmax - xmin) / 2)
                ymin = int(ymin - (ymax - ymin) / 2)
                ymax = int(ymax + (ymax - ymin) / 2)
                self.rect = (xmin, ymin, xmax, ymax)
                self.trackers = mosse.MOSSE(frame_gray, frame, self.rect, colordetection=False)
        except:
            None

    def run(self):
        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                frame, subframe = self.pending.popleft().get()
                cv2.imshow('frame', frame)
                cv2.imshow('subframe', subframe)
            if len(self.pending) < self.threadn:
                self.task = self.pool.apply_async(self.process_frame, ())
                self.pending.append(self.task)
            ch = cv2.waitKey(1)
            if ch == 27:
                break
            if ch == ord('c'):
                try:
                    self.initTracking(frame)
                except:
                    None
        self.stopCamera()


if __name__ == '__main__':
    print(__doc__)
    try:
        video_src = args[0]
    except:
        video_src = 0
    App(video_src, 5, 5, 8).run()
