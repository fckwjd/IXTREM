# -*- coding: utf-8 -*-
import cv2
import numpy as np
import cameraundistort as undis


class Chessboard3D():
    def __init__(self, mtx=[], dist=[], board_h=8, board_w=7, size=25,
                 folder='C:\\Users\\502750516\\Documents\\Programmation\\Python_3\\Sources\\Camera\\Scanner\\chessboard\\'):
        self.mtx = mtx
        self.dist = dist
        self.board_h = board_h
        self.board_w = board_w
        self.size = size
        self.folder = folder
        self.objp = np.zeros(((self.board_h - 1) * (self.board_w - 1), 3), np.float32)
        self.objp[:, :2] = np.mgrid[-((self.board_h - 1) / 2 - 0.5):((self.board_h - 1) / 2 - 0.5) + 1,
                           -((self.board_w - 1) / 2 - 0.5):((self.board_w - 1) / 2 - 0.5) + 1].T.reshape(-1, 2)
        self.objp = self.objp * self.size
        self.axis = np.float32([[self.size, 0, 0], [0, self.size, 0], [0, 0, -self.size]]).reshape(-1, 3)
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1)
        # self.point = np.array([[-((self.board_h-1)/2-0.5),((self.board_w-1)/2-0.5),0],
        # [((self.board_h-1)/2-0.5),((self.board_w-1)/2-0.5),0],
        # [((self.board_h-1)/2-0.5),-((self.board_w-1)/2-0.5),0],
        # [-((self.board_h-1)/2-0.5),-((self.board_w-1)/2-0.5),0]],np.float32)*self.size
        self.point = np.array([[-3, 0, 0], [-1, 0, 0], [1, 0, 0], [3, 0, 0]])
        self.points3D = []
        self.keep = False
        self.newCamMatrix()

    def chessboard3D(self, img, drawimg=False, keep=False):
        self.img = img
        self.drawimg = drawimg
        self.keep = keep
        # Find the chess board corner
        self.gray = cv2.cvtColor(self.img, cv2.COLOR_BGR2GRAY)
        self.ret, self.corners = cv2.findChessboardCorners(self.gray, (self.board_h - 1, self.board_w - 1))
        # If found, add object points, image points (after refining them)
        if self.ret == True:
            self.corners = cv2.cornerSubPix(self.gray, self.corners, (9, 9), (-1, -1), self.criteria)
            # Find the chessboard center
            self.xmin = np.min(self.corners[:, :, 0])
            self.xmax = np.max(self.corners[:, :, 0])
            self.ymin = np.min(self.corners[:, :, 1])
            self.ymax = np.max(self.corners[:, :, 1])
            self.xc = (self.xmax + self.xmin) / 2
            self.yc = (self.ymax + self.ymin) / 2
            self.ptzero = [self.xc, self.yc]
            self.ptzero = tuple(np.float32(self.ptzero))
            # Find the rotation and translation vectors.
            try:
                self.ret, self.rvecs, self.tvecs = cv2.solvePnP(self.objp, self.corners, self.mtx2,
                                                                self.dist2)  # rvecs rotational vector, tvecs translation vector
                # project 3D points to image plane
                self.cornerRect, self.cornerRectA = self.findCornerRect()
                if self.drawimg:
                    self.img = self.drawRect()
                self.rmat, self.rjacob = cv2.Rodrigues(self.rvecs)
                self.points3D = self.real3DPosition(self.points3D)
            except:
                self.ret = False
        if not self.ret:
            self.rvecs = False
            self.tvecs = False
            self.rmat = False
            self.ptzero = False
            self.points3D = None
        return self.img, self.ptzero, self.points3D

    def newCamMatrix(self):
        # Get new camera matrix of undistort image
        self.newcamcorr = undis.CameraUndistort(self.board_h, self.board_w, self.size)
        self.newcamcorr.setFolder(self.folder)
        self.mtx2, self.dist2 = self.newcamcorr.calibrate()
        return self.mtx2, self.dist2

    def findCornerRect(self):
        self.c1 = self.corners[0].ravel()
        self.c2 = self.corners[(self.board_h - 1) - 1].ravel()
        self.c4 = self.corners[(self.board_h - 1) * (self.board_w - 2)].ravel()
        self.c3 = self.corners[(self.board_h - 1) * (self.board_w - 1) - 1].ravel()
        self.c1t = tuple(np.float32(self.c1))
        self.c2t = tuple(np.float32(self.c2))
        self.c3t = tuple(np.float32(self.c3))
        self.c4t = tuple(np.float32(self.c4))
        self.cornerRect = [self.c1t, self.c2t, self.c3t, self.c4t]
        self.cornerRectA = [self.c1.tolist(), self.c2.tolist(), self.c3.tolist(), self.c4.tolist()]
        self.cornerRectA = np.array(self.cornerRectA, np.float32)
        return self.cornerRect, self.cornerRectA

    def drawRect(self):
        for i in range(len(self.cornerRect) - 1):
            self.img = cv2.line(self.img, self.cornerRect[i], self.cornerRect[i + 1], (0, 255, 0), 1)
        self.img = cv2.line(self.img, self.cornerRect[0], self.cornerRect[len(self.cornerRect) - 1], (0, 255, 0), 1)
        return self.img

    def draw(self):
        self.corner = tuple(self.corners[0].ravel())
        self.img = cv2.line(self.img, self.corner, tuple(self.imgpts[0].ravel()), (255, 0, 0), 3)
        self.img = cv2.line(self.img, self.corner, tuple(self.imgpts[1].ravel()), (0, 255, 0), 3)
        self.img = cv2.line(self.img, self.corner, tuple(self.imgpts[2].ravel()), (0, 0, 255), 3)
        return img

    def real3DPosition(self, points3D):
        self.points3D = points3D
        for i in range(len(self.point)):
            self.tempmat = (np.dot(self.rmat, self.point[i]) + self.tvecs.T).tolist()
            if i == 0:
                self.temp = [self.tempmat[0]]
            else:
                self.temp = np.insert(self.temp, i, self.tempmat[0], axis=0)
        if self.points3D is None or not self.points3D:
            self.points3D = np.array([self.temp.tolist()])
        else:
            if self.keep:
                self.points3D = np.insert(self.points3D, len(self.points3D), self.temp, axis=0)
            else:
                self.points3D = np.array([self.temp.tolist()])
        return self.points3D
