# -*- coding: utf-8 -*-
import cv2
import numpy as np
import cameraundistort as undis


class Chessboard3D:
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
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, 0.1)
        # self.point = np.array([[-((self.board_h-1)/2-0.5),((self.board_w-1)/2-0.5),0],
        # [((self.board_h-1)/2-0.5),((self.board_w-1)/2-0.5),0],
        # [((self.board_h-1)/2-0.5),-((self.board_w-1)/2-0.5),0],
        # [-((self.board_h-1)/2-0.5),-((self.board_w-1)/2-0.5),0]],np.float32)*self.size
        # self.point = np.array([[-3,0,0],[-1,0,0],[1,0,0],[3,0,0]])
        self.point = np.array([[0, 0, 0]]) * self.size
        self.points3D = []
        self.keep = False
        # self.newCamMatrix()

    def chessboard3D(self, img, drawimg=False, keep=False, initimg=False, pos=(0, 0, 0, 0)):
        # img = self.equalize_histogram(img)
        if initimg:
            self.img = img
        self.keep = keep
        # Find the chess board corner
        grayimg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # grayimg = cv2.equalizeHist(grayimg)
        blur = cv2.GaussianBlur(grayimg, (3, 3), 0)
        ret, grayimg = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        # ret,grayimg  = cv2.threshold(grayimg ,200, 255,cv2.THRESH_BINARY)
        flags = cv2.CALIB_CB_FAST_CHECK  # and cv2.CALIB_CB_ADAPTIVE_THRESH #and cv2.CALIB_CB_FILTER_QUADS and cv2.CALIB_CB_NORMALIZE_IMAGE
        foundcorners, self.corners = cv2.findChessboardCorners(grayimg, (self.board_h - 1, self.board_w - 1),
                                                               flags=flags)

        # foundcorners, self.corners = cv2.findChessboardCorners(grayimg, (self.board_h-1,self.board_w-1),flags=flags)
        # If found, add object points, image points (after refining them)
        if foundcorners:
            self.corners = cv2.cornerSubPix(grayimg, self.corners, (5, 5), (-1, -1), self.criteria)
            if type(self.corners) is not None:
                self.cornerexist = True
                try:
                    # Find the chessboard center
                    self.corners[:, :, 0] = pos[0] + self.corners[:, :, 0]
                    self.corners[:, :, 1] = pos[1] + self.corners[:, :, 1]
                    self.xmin = np.min(self.corners[:, :, 0])
                    self.xmax = np.max(self.corners[:, :, 0])
                    self.ymin = np.min(self.corners[:, :, 1])
                    self.ymax = np.max(self.corners[:, :, 1])
                    self.xc = (self.xmax + self.xmin) / 2
                    self.yc = (self.ymax + self.ymin) / 2
                    self.ptzero = [self.xc, self.yc]
                    self.ptzero = tuple(np.float32(self.ptzero))
                    # Find the rotation and translation vectors.
                    flags = cv2.SOLVEPNP_ITERATIVE
                    solvedPnP, self.rvecs, self.tvecs = cv2.solvePnP(self.objp, self.corners, self.mtx,
                                                                     self.dist)  # rvecs rotational vector, tvecs translation vector
                    # project 3D points to image plane
                    self.cornerRect, self.cornerRectA = self.findCornerRect()
                    if drawimg:
                        img = self.drawRect(img)
                    self.rmat, self.rjacob = cv2.Rodrigues(self.rvecs)
                    self.points3D = self.real3DPosition(self.points3D)
                except:
                    self.cornerexist = False
            else:
                self.cornerexist = False
        elif not foundcorners:
            self.xmin = None
            self.xmax = None
            self.ymin = None
            self.ymax = None
            self.rvecs = False
            self.tvecs = False
            self.rmat = False
            self.ptzero = False
            self.points3D = None
            self.cornerexist = False
        return img, self.ptzero, self.points3D, grayimg

    def getSubRect(self):
        return self.xmin, self.xmax, self.ymin, self.ymax

    def getCornerExist(self):
        return self.cornerexist

    def correctHist(self, frame):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
        cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)

    def equalize_histogram(self, frame):
        # Histogram equalization
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        lab = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        return lab

    def newCamMatrix(self):
        # Get new camera matrix of undistort image
        self.newcamcorr = undis.CameraUndistort(self.board_h, self.board_w, self.size)
        self.newcamcorr.setFolder(self.folder)
        self.mtx, self.dist = self.newcamcorr.calibrate()
        return self.mtx, self.dist

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

    def drawRect(self, img, offset=(0, 0)):
        if self.cornerexist and type(self.cornerRect) is not None:
            for i in range(len(self.cornerRect) - 1):
                xy1 = (int(self.cornerRect[i][0] + offset[0]), int(self.cornerRect[i][1] + offset[1]))
                xy2 = (int(self.cornerRect[i + 1][0] + offset[0]), int(self.cornerRect[i + 1][1] + offset[1]))
                img = cv2.line(img, xy1, xy2, (0, 255, 0), 1)
            xy1 = (int(self.cornerRect[0][0] + offset[0]), int(self.cornerRect[0][1] + offset[1]))
            xy2 = (int(self.cornerRect[len(self.cornerRect) - 1][0] + offset[0]),
                   int(self.cornerRect[len(self.cornerRect) - 1][1] + offset[1]))
            img = cv2.line(img, xy1, xy2, (0, 255, 0), 1)
        return img

    def draw(self):
        self.corner = tuple(self.corners[0].ravel())
        self.img = cv2.line(self.img, self.corner, tuple(self.imgpts[0].ravel()), (255, 0, 0), 3)
        self.img = cv2.line(self.img, self.corner, tuple(self.imgpts[1].ravel()), (0, 255, 0), 3)
        self.img = cv2.line(self.img, self.corner, tuple(self.imgpts[2].ravel()), (0, 0, 255), 3)
        return img

    def real3DPosition(self, points3D):
        self.points3D = points3D
        try:
            self.temp = []
            for i in range(len(self.point)):
                self.temp = np.append(self.temp, (np.dot(self.rmat, self.point[i]) + self.tvecs.T).tolist())
                # if i==0:
                # self.temp = [self.tempmat[0]]
                # else:    
                # self.temp = np.insert(self.temp,i,self.tempmat[0],axis=0)
                print(self.temp)
            if type(self.points3D) is None:
                self.points3D = np.array([self.temp.tolist()])
            else:
                if self.keep:
                    self.points3D = np.insert(self.points3D, len(self.points3D), self.temp, axis=0)
                else:
                    self.points3D = np.array([self.temp.tolist()])
        except:
            None
        return self.points3D
