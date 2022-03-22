#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Multithreaded video processing sample. Feature tracker with MOSSE method.
Select your areas to be tracked.
Keyboard shortcuts:
   ESC - exit
   C - clean trackers
"""
# Python 2/3 compatibility
from __future__ import print_function
import numpy as np
import cv2
from multiprocessing.pool import ThreadPool
from collections import deque
from common import draw_str, RectSelector
from matplotlib import pyplot as plt
import video
import time
import sys

PY3 = sys.version_info[0] == 3

if PY3:
    xrange = range


class MOSSE:
    def __init__(self, frame, rect):
        self.good = False
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

        self.g = cv2.dft(g, flags=cv2.DFT_COMPLEX_OUTPUT)
        self.h1 = np.zeros_like(self.g)
        self.h2 = np.zeros_like(self.g)
        for _i in xrange(128):
            a = self.preprocess(self.rnd_warp(img))
            b = cv2.dft(a, flags=cv2.DFT_COMPLEX_OUTPUT)
            self.h1 += cv2.mulSpectrums(self.g, b, 0, conjB=True)
            self.h2 += cv2.mulSpectrums(b, b, 0, conjB=True)
        self.update_kernel()
        self.update(frame)

    def update(self, frame, rate=0.125):
        (x, y), (w, h) = self.pos, self.size
        self.last_img = img = cv2.getRectSubPix(frame, (w, h), (x, y))
        img = self.preprocess(img)
        self.last_resp, (dx, dy), self.psr = self.correlate(img)
        self.good = self.psr > 10000.0  # 8.0
        if not self.good:
            return

        self.pos = x + dx, y + dy
        self.last_img = img = cv2.getRectSubPix(frame, (w, h), self.pos)
        img = self.preprocess(img)

        b = cv2.dft(img, flags=cv2.DFT_COMPLEX_OUTPUT)
        h1 = cv2.mulSpectrums(self.g, b, 0, conjB=True)
        h2 = cv2.mulSpectrums(b, b, 0, conjB=True)
        self.h1 = self.h1 * (1.0 - rate) + h1 * rate
        self.h2 = self.h2 * (1.0 - rate) + h2 * rate
        self.update_kernel()

    def get_subframe(self, frame):
        (x, y), (w, h) = self.pos, self.size
        img = cv2.getRectSubPix(frame, (w, h), (x, y))
        return img

    @property
    def state_vis(self):
        f = cv2.idft(self.h, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
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
        c = cv2.mulSpectrums(cv2.dft(img, flags=cv2.DFT_COMPLEX_OUTPUT), self.h, 0, conjB=True)
        resp = cv2.idft(c, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
        h, w = resp.shape
        _, mval, _, (mx, my) = cv2.minMaxLoc(resp)
        side_resp = resp.copy()
        cv2.rectangle(side_resp, (mx - 50, my - 50), (mx + 50, my + 50), 0, -1)
        smean, sstd = side_resp.mean(), side_resp.std()
        psr = (mval - smean) / (sstd + self.eps)
        return resp, (mx - w // 2, my - h // 2), psr

    def update_kernel(self):
        self.h = self.divspec(self.h1, self.h2)
        self.h[..., 1] *= -1

    def rnd_warp(self, a):
        h, w = a.shape[:2]
        t = np.zeros((2, 3))
        coef = 0.2
        ang = (np.random.rand() - 0.5) * coef
        c, s = np.cos(ang), np.sin(ang)
        t[:2, :2] = [[c, -s], [s, c]]
        t[:2, :2] += (np.random.rand(2, 2) - 0.5) * coef
        c = (w / 2, h / 2)
        t[:, 2] = c - np.dot(t[:2, :2], c)
        return cv2.warpAffine(a, t, (w, h), borderMode=cv2.BORDER_REFLECT)

    def divspec(self, a, b):
        ar, ai = a[..., 0], a[..., 1]
        br, bi = b[..., 0], b[..., 1]
        c = (ar + 1j * ai) / (br + 1j * bi)
        c = np.dstack([np.real(c), np.imag(c)]).copy()
        return c

    def get_centralpos(self):
        return self.pos


class Position:
    def __init__(self):
        self.pos = ()

    def setpos(self, posx, posy):
        self.pos = (posx, posy)

    def getpos(self):
        return self.pos


class App:
    def __init__(self, video_src, color_chc, width=1280, height=720):
        self.cap = video.create_capture(video_src)
        brightness = 8
        contrast = 20
        saturation = 84
        fps = 30
        self.cap.set(3, width)
        self.cap.set(4, height)
        self.cap.set(10, brightness)
        self.cap.set(11, contrast)
        self.cap.set(12, saturation)
        self.color_chc = color_chc

        self.cap.set(cv2.CAP_PROP_FPS, fps)
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(time, fps)

        self.threadn = cv2.getNumberOfCPUs()
        self.pool = ThreadPool(processes=self.threadn)
        self.pending = deque()

        _, frame = self.cap.read()
        cv2.imshow('frame', frame)

        self.ti = time.time_ns() * 1e-9
        self.rect_sel = RectSelector('frame', self.onrect)
        self.trackers = []
        self.trackerspos = np.array([]).reshape((0, 2))
        self.positions = []
        self.count = 0
        self.tn = 0
        self.timet = 0

    def onrect(self, rect):
        _, frame = self.cap.read()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        tracker = MOSSE(frame_gray, rect)
        position = Position()
        self.trackers.append(tracker)
        self.positions.append(position)

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
        self.tn = time.time_ns() * 1e-9
        self.timet = (self.tn - self.ti) * 1000
        self.ti = self.tn
        # print('time (ms):', self.timet)
        frame = self.equalize_histogram(frame)
        self.rect_sel.draw(frame)
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        for tracker in self.trackers:
            tracker.update(frame_gray, 0.05)
        for tracker in self.trackers:
            tracker.draw_state(frame)
            # frame = cb.ColorBox(frame,self.color_chc)
        return frame

    def run(self):
        while True:
            while len(self.pending) > 0 and self.pending[0].ready():
                frame = self.pending.popleft().get()

                if len(self.trackers) > 0:

                    for i in range(len(self.trackers)):
                        # cv2.imshow('tracker state ' + str(i),
                        #           self.trackers[i - 1].state_vis)
                        # subframe = self.calc_histogram(self.trackers[i-1].get_subframe(frame),frame)                
                        # cv2.imshow('tracking'+str(i),subframe)
                        # cv2.imshow('tracking' + str(i),
                        # self.trackers[i - 1].get_subframe(frame))
                        pos = self.trackers[i - 1].get_centralpos()
                        self.pos = self.positions[i - 1].getpos()
                        if self.count > 0:
                            try:
                                self.speed = np.sqrt((self.pos[0] - pos[0]) ** 2 + (self.pos[1] - pos[1]) ** 2) / (
                                        self.timet * 1e-3)
                                # print(self.speed)
                                self.angle = np.arctan2((self.pos[1] - pos[1]), (self.pos[0] - pos[0]))
                                print(self.angle * 180 / np.pi)
                                if not np.isnan(self.angle):
                                    x = int(pos[0] - self.speed * 1 * np.cos(self.angle))
                                    y = int(pos[1] - self.speed * 1 * np.sin(self.angle))
                                    arrowpos = (x, y)
                                    # print(self.arrowpos)
                                    postemp = (int(pos[0]), int(pos[1]))
                                    cv2.arrowedLine(frame, postemp, arrowpos, (255, 255, 0))
                            except:
                                None
                        self.trackerspos = np.append(self.trackerspos, np.array([pos]), axis=0)
                        self.positions[i - 1].setpos(pos[0], pos[1])
                        self.count = self.count + 1
                cv2.imshow('frame', frame)
            if len(self.pending) < self.threadn:
                self.task = self.pool.apply_async(self.process_frame, ())
                self.pending.append(self.task)
            ch = cv2.waitKey(1)
            if ch == 27:
                break
            if ch == ord('c'):
                if len(self.trackers) > 0:

                    for i in range(len(self.trackers)):
                        cv2.destroyWindow('tracker state ' + str(i))
                        cv2.destroyWindow('tracking' + str(i))
                self.trackers = []

                self.trackerspos = np.array(self.trackerspos)
                posx = self.trackerspos[:, 0]
                posy = self.trackerspos[:, 1]
                plt.figure(figsize=(17, 3.5), num="Rotor")
                ax = plt.subplot(111)
                ax.plot(posx, posy, 'k+')
                plt.show()
                self.trackerspos = np.array([]).reshape((0, 2))
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':

    print(__doc__)
    try:
        video_src = args[0]
    except:
        video_src = '0'
    App(video_src, 'dark_red', 620, 480).run()
