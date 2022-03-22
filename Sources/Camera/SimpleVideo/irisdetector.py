#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Multithreaded video processing sample. Feature tracker with MOSSE method.
Select your areas to be tracked.
Keyboard shortcuts:
   ESC - exit
   C - clean trackers
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
from common import clock, draw_str, RectSelector
import video


class App:
    def __init__(self, video_src, color_chc):
        self.cap = video.create_capture(video_src)
        width = 1280
        height = 720
        self.cap.set(3, width)
        self.cap.set(4, height)
        self.color_chc = color_chc

        self.threadn = cv2.getNumberOfCPUs()
        self.pool = ThreadPool(processes=self.threadn)
        self.pending = deque()

        _, frame = self.cap.read()
        cv2.imshow('frame', frame)

    def process_frame(self):
        ret, frame = self.cap.read()
        # Histogram equalization
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        lab = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        frame = lab
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blur = cv2.bilateralFilter(frame_gray, 9, 75, 75)
        # blur = cv2.bilateralFilter(blur,9,75,75)

        ret, thresh = cv2.threshold(blur, 50, 255, cv2.THRESH_BINARY)
        thresh = cv2.bilateralFilter(thresh, 9, 75, 75)
        res = cv2.bitwise_and(frame, frame, mask=thresh)

        surf = cv2.xfeatures2d.SURF_create(10000)
        kp, des = surf.detectAndCompute(res, None)

        frame = cv2.drawKeypoints(frame, kp, None, (255, 0, 0), 4)

        return frame

    def run(self):
        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                frame = self.pending.popleft().get()
                cv2.imshow('frame', frame)
            if len(self.pending) < self.threadn:
                self.task = self.pool.apply_async(self.process_frame, ())
                self.pending.append(self.task)
            ch = cv2.waitKey(1)
            if ch == 27:
                break
            if ch == ord('c'):
                ret, frame = self.cap.read()
        cv2.destroyAllWindows()
        self.cap.release()


if __name__ == '__main__':
    print(__doc__)
    try:
        video_src = args[0]
    except:
        video_src = '0'
    App(video_src, 'dark_red').run()
