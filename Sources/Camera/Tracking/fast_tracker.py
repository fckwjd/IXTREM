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
from common import clock, draw_str, RectSelector


class App:
    def __init__(self, video_src, color_chc):
        self.cap = cv2.VideoCapture(video_src)
        width = 720
        height = 480
        brightness = 8
        contrast = 20
        saturation = 84
        self.cap.set(3, width)
        self.cap.set(4, height)
        self.cap.set(10, brightness)
        self.cap.set(11, contrast)
        self.cap.set(12, saturation)
        self.color_chc = color_chc

        self.clocking = True

        self.threadn = cv2.getNumberOfCPUs()
        self.pool = ThreadPool(processes=self.threadn)
        self.pending = deque()

        _, frame = self.cap.read()
        cv2.imshow('frame', frame)
        self.rect_sel = RectSelector('frame', self.onrect)
        self.trackers = []

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

    def onrect(self, rect):
        _, frame = self.cap.read()
        # frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.tracker = self.define_tracker()
        # Initialize tracker with first frame and bounding box      
        w = np.abs(rect[2] - rect[0])
        h = np.abs(rect[1] - rect[3])
        bbox = (rect[0], rect[1], w, h)
        ok = self.tracker.init(frame, bbox)
        self.trackers.append(self.tracker)

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

    def define_tracker(self):
        tracker_types = ['BOOSTING', 'MIL', 'KCF', 'TLD', 'MEDIANFLOW', 'GOTURN']
        tracker_type = tracker_types[4]

        if tracker_type == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        elif tracker_type == 'MIL':
            tracker = cv2.TrackerMIL_create()
        elif tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        elif tracker_type == 'TLD':
            tracker = cv2.TrackerTLD_create()
        elif tracker_type == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        elif tracker_type == 'GOTURN':
            tracker = cv2.TrackerGOTURN_create()
        return tracker

    def process_frame(self):
        ret, frame = self.cap.read()
        frame = self.equalize_histogram(frame)

        self.rect_sel.draw(frame)
        if ret:
            # for tracker in self.trackers:
            try:
                ok, bbox = self.tracker.update(frame)
                if ok:
                    # Tracking success
                    p1 = (int(bbox[0]), int(bbox[1]))
                    p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
                    cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)
                else:
                    # Tracking failure
                    cv2.putText(frame, "Tracking failure detected", (100, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,
                                (0, 0, 255), 2)
            except:
                None
            # tracker.draw_state(frame)                   
        return frame

    def run(self):
        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                frame = self.pending.popleft().get()
                cv2.imshow('frame', frame)
                # if len(self.trackers) > 0:
                # for i in range(len(self.trackers)):
                # cv2.imshow('tracker state '+str(i),
                # self.trackers[i-1].state_vis)
                # subframe = self.trackers[i-1].get_subframe(frame)
                # cv2.imshow('tracking'+str(i),
                # self.trackers[i-1].detect_color(subframe,self.color_chc))
                # pos = self.trackers[i-1].get_centralpos()
                # self.trackerspos = np.append(self.trackerspos, np.array([pos]),axis=0)
            if len(self.pending) < self.threadn:
                self.task = self.pool.apply_async(self.process_frame, ())
                self.pending.append(self.task)
            ch = cv2.waitKey(1)
            if ch == 27:
                break
            if ch == ord('p'):
                cv2.imwrite('img' + str(numimg) + '.jpg', frame)
                numimg += 1

        cv2.destroyAllWindows()
        self.cap.release()


if __name__ == '__main__':
    print(__doc__)
    try:
        video_src = args[0]
    except:
        video_src = 0
    App(video_src, 'dark_red').run()
