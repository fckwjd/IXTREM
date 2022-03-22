#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python 2/3 compatibility
from __future__ import print_function
import sys
import numpy as np
import cv2
# import colorbox as cb
import cannydetec as cd
from common import draw_str

'''
Feature tracker with MOSSE method and
Canny detection.
'''

PY3 = sys.version_info[0] == 3

if PY3:
    xrange = range


class MOSSE:
    def __init__(self, frame, framecolor, rect, color_chc='red', colordetection=True):
        self.colordetection = colordetection
        self.eps = 1e-5
        self.prevarea = 0
        self.istracked = True
        self.color_chc = color_chc
        x1, y1, x2, y2 = rect
        w, h = map(cv2.getOptimalDFTSize, [x2 - x1, y2 - y1])
        x1, y1 = (x1 + x2 - w) // 2, (y1 + y2 - h) // 2
        self.pos = x, y = x1 + 0.5 * (w - 1), y1 + 0.5 * (h - 1)
        self.size = w, h

        img = cv2.getRectSubPix(framecolor, (w, h), (x, y))
        if self.colordetection:
            img = self.detect_color(img, self.color_chc)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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
        self.update(framecolor)

    def update(self, framecolor, rate=0.125):
        (x, y), (w, h) = self.pos, self.size
        img = cv2.getRectSubPix(framecolor, (w, h), (x, y))
        if self.colordetection:
            img = self.detect_color(img, self.color_chc)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.last_img = img
        img = self.preprocess(img)
        self.last_resp, (dx, dy), self.psr = self.correlate(img)
        self.good = self.psr > 8.0
        if not self.good:
            self.istracked = False
            return
        self.istracked = True
        self.pos = x + dx, y + dy
        img = cv2.getRectSubPix(framecolor, (w, h), self.pos)
        if self.colordetection:
            img = self.detect_color(img, self.color_chc)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self.last_img = img
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
        vis = np.hstack([self.last_img])  # , kernel, resp])
        return vis

    def draw_state(self, vis):
        (x, y), (w, h) = self.pos, self.size
        # (xmax, ymax) = self.last_img.shape()
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
        C = cv2.mulSpectrums(cv2.dft(img, flags=cv2.DFT_COMPLEX_OUTPUT), self.H, 0, conjB=True)
        resp = cv2.idft(C, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
        h, w = resp.shape
        _, mval, _, (mx, my) = cv2.minMaxLoc(resp)
        side_resp = resp.copy()
        # cv2.rectangle(side_resp, (mx-5, my-5), (mx+5, my+5), 0, -1)
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

    def divSpec(self, a, b):
        ar, ai = a[..., 0], a[..., 1]
        br, bi = b[..., 0], b[..., 1]
        c = (ar + 1j * ai) / (br + 1j * bi)
        c = np.dstack([np.real(c), np.imag(c)]).copy()
        return c

    def get_centralpos(self):
        return self.pos

    def get_pos(self):
        (x, y), (w, h) = self.pos, self.size
        x1, y1, x2, y2 = int(x - 0.5 * w), int(y - 0.5 * h), int(x + 0.5 * w), int(y + 0.5 * h)
        pos = (x1, y1, x2, y2)
        return pos

    def get_size(self):
        return self.size

    def get_area(self):
        return self.area

    def get_istracked(self):
        return self.istracked

    def detect_color(self, frame, color_chc):
        mask = np.zeros_like(frame)
        areasum = 0
        contours = cd.CannyDetec(frame, color_chc, 1000, 5000)
        if self.prevarea == 0:
            for idx in range(len(contours)):
                cnt = contours[idx]
                area = cv2.contourArea(cnt)
                if area > self.prevarea:
                    self.prevarea = area
        if len(contours) > 0 and self.prevarea > 0:
            for idx in range(len(contours)):
                cnt = contours[idx]
                area = cv2.contourArea(cnt)
                M = cv2.moments(cnt)
                ratio = np.abs(area - self.prevarea) / self.prevarea
                if 10 < area < 50000 and ratio < 0.25:
                    try:
                        self.prevarea = area
                        rect = cv2.minAreaRect(cnt)
                        box = cv2.boxPoints(rect)
                        box = np.int0(box)
                        mask = cv2.drawContours(mask, contours, idx, (255, 255, 255), cv2.FILLED)
                        areasum += area
                        cx = int(M['m10'] / M['m00'])
                        cy = int(M['m01'] / M['m00'])
                        # print(cx,cy)
                    except:
                        None
        self.area = areasum
        mask = cv2.bitwise_and(frame, mask)

        return mask
