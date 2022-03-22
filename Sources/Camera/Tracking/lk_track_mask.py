#!/usr/bin/env python

'''
Lucas-Kanade tracker
====================

Lucas-Kanade sparse optical flow demo. Uses goodFeaturesToTrack
for track initialization and back-tracking for match verification
between frames.

Usage
-----
lk_track.py [<video_source>]


Keys
----
ESC - exit
'''

# Python 2/3 compatibility
from __future__ import print_function

import numpy as np
import cv2
import video
import common
from common import anorm2, draw_str, getsize, draw_keypoints
from time import clock
import cameraundistort as undis

lk_params = dict(winSize=(15, 15),
                 maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict(maxCorners=200,
                      qualityLevel=0.3,
                      minDistance=7,
                      blockSize=7)
ar_verts = np.float32([[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0],
                       [0, 0, 1], [0, 1, 1], [1, 1, 1], [1, 0, 1],
                       [0, 0.5, 2], [1, 0.5, 2]])
# ar_verts = np.float32([[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0],
# [0, 0, 1], [0, 1, 1], [1, 1, 1], [1, 0, 1]
# ])

# ar_edges = [(0, 1), (1, 2), (2, 3), (3, 0),
# (4, 5), (5, 6), (6, 7), (7, 4),
# (0, 4), (1, 5), (2, 6), (3, 7),
# (4, 8), (5, 8), (6, 9), (7, 9), (8, 9)]

ar_edges = [(0, 1), (3, 0), (0, 4)]


class App:
    def __init__(self, video_src):
        self.track_len = 10
        self.detect_interval = 5
        self.tracks = []
        self.cam = video.create_capture(video_src)
        self.frame_idx = 0
        self.camcorr = undis.CameraUndistort()
        self.mtx, self.dist = self.camcorr.calibrate()
        cv2.namedWindow('lk_track')
        self.rect_sel = common.RectSelector('lk_track', self.on_rect)

    def on_rect(self, rect):
        self.tracks = []
        ret, frame = self.cam.read()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_gray = self.camcorr.undistortImage(frame_gray, self.mtx, self.dist)
        mask = np.zeros_like(frame_gray)
        x0, y0, x1, y1 = rect
        mask = np.zeros_like(frame_gray)
        mask[y0:y1, x0:x1] = 255
        mask = cv2.bitwise_and(frame_gray, frame_gray, mask=mask)
        for x, y in [np.int32(tr[-1]) for tr in self.tracks]:
            cv2.circle(mask, (x, y), 5, 0, -1)
        p = cv2.goodFeaturesToTrack(frame_gray, mask=mask, **feature_params)
        if p is not None:
            for x, y in np.float32(p).reshape(-1, 2):
                self.tracks.append([(x, y)])
        p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)

        cnt0 = None
        for (x, y) in p0.reshape(-1, 2):
            if cnt0 == None:
                cnt0 = [[x, y]]
            else:
                cnt0.append([x, y])
        self.cnta = np.array(cnt0)
        self.rectangle = cv2.minAreaRect(self.cnta)
        self.box = cv2.boxPoints(self.rectangle)
        self.rectangle = cv2.boundingRect(self.cnta)

    def run(self):
        while True:
            ret, frame = self.cam.read()
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            frame_gray = self.camcorr.undistortImage(frame_gray, self.mtx, self.dist)
            frame = self.camcorr.undistortImage(frame, self.mtx, self.dist)
            vis = frame.copy()
            self.rect_sel.draw(vis)

            if len(self.tracks) > 0:
                img0, img1 = self.prev_gray, frame_gray
                p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)
                p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
                p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
                d = abs(p0 - p0r).reshape(-1, 2).max(-1)
                good = d < 1
                new_tracks = []

                cnt = None
                for (x, y) in p1.reshape(-1, 2):
                    if cnt == None:
                        cnt = [[x, y]]
                    else:
                        cnt.append([x, y])
                cnt = np.array(cnt)

                for tr, (x, y), good_flag in zip(self.tracks, p1.reshape(-1, 2), good):
                    if not good_flag:
                        continue
                    tr.append((x, y))
                    if len(tr) > self.track_len:
                        del tr[0]
                    new_tracks.append(tr)
                    cv2.circle(vis, (x, y), 2, (0, 255, 0), -1)
                self.tracks = new_tracks

                try:
                    self.M, mask = cv2.findHomography(self.cnta, cnt, cv2.RANSAC, 5.0)
                    self.draw_overlay(vis)
                except:
                    self.tracks = []
                    continue

            self.frame_idx += 1
            self.prev_gray = frame_gray
            cv2.imshow('lk_track', vis)

            ch = 0xFF & cv2.waitKey(1)
            if ch == 27:
                self.cam.release()
                break

    def draw_overlay(self, vis):
        x0, y0, width, height = self.rectangle
        x1 = x0 + width
        y1 = y0 + height
        x00 = (x0 + x1) / 2
        y00 = (y0 + y1) / 2
        x11 = x00 + width
        y11 = y00 + height
        quad_3d = np.float32([[x0, y0, 0], [x1, y0, 0], [x1, y1, 0], [x0, y1, 0]])
        fx = 1
        h, w = vis.shape[:2]
        K = np.float64([[fx * w, 0, 0.5 * (w - 1)],
                        [0, fx * w, 0.5 * (h - 1)],
                        [0.0, 0.0, 1.0]])
        dist_coef = np.zeros(4)
        quad = self.box
        quad = cv2.perspectiveTransform(quad.reshape(1, -1, 2), self.M).reshape(-1, 2)
        ret, rvec, tvec = cv2.solvePnP(quad_3d, quad, K, dist_coef)
        quad = [np.int32(quad)]
        # cv2.polylines(vis, quad, True, (255, 255, 255), 1)
        verts = ar_verts * [(x1 - x0), (y1 - y0), -(x1 - x0) * 1] + (x00, y00, 0)
        verts = cv2.projectPoints(verts, rvec, tvec, K, dist_coef)[0].reshape(-1, 2)
        d = 0
        print(verts)
        for i, j in ar_edges:
            (x0, y0), (x1, y1) = verts[i], verts[j]

            d = d + np.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            cv2.line(vis, (int(x0), int(y0)), (int(x1), int(y1)), (255, 200, 200), 2)


def main():
    import sys
    try:
        video_src = sys.argv[1]
    except:
        video_src = 0

    print(__doc__)
    App(video_src).run()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
