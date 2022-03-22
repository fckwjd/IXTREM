#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Multithreaded video processing sample. Feature tracker with MOSSE method and
Canny detection.
Select your colored area to be tracked. Plot a 3D graph of the tracking.
Keyboard shortcuts:
   ESC - exit
   C - clean trackers and plot 3D graph
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
from common import draw_str, RectSelector
from matplotlib import pyplot as plt
from mpl_toolkits.mplot3d import axis3d
import mossedetection as mosse


class App:

    def __init__(self, video_src, color_chc, width=1280, height=720):
        print('ok')
        self.cap = cv2.VideoCapture(video_src)
        brightness = 20
        contrast = 1
        saturation = 60
        self.cap.set(3, width)
        self.cap.set(4, height)
        self.cap.set(10, brightness)
        self.cap.set(11, contrast)
        self.cap.set(12, saturation)
        self.color_chc = color_chc

        self.threadn = cv2.getNumberOfCPUs()
        self.pool = ThreadPool(processes=self.threadn)
        self.pending = deque()

        _, frame = self.cap.read()
        print('ok')
        cv2.imshow('frame', frame)
        self.rect_sel = RectSelector('frame', self.onrect)
        self.trackers = []
        self.trackerspos = np.array([]).reshape((0, 2))
        self.area_l = []

    def onrect(self, rect):
        _, frame = self.cap.read()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tracker = mosse.MOSSE(frame_gray, frame, rect, self.color_chc)
        self.trackers.append(tracker)

    def equalize_histogram(self, frame):
        # Histogram equalization
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        lab = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        frame = lab
        return frame

    def calc_histogram(self, subframe, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsvs = cv2.cvtColor(subframe, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsvs], [0, 1], None, [180, 256], [0, 180, 0, 256])

        cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
        dst = cv2.calcBackProject([hsv], [0, 1], hist, [0, 180, 0, 256], 1)

        # Now convolute with circular disc
        disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cv2.filter2D(dst, -1, disc, dst)

        # threshold and binary AND
        ret, thresh = cv2.threshold(dst, 50, 255, 0)
        thresh = cv2.merge((thresh, thresh, thresh))
        res = cv2.bitwise_and(frame, thresh)

        frame = np.vstack((thresh, res))
        return frame

    def process_frame(self):
        ret, frame = self.cap.read()
        # frame = self.equalize_histogram(frame)
        framecopy = frame.copy()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.rect_sel.draw(frame)
        for tracker in self.trackers:
            tracker.update(framecopy, 0.1)
            tracker.draw_state(frame)
        return frame

    def run(self):
        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                # Dequeue frame and display it
                frame = self.pending.popleft().get()
                cv2.imshow('frame', frame)

                # Display tracked objects
                if len(self.trackers) > 0:
                    for i in range(len(self.trackers)):
                        subframe = self.trackers[i - 1].get_subframe(frame)
                        cv2.imshow('tracking' + str(i),
                                   self.trackers[i - 1].detect_color(subframe, self.color_chc))
                        pos = self.trackers[i - 1].get_centralpos()
                        area = self.trackers[i - 1].get_area()
                        if area > 0:
                            self.area_l = np.append(self.area_l, area)
                            self.trackerspos = np.append(self.trackerspos,
                                                         np.array([pos]), axis=0)

            if len(self.pending) < self.threadn:
                self.task = self.pool.apply_async(self.process_frame, ())
                self.pending.append(self.task)
            ch = cv2.waitKey(1)
            if ch == 27:
                # Quit App if 'Esc' pressed
                break
            if ch == ord('c'):
                if len(self.trackers) > 0:
                    # Destroy windows
                    for i in range(len(self.trackers)):
                        cv2.destroyWindow('tracking' + str(i))

                        # Plot 3D graph of the position of the tracked object
                self.trackerspos = np.array(self.trackerspos)
                posx = self.trackerspos[:, 0]
                posy = self.trackerspos[:, 1]
                fig = plt.figure()
                ax = fig.gca(projection='3d')
                z = np.array(1 / (self.area_l / np.max(self.area_l)))
                ax.plot(posx, posy, zs=z)
                plt.show()

                # Initialize arrays
                self.trackers = []
                self.trackerspos = np.array([]).reshape((0, 2))
                self.area_l = []

        cv2.destroyAllWindows()
        self.cap.release()


if __name__ == '__main__':
    print(__doc__)
    try:
        video_src = args[0]
    except:
        video_src = 0
    App(video_src, 'white', 480, 640).run()
