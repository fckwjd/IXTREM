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
from common import clock, draw_str, StatValue
import video


class App:
    def __init__(self, video_src, color_chc):
        self.cap = video.create_capture(video_src)
        width = 1280
        height = 720
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

    def process_frame(self, t0):
        ret, frame = self.cap.read()
        # frame = self.equalize_histogram(frame)

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # frame_gray = cv2.fastNlMeansDenoising(frame_gray, 10,10, 7, 5)
        return frame_gray, t0

    def run(self):
        latency = StatValue()
        frame_interval = StatValue()
        last_frame_time = clock()
        numimg = 0

        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                frame, t0 = self.pending.popleft().get()
                latency.update(clock() - t0)
                if self.clocking:
                    draw_str(frame, (20, 20), "latency        :  %.1f ms" % (latency.value * 1000))
                    draw_str(frame, (20, 40), "frame interval :  %.1f ms" % (frame_interval.value * 1000))
                    draw_str(frame, (20, 60), "frame frequency :  %.1f Hz" % (1 / frame_interval.value))

                cv2.imshow('frame', frame)

            if len(self.pending) < self.threadn:
                t = clock()
                frame_interval.update(t - last_frame_time)
                last_frame_time = t
                self.task = self.pool.apply_async(self.process_frame, (t,))
                self.pending.append(self.task)
            ch = cv2.waitKey(1)
            if ch == 27:
                break
            if ch == ord('c'):
                self.clocking = not self.clocking
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
        video_src = '0'
    App(video_src, 'dark_red').run()
