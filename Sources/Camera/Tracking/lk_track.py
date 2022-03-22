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
from time import clock, sleep

lk_params = dict(winSize=(15, 15),
                 maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict(maxCorners=100,
                      qualityLevel=0.3,
                      minDistance=7,
                      blockSize=7)


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

        self.track_len = 10
        self.detect_interval = 5
        self.tracks = []
        self.frame_idx = 0

        self.clocking = True

        self.threadn = cv2.getNumberOfCPUs()
        self.pool = ThreadPool(processes=self.threadn)
        self.pending = deque()

        _, frame = self.cap.read()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.prev_gray = frame_gray.copy()
        # cv2.imshow('frame', frame)

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

    def calcLK(self, frame_gray, vis):
        if len(self.tracks) > 0:
            img0, img1 = self.prev_gray, frame_gray
            p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)
            p1, _st, _err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
            p0r, _st, _err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
            d = abs(p0 - p0r).reshape(-1, 2).max(-1)
            good = d < 1
            new_tracks = []
            for tr, (x, y), good_flag in zip(self.tracks, p1.reshape(-1, 2), good):
                if not good_flag:
                    continue
                tr.append((x, y))
                if len(tr) > self.track_len:
                    del tr[0]
                new_tracks.append(tr)
                cv2.circle(vis, (x, y), 2, (0, 255, 0), -1)
            self.tracks = new_tracks
            cv2.polylines(vis, [np.int32(tr) for tr in self.tracks], False, (0, 255, 0))
            draw_str(vis, (20, 20), 'track count: %d' % len(self.tracks))
            # print(d)

        if self.frame_idx % self.detect_interval == 0:
            mask = np.zeros_like(frame_gray)
            mask[:] = 255
            for x, y in [np.int32(tr[-1]) for tr in self.tracks]:
                cv2.circle(mask, (x, y), 5, 0, -1)
            p = cv2.goodFeaturesToTrack(frame_gray, mask=mask, **feature_params)
            if p is not None:
                for x, y in np.float32(p).reshape(-1, 2):
                    self.tracks.append([(x, y)])
        return vis

    def process_frame(self, t0):
        ret, frame = self.cap.read()
        # frame = self.equalize_histogram(frame)

        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # frame_gray = cv2.fastNlMeansDenoising(frame_gray, 10,10, 7, 5)

        vis = frame.copy()
        vis = self.calcLK(frame_gray, vis)

        return frame_gray, t0, vis

    def run(self):
        latency = StatValue()
        frame_interval = StatValue()
        last_frame_time = clock()
        numimg = 0

        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                frame_gray, t0, vis = self.pending.popleft().get()
                # latency.update(clock() - t0)
                # if self.clocking:
                # draw_str(frame_gray, (20, 20), "latency        :  %.1f ms" % (latency.value*1000))
                # draw_str(frame_gray, (20, 40), "frame interval :  %.1f ms" % (frame_interval.value*1000))

                # cv2.imshow('frame', frame_gray)                

                self.frame_idx += 1
                self.prev_gray = frame_gray.copy()
                cv2.imshow('lk_track', vis)
            sleep(0.05)
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
