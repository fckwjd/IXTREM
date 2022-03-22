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
import colorbox as cb
from common import clock, draw_str, RectSelector
# import video
from time import sleep


class NewMOSSE:
    def __init__(self, frame, rect):
        self.eps = 1e-5
        x1, y1, x2, y2 = rect
        w, h = map(cv2.getOptimalDFTSize, [x2 - x1, y2 - y1])
        x1, y1 = (x1 + x2 - w) // 2, (y1 + y2 - h) // 2
        self.pos = x, y = x1 + 0.5 * (w - 1), y1 + 0.5 * (h - 1)
        self.size = w, h
        img = cv2.getRectSubPix(frame, (w, h), (x, y))

        self.win = cv2.createHanningWindow((w, h), cv2.CV_32F)
        g = np.zeros((h, w), np.float32)
        g[h // 2, w // 2] = 1
        g = cv2.GaussianBlur(g, (-1, -1), 2.0)
        g /= g.max()

        self.G = cv2.dft(g, flags=cv2.DFT_COMPLEX_OUTPUT)
        self.H1 = np.zeros_like(self.G)
        self.H2 = np.zeros_like(self.G)
        for _i in xrange(128):
            a = self.preprocess(self.rnd_warp(img))
            A = cv2.dft(a, flags=cv2.DFT_COMPLEX_OUTPUT)
            self.H1 += cv2.mulSpectrums(self.G, A, 0, conjB=True)
            self.H2 += cv2.mulSpectrums(A, A, 0, conjB=True)
        self.update_kernel()
        self.update(frame, 0.05, 10)

    def update(self, frame, rate=0.125, psr=8.0):
        (x, y), (w, h) = self.pos, self.size
        self.last_img = img = cv2.getRectSubPix(frame, (w, h), (x, y))
        img = self.preprocess(img)
        self.last_resp, (dx, dy), self.psr = self.correlate(img)
        self.good = self.psr > psr
        if not self.good:
            return
        self.last_img = img = cv2.getRectSubPix(frame, (w, h), (x, y))
        img = self.preprocess(img)

        A = cv2.dft(img, flags=cv2.DFT_COMPLEX_OUTPUT)
        H1 = cv2.mulSpectrums(self.G, A, 0, conjB=True)
        H2 = cv2.mulSpectrums(A, A, 0, conjB=True)
        self.H1 = self.H1 * (1.0 - rate) + H1 * rate
        self.H2 = self.H2 * (1.0 - rate) + H2 * rate
        self.update_kernel()

    def get_subframe(self, frame):
        (x, y), (w, h) = self.pos, self.size
        img = cv2.getRectSubPix(frame, (w, h), (x, y))
        return img

    @property
    def state_vis(self):
        f = cv2.idft(self.H, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
        h, w = f.shape
        f = np.roll(f, -h // 2, 0)
        f = np.roll(f, -w // 2, 1)
        kernel = np.uint8((f - f.min()) / f.ptp() * 255)
        resp = self.last_resp
        resp = np.uint8(np.clip(resp / resp.max(), 0, 1) * 255)
        vis = np.hstack([self.last_img, kernel, resp])
        return vis

    def draw_state(self, vis):
        (x, y), (w, h) = self.pos, self.size
        x1, y1, x2, y2 = int(x - 0.5 * w), int(y - 0.5 * h), int(x + 0.5 * w), int(y + 0.5 * h)
        cv2.rectangle(vis, (x1, y1), (x2, y2), (255, 0, 255))
        if self.good:
            cv2.circle(vis, (int(x), int(y)), 2, (255, 0, 255), -1)
        else:
            cv2.line(vis, (x1, y1), (x2, y2), (255, 0, 255))
            cv2.line(vis, (x2, y1), (x1, y2), (255, 0, 255))
        draw_str(vis, (x1, y2 + 16), 'PSR: %.2f' % self.psr)

    def preprocess(self, img):
        img = np.log(np.float32(img) + 1.0)
        img = (img - img.mean()) / (img.std() + self.eps)
        return img * self.win

    def correlate(self, img):
        C = cv2.mulSpectrums(cv2.dft(img, flags=cv2.DFT_COMPLEX_OUTPUT)
                             , self.H, 0, conjB=True)
        resp = cv2.idft(C, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
        h, w = resp.shape
        _, mval, _, (mx, my) = cv2.minMaxLoc(resp)
        side_resp = resp.copy()
        cv2.rectangle(side_resp, (mx - 5, my - 5), (mx + 5, my + 5), 0, -1)
        smean, sstd = side_resp.mean(), side_resp.std()
        psr = (mval - smean) / (sstd + self.eps)
        return resp, (mx - w // 2, my - h // 2), psr

    def update_kernel(self):
        self.H = self.divSpec(self.H1, self.H2)
        self.H[..., 1] *= -1

    def rnd_warp(self, a):
        h, w = a.shape[:2]
        T = np.zeros((2, 3))
        coef = 0.2
        ang = (np.random.rand() - 0.5) * coef
        c, s = np.cos(ang), np.sin(ang)
        T[:2, :2] = [[c, -s], [s, c]]
        T[:2, :2] += (np.random.rand(2, 2) - 0.5) * coef
        c = (w / 2, h / 2)
        T[:, 2] = c - np.dot(T[:2, :2], c)
        return cv2.warpAffine(a, T, (w, h), borderMode=cv2.BORDER_REFLECT)

    def divSpec(self, A, B):
        Ar, Ai = A[..., 0], A[..., 1]
        Br, Bi = B[..., 0], B[..., 1]
        C = (Ar + 1j * Ai) / (Br + 1j * Bi)
        C = np.dstack([np.real(C), np.imag(C)]).copy()
        return C


class App:
    def __init__(self, video_src, color_chc):
        self.cap = cv2.VideoCapture(video_src)
        width = 1280
        height = 720
        self.cap.set(3, width)
        self.cap.set(4, height)
        self.color_chc = color_chc

        self.threadn = cv2.getNumberOfCPUs()
        self.pool = ThreadPool(processes=self.threadn)

        _, frame = self.cap.read()
        cv2.imshow('frame', frame)
        self.init_tracker(frame)

    def init_tracker(self, frame):
        self.trackers = []
        height, width = frame.shape[:2]
        divframe = 8
        xi = 0
        yi = 0
        divwidth = int(width / divframe)
        divheight = int(height / divframe)
        for i in range(divframe):
            for j in range(divframe):
                rect = xi, yi, xi + divwidth, yi + divheight
                self.onrect(rect, frame)
                xi = xi + divwidth
            yi = yi + divheight
            xi = 0

    def onrect(self, rect, frame):
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tracker = NewMOSSE(frame_gray, rect)
        self.trackers.append(tracker)

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
        for tracker in self.trackers:
            tracker.update(frame_gray, 0.05, 10.0)
        for tracker in self.trackers:
            tracker.draw_state(frame)
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
                self.trackers = []
                ret, frame = self.cap.read()
                self.init_tracker(frame)
        cv2.destroyAllWindows()
        self.cap.release()


if __name__ == '__main__':
    print(__doc__)
    try:
        video_src = args[0]
    except:
        video_src = 0
    App(video_src, 'dark_red').run()
