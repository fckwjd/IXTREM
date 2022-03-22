# -*- coding: utf-8 -*-
import cv2
import numpy as np
import cameraundistort as undis
import colordetection as coldet
import rangefinder as rgfd
import time


def chessboard3D(img, mtx, dist, objp, axis, criteria, board_h=8, board_w=7, size=25):
    # Find the chess board corner
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (board_h - 1, board_w - 1))
    # If found, add object points, image points (after refining them)
    if ret == True:
        # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)       
        corners = cv2.cornerSubPix(gray, corners, (9, 9), (-1, -1), criteria)
        cv2.drawChessboardCorners(img, (board_h - 1, board_w - 1), corners, ret)
        # Find the chessboard center
        xmin = np.min(corners[:, :, 0])
        xmax = np.max(corners[:, :, 0])
        ymin = np.min(corners[:, :, 1])
        ymax = np.max(corners[:, :, 1])
        xc = (xmax + xmin) / 2
        yc = (ymax + ymin) / 2
        ptzero = [xc, yc]
        ptzero = tuple(np.float32(ptzero))
        # Find the rotation and translation vectors.
        try:
            ret, rvecs, tvecs = cv2.solvePnP(objp, corners, mtx,
                                             dist)  # rvecs rotational vector, tvecs translation vector
            cornerRect, cornerRectA = findCornerRect(corners, board_h, board_w)
            img = drawRect(img, cornerRect)
            rmat, rjacob = cv2.Rodrigues(rvecs)
        except:
            ret = False
    if not ret:
        rvecs = False
        tvecs = False
        rmat = False
        ptzero = False
    return img, rvecs, tvecs, rmat, ptzero


def findCornerRect(corners, board_h=8, board_w=7):
    c1 = corners[0].ravel()
    c2 = corners[(board_h - 1) - 1].ravel()
    c4 = corners[(board_h - 1) * (board_w - 1) - (board_h - 1)].ravel()
    c3 = corners[(board_h - 1) * (board_w - 1) - 1].ravel()
    c1t = tuple(np.float32(c1))
    c2t = tuple(np.float32(c2))
    c3t = tuple(np.float32(c3))
    c4t = tuple(np.float32(c4))
    cornerRect = [c1t, c2t, c3t, c4t]
    cornerRectA = [c1.tolist(), c2.tolist(), c3.tolist(), c4.tolist()]
    cornerRectA = np.array(cornerRectA, np.float32)
    return cornerRect, cornerRectA


def drawRect(img, cornerRect):
    for i in range(len(cornerRect) - 1):
        img = cv2.line(img, cornerRect[i], cornerRect[i + 1], (0, 255, (i - 1) * 70), 1)
    img = cv2.line(img, cornerRect[0], cornerRect[len(cornerRect) - 1], (0, 255, 0), 1)
    return img


def draw(img, corners, imgpts, ptzero):
    corner = tuple(corners[0].ravel())
    img = cv2.line(img, corner, tuple(imgpts[0].ravel()), (255, 0, 0), 3)
    img = cv2.line(img, corner, tuple(imgpts[1].ravel()), (0, 255, 0), 3)
    img = cv2.line(img, corner, tuple(imgpts[2].ravel()), (0, 0, 255), 3)
    return img


def real3DPosition(points, rmat, tvec, points3D):
    for i in range(len(points)):
        tempmat = (np.dot(rmat, points[i]) + tvec.T).tolist()
        if i == 0:
            temp = [tempmat[0]]
        else:
            temp = np.insert(temp, i, tempmat[0], axis=0)
    if len(points3D) == 0:
        points3D = [temp]
    else:
        points3D = np.insert(points3D, len(points3D), temp, axis=0)
    return points3D


cap = cv2.VideoCapture(1)
_, frame = cap.read()
width = cap.get(3)
height = cap.get(4)
if width > 0 and height > 0:
    # Create CameraUndistort object
    camcorr = undis.CameraUndistort(board_h=8, board_w=7, size=1)
    mtx, dist = camcorr.calibrate()

    # Correct distortion
    frame = camcorr.undistortImage(frame, mtx, dist)

    # Get new camera matrix of undistort image
    newcamcorr = undis.CameraUndistort(8, 7, 25)
    newcamcorr.setFolder('C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Sources\\Camera\\test\\')
    mtx2, dist2 = newcamcorr.calibrate()

    # Initialize file number
    idx_file = 0

    # Initialize chessboard detection
    size = 5.667  # in mm
    size = 8.1667  # in mm
    board_h = 5
    board_w = 5
    objp = np.zeros(((board_h - 1) * (board_w - 1), 3), np.float32)
    objp[:, :2] = np.mgrid[-((board_h - 1) / 2 - 0.5):((board_h - 1) / 2 - 0.5) + 1,
                  -((board_w - 1) / 2 - 0.5):((board_w - 1) / 2 - 0.5) + 1].T.reshape(-1, 2)
    objp = objp * size
    axis = np.float32([[size, 0, 0], [0, size, 0], [0, 0, -size]]).reshape(-1, 3)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1)
    # point = np.array([[-((board_h-1)/2-0.5),((board_w-1)/2-0.5),0],
    # [((board_h-1)/2-0.5),((board_w-1)/2-0.5),0],
    # [((board_h-1)/2-0.5),-((board_w-1)/2-0.5),0],
    # [-((board_h-1)/2-0.5),-((board_w-1)/2-0.5),0]],np.float32)*size
    point = np.array([[-3, 0, 0], [-1, 0, 0], [1, 0, 0], [3, 0, 0]])
    points3D = []

    # Acquire image continuously
    while (1):
        try:
            # Grab frame
            _, frame = cap.read()

            # Correct distortion
            frameU = camcorr.undistortImage(frame, mtx, dist)
            try:
                frame2, rvec, tvec, rmat, ptzero = chessboard3D(frameU, mtx2, dist2, objp, axis, criteria, board_h,
                                                                board_w)
                points3D = real3DPosition(point, rmat, tvec, points3D)
            except:
                print('error')
            # Display images
            try:
                # img = cv2.add(frameU,frame2)
                img = frame2
            except:
                img = frameU
            cv2.imshow('img', frame2)
            cv2.imshow('imgU', frameU)
        except:
            None
        # Wait for a key pressed
        k = cv2.waitKey(30) & 0xFF
        # Esc. pressed, quit app
        if k == 27:
            break
        # "p" pressed, save image
        if k == ord('p'):
            cv2.imwrite("chess_" + str(idx_file) + ".jpg", frame)
            idx_file = idx_file + 1

    # Destroy windows, close the app
cv2.destroyAllWindows()
cap.release()
points3D = np.array(points3D)
X = points3D[:, :, 0].reshape(1, -1)
X = X[0]
Y = points3D[:, :, 1].reshape(1, -1)
Y = Y[0]
Z = points3D[:, :, 2].reshape(1, -1)
Z = Z[0]

from mpl_toolkits.mplot3d import axes3d
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure()
ax = fig.add_subplot(121, projection='3d')
# ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)
ax.scatter(X, Y, Z, c='r', marker='o')
ax.set_xlabel('X axis')
ax.set_ylabel('Y axis')
ax.set_zlabel('Z axis')
ax2 = fig.add_subplot(122, projection='3d')
# ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)
ax2.scatter(X, Y, Z, c='r', marker='o')
ax2.set_xlabel('X axis')
ax2.set_ylabel('Y axis')
ax2.set_zlabel('Z axis')

plt.show()
