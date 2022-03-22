#!/usr/bin/env python

'''
Feature homography
==================

Example of using features2d framework for interactive video homography matching.
ORB features and FLANN matcher are used. The actual tracking is implemented by
PlaneTracker class in plane_tracker.py

Inspired by http://www.youtube.com/watch?v=-ZNYoL8rzPY

video: http://www.youtube.com/watch?v=FirtmYcC0Vc

Usage
-----
feature_homography.py [<video source>]

Keys:
   SPACE  -  pause video

Select a textured planar object to track by drawing a box with a mouse.
'''

# Python 2/3 compatibility
from __future__ import print_function

import numpy as np
import cv2

# local modules
import video
import common
import cameraundistort as undis
from common import getsize, draw_keypoints
from plane_tracker import PlaneTracker

lk_params = dict(winSize=(15, 15),
                 maxLevel=2,
                 criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict(maxCorners=200,
                      qualityLevel=0.3,
                      minDistance=7,
                      blockSize=7)


class App:
    def __init__(self, src):
        self.cap = video.create_capture(src)
        self.frame = None
        self.paused = False
        # self.tracks = PlaneTracker()
        self.tracks = []
        # self.camcorr = undis.CameraUndistort()
        # self.mtx, self.dist = self.camcorr.calibrate()
        cv2.namedWindow('plane')
        self.rect_sel = common.RectSelector('plane', self.on_rect)

    def on_rect(self, rect):
        ret, frame = self.cap.read()
        self.frame = frame.copy()
        self.frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        self.frame_gray = self.camcorr.undistortImage(self.frame_gray, self.mtx, self.dist)

        mask = np.zeros_like(frame_gray)
        cv2.rectangle(mask, self.rect_sel, 280, 1, thickness=-1)
        mask = cv2.bitwise_and(self.frame_gray, self.frame_gray, mask=mask)
        for x, y in [np.int32(tr[-1]) for tr in self.tracks]:
            cv2.circle(mask, (x, y), 5, 0, -1)
        p = cv2.goodFeaturesToTrack(frame_gray, mask=mask, **feature_params)
        if p is not None:
            for x, y in np.float32(p).reshape(-1, 2):
                self.tracks.append([(x, y)])

    def run(self):
        while True:
            playing = not self.paused and not self.rect_sel.dragging
            if playing or self.frame is None:
                ret, frame = self.cap.read()
                if not ret:
                    break
                self.frame = frame.copy()
                # self.frame = self.camcorr.undistortImage(self.frame, self.mtx, self.dist)

            w, h = getsize(self.frame)
            vis = np.zeros((h, w * 2, 3), np.uint8)
            vis[:h, :w] = self.frame
            if len(self.tracks) > 0:
                target = self.tracks.targets[0]
                vis[:, w:] = target.image
                draw_keypoints(vis[:, w:], target.keypoints)
                x0, y0, x1, y1 = target.rect
                cv2.rectangle(vis, (x0 + w, y0), (x1 + w, y1), (0, 255, 0), 2)

            if playing:
                tracked = self.tracks.track(self.frame)
                if len(tracked) > 0:
                    tracked = tracked[0]
                    cv2.polylines(vis, [np.int32(tracked.quad)], True, (255, 255, 255), 2)
                    for (x0, y0), (x1, y1) in zip(np.int32(tracked.p0), np.int32(tracked.p1)):
                        cv2.line(vis, (x0 + w, y0), (x1, y1), (0, 255, 0))
            draw_keypoints(vis, self.tracks.frame_points)

            # ---------------------------------------------------------------------------------------------
            ret, frame = self.cam.read()
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            vis = frame.copy()

            if len(self.tracks) > 0:
                img0, img1 = self.prev_gray, frame_gray
                p0 = np.float32([tr[-1] for tr in self.tracks]).reshape(-1, 1, 2)
                p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
                p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
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

            # ---------------------------------------------------------------------------------------------

            self.rect_sel.draw(vis)
            cv2.imshow('plane', vis)
            ch = cv2.waitKey(1)
            if ch == ord(' '):
                self.paused = not self.paused
            if ch == 27:
                cv2.destroyAllWindows()
                self.cap.release()
                break


if __name__ == '__main__':
    print(__doc__)

    import sys

    try:
        video_src = sys.argv[1]
    except:
        video_src = 0
    App(video_src).run()
