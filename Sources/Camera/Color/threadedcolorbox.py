#!/usr/bin/env python

'''
Multithreaded video processing sample.
Keyboard shortcuts:
   ESC - exit
'''

# Python 2/3 compatibility
from __future__ import print_function

import numpy as np
import cv2

from multiprocessing.pool import ThreadPool
from collections import deque

from common import clock, draw_str
import video

import colorbox as cb

if __name__ == '__main__':
    import sys

    print(__doc__)

    try:
        fn = sys.argv[1]
    except:
        fn = 0
    cap = video.create_capture(fn)

    color_chc = 'dark_red'


    def process_frame(frame, t):
        frame = cb.ColorBox(frame, color_chc)
        return frame, t


    threadn = cv2.getNumberOfCPUs()
    pool = ThreadPool(processes=threadn)
    pending = deque()

    while True:
        while len(pending) > 0 and pending[0].ready():
            res, t0 = pending.popleft().get()
            cv2.imshow('threaded video', res)
        if len(pending) < threadn:
            ret, frame = cap.read()
            t = clock()
            task = pool.apply_async(process_frame, (frame.copy(), t))
            pending.append(task)
        ch = cv2.waitKey(1) & 0xFF
        if ch == 27:
            break

    cv2.destroyAllWindows()
    cap.release()
