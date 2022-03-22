# -*- coding: utf-8 -*-
import cv2
import glob
import numpy as np


class CameraUndistort:
    def __init__(self, folder, board_h=8, board_w=7, size=25):
        # termination criteria
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        self.board_h = board_h
        self.board_w = board_w
        self.size = size
        # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
        self.objp = np.zeros(((self.board_h - 1) * (self.board_w - 1), 3), np.float32)
        self.objp[:, :2] = np.mgrid[0:self.board_h - 1, 0:self.board_w - 1].T.reshape(-1, 2)
        self.objp = self.objp * self.size
        # Arrays to store object points and image points from all the images.
        self.objpoints = []  # 3d point in real world space
        self.imgpoints = []  # 2d points in image plane.

        self.images = glob.glob(folder + '*.jpg')
        print(self.images)

    def setFolder(self, folder):
        self.images = glob.glob(folder + '*.jpg')

    def calibrate(self):
        for fname in self.images:
            img = cv2.imread(fname)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, (self.board_h - 1, self.board_w - 1), None)
            # If found, add object points, image points (after refining them)
            if ret:
                self.objpoints.append(self.objp)
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
                self.imgpoints.append(corners2)
                # Draw and display the corners
                # cv2.drawChessboardCorners(gray, (5,5), corners2, ret)
                # cv2.imshow('img'+fname, gray)
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(self.objpoints, self.imgpoints, gray.shape[::-1], None, None)
        return mtx, dist

    def undistortImage(self, img, mtx, dist):
        h, w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
        undimg = cv2.undistort(img, mtx, dist, None, newcameramtx)
        return undimg
