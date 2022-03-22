# -*- coding: utf-8 -*-
import numpy as np


class RangeFinder:
    def __init__(self, center, imgsize):
        self.center = center
        self.imgsize = imgsize
        self.imgCenter()
        self.focal = 884.  # Focal length of the camera in pixels
        tant1 = 175.263 / self.focal
        tant2 = 239.426 / self.focal
        L1 = 0.7
        L2 = 0.2
        self.laseroffset = np.abs((L1 * L2 * (tant2 - tant1)) / (tant2 * L2 - tant1 * L1))
        print(self.laseroffset)
        self.laserangletan = tant2 * L2 / (L2 + self.laseroffset)
        print(np.arctan(self.laserangletan) * 180 / np.pi)

    def imgCenter(self):
        (width, height) = self.imgsize
        self.xcenter = width / 2.
        self.ycenter = height / 2.

    def pixelsFromCenter(self, center):
        self.center = center
        (self.x, self.y) = self.center
        self.dx = np.abs(self.x - self.xcenter)
        self.dy = np.abs(self.y - self.xcenter)
        self.pfc = np.sqrt(self.dx ** 2 + self.dy ** 2)

    def calcDistance(self):
        self.distance = self.laseroffset * self.laserangletan / (self.pfc / self.focal - self.laserangletan)
        # self.distance=-9438.31317457957 + 201.25032427917*self.pfc - 1.56320392857476*self.pfc**2 + 0.00529782313954671*self.pfc**3 - 6.64268846809443e-06*self.pfc**4
        return self.distance
