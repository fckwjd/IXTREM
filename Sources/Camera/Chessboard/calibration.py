import numpy as np
import cv2
import glob

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((7 * 6, 3), np.float32)
objp[:, :2] = np.mgrid[0:6, 0:7].T.reshape(-1, 2)

# Arrays to store object points and image points from all the images.
objpoints = []  # 3d point in real world space
imgpoints = []  # 2d points in image plane.

images = glob.glob('*.jpg')
print(images)

for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imshow('img', gray)
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (6, 7), None)
    # If found, add object points, image points (after refining them)
    if ret == True:
        objpoints.append(objp)

        corners2 = cv2.cornerSubPix(gray, corners, (9, 9), (-1, -1), criteria)
        imgpoints.append(corners2)

        # Draw and display the corners
        img = cv2.drawChessboardCorners(img, (7, 6), corners2, ret)
        cv2.imshow('img', img)
        cv2.waitKey(500)

ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
cap = cv2.VideoCapture(0)
while (1):
    # Take each frame
    _, img = cap.read()
    dst = cv2.undistort(img, mtx, dist, None, mtx)
    cv2.imshow('ttt', dst)
    k = cv2.waitKey(200) & 0xFF
    # Esc. pressed, quit app
    if k == 27:
        break

cv2.destroyAllWindows()
cap.release()
